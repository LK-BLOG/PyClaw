#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站扫码登录 - 使用requests直接调用API
"""
import requests
import json
import time
import sys
import os
import qrcode

def main():
    print("=" * 50)
    print("📱 B站扫码登录")
    print("=" * 50)
    print()
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://passport.bilibili.com/'
    })
    
    # Step 1: 获取二维码
    print("🔧 获取二维码...")
    r = session.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate')
    data = r.json()
    if data.get('code') != 0:
        print(f"❌ 获取二维码失败: {data}")
        return False
    
    qrcode_key = data['data']['qrcode_key']
    url = data['data']['url']
    print(f"✅ 二维码生成成功！")
    print()
    
    # 显示二维码（ASCII）
    try:
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii()
    except Exception as e:
        print(f"(二维码显示失败: {e})")
    
    print()
    print(f"🔗 二维码链接: {url}")
    print()
    print("⏳ 请使用B站App扫描上方二维码...")
    print()
    
    # Step 2: 轮询扫码状态
    timeout = 180  # 3分钟
    start = time.time()
    
    while time.time() - start < timeout:
        r = session.get(
            'https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
            params={'qrcode_key': qrcode_key}
        )
        data = r.json()
        code = data.get('data', {}).get('code', -1)
        
        if code == 0:  # 已确认
            print("  ✅ 扫码登录成功！")
            break
        elif code == 86038:  # 已过期
            print("  ❌ 二维码已过期，请重新运行")
            return False
        elif code == 86090:  # 已扫码未确认
            print("  👀 已扫码，请在手机上确认登录！")
        else:
            print("  ⏳ 等待扫码...")
        
        time.sleep(2)
    
    # Step 3: 获取Cookie
    cookies = session.cookies.get_dict()
    
    sessdata = cookies.get('SESSDATA', '')
    bili_jct = cookies.get('bili_jct', '')
    buvid3 = cookies.get('buvid3', '')
    dedeuserid = cookies.get('DedeUserID', '')
    
    if not sessdata:
        print("❌ 获取Cookie失败")
        return False
    
    print()
    print("=" * 50)
    print("✅ 登录成功！")
    print("=" * 50)
    print()
    print(f"【Cookie已获取】")
    print(f"SESSDATA: {sessdata[:10]}...{sessdata[-10:]}")
    print(f"bili_jct: {bili_jct[:10]}...{bili_jct[-10:]}")
    print(f"buvid3: {buvid3[:10]}...{buvid3[-10:]}")
    print(f"DedeUserID: {dedeuserid}")
    print()
    
    # 保存到文件
    cookie_path = "/home/claw/.openclaw/workspace/pyclaw-public/skills/bilibili/Cookie.txt"
    os.makedirs(os.path.dirname(cookie_path), exist_ok=True)
    cookie_content = f"SESSDATA={sessdata}; bili_jct={bili_jct}; buvid3={buvid3}; DedeUserID={dedeuserid}"
    
    with open(cookie_path, 'w') as f:
        f.write(cookie_content)
    
    print(f"✅ Cookie已保存到: {cookie_path}")
    print()
    
    # 输出环境变量设置命令
    print("=" * 60)
    print("📝 请运行以下命令设置环境变量：")
    print("=" * 60)
    print(f"export BILIBILI_SESSDATA='{sessdata}'")
    print(f"export BILIBILI_BILI_JCT='{bili_jct}'")
    print(f"export BILIBILI_BUVID3='{buvid3}'")
    print()
    print("或者添加到 .bashrc：")
    print(f"echo 'export BILIBILI_SESSDATA=\"{sessdata}\"' >> ~/.bashrc")
    print(f"echo 'export BILIBILI_BILI_JCT=\"{bili_jct}\"' >> ~/.bashrc")
    print(f"echo 'export BILIBILI_BUVID3=\"{buvid3}\"' >> ~/.bashrc")
    print()
    
    print("✅ 现在可以发布B站动态了！")
    return True

if __name__ == "__main__":
    main()
