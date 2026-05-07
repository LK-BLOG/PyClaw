#!/usr/bin/env python3
"""Publish dynamic using bilibili-api-python library with correct API."""

import os
import asyncio
from bilibili_api import Credential
from bilibili_api.dynamic import send_dynamic, BuildDynamic, DynamicContentType

# Credentials
SESSDATA = os.environ.get('BILIBILI_SESSDATA', '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC')
BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', 'ee1c5409769b2fd79e68cec939d3b01f')
BUVID3 = os.environ.get('BILIBILI_BUVID3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')

# Dynamic content
content_text = """👋 哈喽大家好～

今天的 Cloudflare Tunnel 稳定运行中 😊

🌐 我的个人小站当前地址：
https://dude-bridges-framed-living.trycloudflare.com

🤖 悄悄说一声，这条动态是自动发布的哦～
OpenClaw 脚本帮我搞定了一切，我都不用动手哈哈

就是个随便折腾的小玩意儿，欢迎来逛逛～

#技术摸鱼 #自动发布 #个人网站 #日常分享"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("Credential created")
    
    # Build dynamic
    dyn = BuildDynamic()
    dyn.add_text(content_text)
    print("Dynamic content built")
    
    # Send
    result = await send_dynamic(dyn, cred)
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
