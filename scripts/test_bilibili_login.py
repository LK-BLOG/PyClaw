#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests

cookie_file = os.path.expanduser("~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])

print("测试B站登录状态...")
print()

url = "https://api.bilibili.com/x/space/v2/myinfo"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": cookie_header,
    "Referer": "https://space.bilibili.com/",
}

response = requests.get(url, headers=headers)
result = response.json()

if result.get('code') == 0:
    print("✅ 已登录！")
    profile = result.get('data', {}).get('profile', {})
    print(f"用户名: {profile.get('name')}")
    print(f"UID: {profile.get('mid')}")
else:
    print(f"❌ 未登录: code={result.get('code')}, message={result.get('message', '未知错误')}")
