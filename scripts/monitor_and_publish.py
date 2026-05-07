#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re
import time
import requests

# 配置
COOKIE_FILE = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
LOCAL_URL = "http://localhost:80"
TEST_TIMEOUT = 10

def read_cookies():
    cookies = {}
    with open(COOKIE_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                cookies[key] = value
    return cookies

def test_website(url, timeout=10):
    """测试网站是否可访问"""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 500
    except Exception as e:
        print(f"连接失败: {e}")
        return False

def kill_old_processes():
    """杀掉旧的cloudflared和lt进程"""
    print("正在杀掉旧的 cloudflared 进程...")
    subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)
    subprocess.run(["pkill", "-f", "lt "], capture_output=True)  # localtunnel
    time.sleep(2)
    print("✅ 旧进程已清理")

def start_cloudflared():
    """启动 cloudflared 并获取新链接"""
    print("正在启动 Cloudflare Tunnel...")
    
    # 在后台启动 cloudflared，捕获输出
    cmd = ["cloudflared", "tunnel", "--url", LOCAL_URL]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # 读取输出以获取公网链接
    tunnel_url = None
    start_time = time.time()
    timeout = 30
    
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.5)
            continue
        
        print(f"[cloudflared] {line.strip()}")
        
        # 匹配 URL 输出: +-------------------------------------------------------------------------------------------+
        # |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
        # |  https://random-subdomain.trycloudflare.com                                               |
        # +-------------------------------------------------------------------------------------------+
        if "https://" in line and ".trycloudflare.com" in line:
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n✅ 获取到新链接: {tunnel_url}")
                break
    
    if not tunnel_url:
        print("⚠️ 未能从输出中提取链接，尝试其他方式...")
        # 给更多时间让隧道启动
        time.sleep(5)
    
    return proc, tunnel_url

def publish_bilibili_dynamic(new_url):
    """发布 B 站动态 - 使用 requests 直接调用 API"""
    print("\n正在发布 B 站动态...")
    
    cookies = read_cookies()
    
    if not cookies.get('bili_jct'):
        print("❌ Cookie 不完整，无法发布动态")
        return False
    
    content = f"""个人网站更新地址👇

{new_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""
    
    # 构造完整的Cookie头
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    BILI_JCT = cookies.get('bili_jct', '')
    
    try:
        url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Referer": "https://t.bilibili.com/",
            "Origin": "https://t.bilibili.com"
        }
        data = {
            "type": 4,
            "content": content,
            "csrf": BILI_JCT,
            "from": "create.dynamic.web"
        }
        response = requests.post(url, headers=headers, data=data, timeout=30)
        result = response.json()
        
        if result.get('code') == 0:
            dyn_id = result.get('data', {}).get('dyn_id', '未知')
            print(f"✅ 动态发布成功！ID: {dyn_id}")
            return True
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            print(f"完整响应: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_tools_md(new_url):
    """更新 TOOLS.md 中的隧道链接"""
    tools_md = "/home/claw/.openclaw/workspace/TOOLS.md"
    if not os.path.exists(tools_md):
        return
    
    with open(tools_md, 'r') as f:
        content = f.read()
    
    # 替换链接
    old_pattern = r'当前公网链接: https://[a-zA-Z0-9\-\.]+\.trycloudflare\.com'
    new_line = f"当前公网链接: {new_url}"
    content = re.sub(old_pattern, new_line, content)
    
    # 更新检查时间
    time_pattern = r'最后检查: \d{4}-\d{2}-\d{2} \d{2}:\d{2}'
    new_time = f"最后检查: {time.strftime('%Y-%m-%d %H:%M')}"
    content = re.sub(time_pattern, new_time, content)
    
    # 更新状态
    content = content.replace("状态: ❌", "状态: ✅")
    
    with open(tools_md, 'w') as f:
        f.write(content)
    
    print("✅ TOOLS.md 已更新")

def main():
    print("=" * 60)
    print("Cloudflare Tunnel 监控 & B 站自动发布")
    print("=" * 60)
    print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 测试当前网站状态
    print("步骤 1: 测试当前网站状态")
    tools_md = "/home/claw/.openclaw/workspace/TOOLS.md"
    current_url = None
    if os.path.exists(tools_md):
        with open(tools_md, 'r') as f:
            for line in f:
                if "当前公网链接:" in line:
                    match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                    if match:
                        current_url = match.group(0)
                        break
    
    is_working = False
    if current_url:
        print(f"当前链接: {current_url}")
        is_working = test_website(current_url, TEST_TIMEOUT)
        print(f"状态: {'✅ 正常' if is_working else '❌ 无法访问'}")
    else:
        print("未找到当前链接")
    
    if is_working:
        print("\n网站正常，无需操作")
        sys.exit(0)
    
    # 2. 杀掉旧进程
    print("\n步骤 2: 清理旧进程")
    kill_old_processes()
    
    # 3. 启动新的 cloudflared
    print("\n步骤 3: 启动新隧道")
    proc, new_url = start_cloudflared()
    
    if not new_url:
        print("❌ 无法获取新链接，退出")
        proc.kill()
        sys.exit(1)
    
    # 4. 等待链接可用
    print("\n步骤 4: 等待链接可用...")
    time.sleep(10)  # 给 DNS 传播时间
    for i in range(6):
        if test_website(new_url, 5):
            print("✅ 链接已可访问！")
            break
        print(f"  重试 {i+1}/6...")
        time.sleep(5)
    
    # 5. 发布 B 站动态
    print("\n步骤 5: 发布动态")
    publish_ok = publish_bilibili_dynamic(new_url)
    
    # 6. 更新 TOOLS.md
    print("\n步骤 6: 更新记录")
    update_tools_md(new_url)
    
    # 7. 输出结果
    print("\n" + "=" * 60)
    print("任务完成！")
    print(f"新链接: {new_url}")
    print(f"动态发布: {'✅ 成功' if publish_ok else '❌ 失败'}")
    print("=" * 60)
    
    # 保持 cloudflared 在后台运行
    print("\nCloudflare Tunnel 正在后台运行中...")
    proc.stdout.close()

if __name__ == "__main__":
    main()
