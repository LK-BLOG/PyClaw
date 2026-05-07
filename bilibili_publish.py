#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests

# 从 Cookie.txt 读取所有Cookie
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
cookies = {}
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
csrf = cookies.get('bili_jct', '')

print("测试B站登录状态...")

# 获取用户信息
url = "https://api.bilibili.com/x/space/v2/myinfo"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": cookie_header,
    "Referer": "https://space.bilibili.com/",
}

response = requests.get(url, headers=headers)
result = response.json()

if result.get('code') == 0:
    profile = result.get('data', {}).get('profile', {})
    print(f"✅ 已登录! 用户名: {profile.get('name')}, UID: {profile.get('mid')}")
else:
    print(f"❌ 未登录: {result}")
    exit(1)

# 当前 Cloudflare Tunnel 链接
tunnel_url = "https://highlight-authorization-thrown-installing.trycloudflare.com"

content = """🤖 自动发布打卡~

今天的 Cloudflare Tunnel 链接已经上线啦：
""" + tunnel_url + """

（得点进动态才能打开链接哦，Cloudflare 免费隧道就是这么设置的）

这条动态是通过 OpenClaw 的 Cron 定时任务自动发布的，用来同步最新的隧道地址，这样大家随时都能访问到我本地的服务啦~ 😄

✅ 隧道状态：正常运行
⏰ 更新时间：2026-04-24 11:45

欢迎来留言板唠嗑～"""

print("\n准备发布动态...")
print(f"内容:\n{content}\n")

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
else:
    print(f"❌ 发布失败: {publish_result.get('message')}")
