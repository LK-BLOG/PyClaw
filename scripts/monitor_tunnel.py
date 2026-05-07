#!/usr/bin/env python3
import sys
import os
import subprocess
import time
import re
import urllib.request
import urllib.error

WORKSPACE = '/home/claw/.openclaw/workspace'
TOOLS_FILE = os.path.join(WORKSPACE, 'TOOLS.md')
LOCAL_PORT = 80
CHECK_URL = 'https://loud-impalas-drop.loca.lt'

def check_site_accessible(url):
    """检查网站是否可访问"""
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception as e:
        print(f"检查失败: {e}")
        return False

def kill_old_processes():
    """杀掉旧的cloudflared和lt进程"""
    print("正在杀掉旧的隧道进程...")
    subprocess.run(['pkill', '-f', 'cloudflared'], capture_output=True)
    subprocess.run(['pkill', '-f', 'lt '], capture_output=True)
    time.sleep(2)

def start_localtunnel():
    """启动localtunnel并获取新链接"""
    print("正在启动localtunnel...")
    import tempfile
    
    output_file = tempfile.mktemp()
    
    # 启动lt进程
    proc = subprocess.Popen(
        ['lt', '--port', str(LOCAL_PORT), '--print-requests', 'false'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待获取URL
    start_time = time.time()
    url = None
    
    while time.time() - start_time < 30:
        try:
            line = proc.stdout.readline()
            if 'your url is:' in line.lower():
                # 提取URL
                match = re.search(r'https?://[^\s]+', line)
                if match:
                    url = match.group(0)
                    break
        except Exception as e:
            print(f"读取输出时出错: {e}")
            break
    
    if url:
        print(f"获取到新链接: {url}")
        # 将进程放入后台
        time.sleep(1)
        return url, proc
    else:
        proc.kill()
        print("未能获取到localtunnel链接")
        return None, None

def publish_bilibili_dynamic(new_url):
    """发布B站动态 - 调用外部脚本"""
    print("正在发布B站动态...")
    
    content = f"""个人网站更新地址👇
{new_url}
（链接需要点进动态才能打开，localtunnel 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""
    
    # 将内容写入临时文件
    content_file = '/tmp/dynamic_content.txt'
    with open(content_file, 'w') as f:
        f.write(content)
    
    # 调用发布脚本
    try:
        result = subprocess.run(
            ['bash', '/home/claw/.openclaw/workspace/publish_dyn.sh', content_file],
            capture_output=True,
            text=True,
            cwd='/home/claw/.openclaw/workspace'
        )
        if result.returncode == 0:
            print(f"动态发布成功!")
            print(f"输出: {result.stdout}")
            return True
        else:
            print(f"动态发布失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"调用发布脚本失败: {e}")
        return False

def update_tools_file(new_url):
    """更新TOOLS.md中的链接"""
    with open(TOOLS_FILE, 'r') as f:
        content = f.read()
    
    # 更新链接
    content = re.sub(
        r'- 当前公网链接: https?://[^\s]+',
        f'- 当前公网链接: {new_url}',
        content
    )
    
    # 更新时间
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    content = re.sub(
        r'- 最后更新: \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
        f'- 最后更新: {now}',
        content
    )
    
    with open(TOOLS_FILE, 'w') as f:
        f.write(content)
    print("TOOLS.md已更新")

def main():
    print("=" * 50)
    print(f"隧道监控脚本启动 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查网站是否可访问
    print(f"正在检查网站: {CHECK_URL}")
    if check_site_accessible(CHECK_URL):
        print("✓ 网站访问正常，无需重启")
        return
    
    print("✗ 网站无法访问，开始重启流程...")
    
    # 杀掉旧进程
    kill_old_processes()
    
    # 启动localtunnel
    new_url, proc = start_localtunnel()
    if not new_url:
        print("重启隧道失败!")
        return
    
    # 等待几秒钟确保隧道稳定
    time.sleep(5)
    
    # 发布动态
    publish_bilibili_dynamic(new_url)
    
    # 更新TOOLS.md
    update_tools_file(new_url)
    
    print("\n" + "=" * 50)
    print(f"隧道重启完成!")
    print(f"新链接: {new_url}")
    print("=" * 50)

if __name__ == '__main__':
    main()
