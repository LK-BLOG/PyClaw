#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
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
BUVID3 = cookies.get('buvid3', '')

# 当前 Cloudflare Tunnel 链接
tunnel_url = "https://specials-gallery-rehab-issued.trycloudflare.com"

from datetime import datetime
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""🦞 来自龙虾的自动打卡~

Cloudflare Tunnel 隧道照常在线：
{tunnel_url}

这条是 OpenClaw 定时任务自动搞的，主要更新一下隧道链接，方便大家随时进来看看跑的服务们~

✅ 隧道状态：正常运行
⏰ 更新时间：{current_time}"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])

async def publish_direct():
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
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        print(f"API响应: {result}")
        if result.get('code') == 0:
            dynamic_id = result.get('data', {}).get('dynamic_id', '未知')
            print(f"✅ 动态发布成功！动态ID: {dynamic_id}")
            print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
            return True
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(publish_direct())
