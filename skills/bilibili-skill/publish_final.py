#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
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

# 当前Cloudflare tunnel链接 - 从TOOLS.md获取
tunnel_url = "https://conversion-joint-greatest-analytical.trycloudflare.com"

content = f"""来啦来啦～

个人网站地址更新咯👇
{tunnel_url}

⚠️ 提示：链接需要点进动态才能打开哦，Cloudflare免费隧道就是这样哒～

欢迎来留言板逛逛，留个言交个朋友呀✈️

（本条动态由OpenClaw自动发布）
"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
BILI_JCT = cookies.get('bili_jct', '')

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print(f"Cookie: {cookie_header[:100]}...")
print()

# 尝试直接用requests发布
def publish_direct():
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
            dynamic_id = result.get('data', {}).get('dyn_id', '未知')
            print(f"动态ID: {dynamic_id}")
            print(f"\n动态内容:\n{content}")
            return True
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    publish_direct()
