#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from urllib.parse import unquote

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

SESSDATA = unquote(cookies.get('SESSDATA', ''))
BILI_JCT = cookies.get('bili_jct', '')

# 当前Cloudflare tunnel链接
tunnel_url = "https://cigarettes-bridal-nickname-universities.trycloudflare.com"

from datetime import datetime
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""🌙 深夜签到～

跟大家同步一下，我的小站隧道还在稳定运行中！
👉 {tunnel_url}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么设置的～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知！
科技改变摸鱼生活 ✌️

发布时间：{current_time}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

# 构造完整的Cookie头
cookie_header = cookie_content

# 尝试直接用requests发布
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
    print(f"API响应: {result}")
    if result.get('code') == 0:
        dyn_id = result.get('data', {}).get('dyn_id', '未知')
        print(f"✅ 动态发布成功！")
        print(f"动态ID: {dyn_id}")
        print(f"动态链接: https://t.bilibili.com/{dyn_id}")
        print(f"隧道链接: {tunnel_url}")
        print(f"\n动态内容:\n{content}")
    else:
        print(f"❌ 发布失败: {result.get('message', '未知错误')}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
