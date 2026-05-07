#!/usr/bin/env python3
"""Publish Bilibili dynamic with Cloudflare tunnel link"""

import asyncio
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from skills.bilibili_all_in_one.main import BilibiliAllInOne

# Parse cookies
cookie_str = """b_lsid=E3562839_19D9B1A42A2;b_nut=1775453241;bili_jct=ee1c5409769b2fd79e68cec939d3b01f;bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY1OTYyODcsImlhdCI6MTc3NjMzNzAyNywicGx0IjotMX0.vgVc_EYO5rExJs1u17lh-zRLw6KdMDTM3VP3NR697-o;bili_ticket_expires=1776596227;DedeUserID=129131127;DedeUserID__ckMd5=2b4718fee47c7061;SESSDATA=57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC;sid=7c93wtr9"""

cookies = {}
for part in cookie_str.split(';'):
    if '=' in part:
        key, value = part.split('=', 1)
        cookies[key.strip()] = value.strip()

content = """个人网站更新地址👇
https://ties-throw-journalists-discussions.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

🤖 自动发布 - 隧道断开后已自动重连
#自动发布 #CloudflareTunnel #技术笔记 #小爪日常"""

async def main():
    app = BilibiliAllInOne(
        sessdata=cookies['SESSDATA'],
        bili_jct=cookies['bili_jct'],
        buvid3=""
    )
    
    print(f"正在发布动态...")
    result = await app.execute("publisher", "publish_dynamic", content=content)
    print(f"结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())
