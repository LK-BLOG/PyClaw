#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])

print("测试B站登录状态...")
print(f"Cookie: {cookie_header[:150]}...")
print()

# 尝试获取用户信息
url = "https://api.bilibili.com/x/space/v2/myinfo"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": cookie_header,
    "Referer": "https://space.bilibili.com/",
}

response = requests.get(url, headers=headers)
result = response.json()
print(f"响应: {result}")

if result.get('code') == 0:
    print("✅ 已登录！")
    profile = result.get('data', {}).get('profile', {})
    print(f"用户名: {profile.get('name')}")
    print(f"UID: {profile.get('mid')}")
else:
    print(f"❌ 未登录: {result.get('message', '未知错误')}")
