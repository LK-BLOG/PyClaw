#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
import requests

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

from urllib.parse import unquote

SESSDATA = unquote(cookies.get('SESSDATA', ''))
BILI_JCT = cookies.get('bili_jct', '')

# 新的Cloudflare tunnel链接
tunnel_url = "https://west-bull-alice-hip.trycloudflare.com"

from datetime import datetime
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""个人网站更新地址👇
{tunnel_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️
（自动发布）

发布时间：{current_time}
"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])

# 直接用requests发布
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
            print("✅ 动态发布成功！")
            dynamic_id = result.get('data', {}).get('result', {}).get('dynamic_id', '未知')
            print(f"动态ID: {dynamic_id}")
            return True, dynamic_id
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            return False, result.get('message', '未知错误')
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False, str(e)

if __name__ == "__main__":
    print(f"发布内容:\n{content}")
    print("\n正在发布B站动态...")
    success, result = asyncio.run(publish_direct())
    if success:
        print(f"\n✅ 隧道已恢复！新链接: {tunnel_url}")
    else:
        print(f"\n❌ 发布失败: {result}")
        print(f"隧道链接已获取但无法发布动态: {tunnel_url}")
