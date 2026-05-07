#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests

# 从 Cookie.txt 读取所有Cookie
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_str = f.read().strip()
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
csrf = cookies.get('bili_jct', '')

# 当前 Cloudflare Tunnel 链接
tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"

# 日常风格内容
content = f"""嘿～晚上好呀 🌙

个人网站隧道正常运行中👇
{tunnel_url}

（小提示：链接要复制到浏览器或者点进动态详情页才能打开哦，Cloudflare免费隧道就是这么设置的😉）

网站弄了个简单的留言板，路过的朋友可以留个爪印打个卡唠唠嗑～

🤖 本条动态由OpenClaw定时任务自动发布
#技术日常 #CloudflareTunnel #自动发布
"""

print("准备发布动态...")

# 发布动态
publish_url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
publish_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": cookie_header,
    "Referer": "https://t.bilibili.com/",
    "Content-Type": "application/json",
}

dyn_req = {
    "type": 4,
    "rid": 0,
    "content": content,
    "csrf": csrf
}

publish_response = requests.post(publish_url, headers=publish_headers, json=dyn_req)
publish_result = publish_response.json()

print(f"发布响应: {publish_result}")

if publish_result.get('code') == 0:
    print("✅ 发布成功!")
    dyn_id = publish_result.get('data', {}).get('dyn_id', '')
    print(f"动态ID: {dyn_id}")
    print(f"动态链接: https://t.bilibili.com/{dyn_id}")
else:
    print(f"❌ 发布失败: {publish_result.get('message')}")
