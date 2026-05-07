#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

# 当前Cloudflare tunnel链接 - 最新链接
tunnel_url = "https://giant-mutual-papers-champions.trycloudflare.com"
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = """🌐 网站还在跑着呢~

Cloudflare Tunnel 自动连接中 🔄
👉 https://giant-mutual-papers-champions.trycloudflare.com

（本条动态由服务器自动发布，隧道每5分钟检测一次，断开自动重连）

#日常 #Cloudflare #服务器状态"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
BILI_JCT = cookies.get('bili_jct', '')

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print(f"发布时间: {current_time}")

# 尝试直接用requests发布
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
response = requests.post(url, headers=headers, data=data)
result = response.json()
print(f"API响应: {result}")
if result.get('code') == 0:
    print("\n✅ 动态发布成功！")
    dynamic_id = result.get('data', {}).get('dyn_id', '未知')
    print(f"动态ID: {dynamic_id}")
    print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
else:
    print(f"\n❌ 发布失败: {result.get('message', '未知错误')}")
