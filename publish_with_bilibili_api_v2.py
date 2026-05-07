#!/usr/bin/env python3
"""Publish dynamic using bilibili-api-python library (new API)."""

import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import DynamicSendContent, Dynamic

import os

# Credentials
SESSDATA = os.environ.get('BILIBILI_SESSDATA', '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC')
BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', 'ee1c5409769b2fd79e68cec939d3b01f')
BUVID3 = os.environ.get('BILIBILI_BUVID3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')

# Dynamic content
content_text = """🤖 每日自动报平安～

Cloudflare Tunnel 又自动重连成功！

🌐 今日访问地址：
https://dude-bridges-framed-living.trycloudflare.com

📝 这条动态由 OpenClaw 自动化脚本定时发布，完全不用动手～
每天自动更新隧道地址，省心又省力！

就是个简单的个人小网站，感兴趣可以点开看看 😄

#自动发布 #OpenClaw #CloudflareTunnel #技术日常"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("Credential created")
    
    # Create send content
    content = DynamicSendContent()
    content.add_text(content_text)
    
    # Send the dynamic
    result = await Dynamic.send_dynamic(content=content, credential=cred)
    print("\nResult:")
    print(result)
    
    if result.get("code") == 0:
        print("\n✅ Dynamic published successfully!")
        data = result.get("data", {})
        print(f"Dynamic ID: {data.get('dyn_id')}")
    else:
        print(f"\n❌ Failed: {result.get('message')} (code: {result.get('code')})")

if __name__ == "__main__":
    asyncio.run(main())
