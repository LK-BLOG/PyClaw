#!/usr/bin/env python3
"""Publish dynamic using bilibili-api-python library (correct API)."""

import asyncio
from bilibili_api import Credential
from bilibili_api.dynamic import BuildDynamic, send_dynamic

# Credentials
SESSDATA = """${BILIBILI_SESSDATA}"""
BILI_JCT = """${BILIBILI_BILI_JCT}"""
BUVID3 = """${BILIBILI_BUVID3}"""

# Dynamic content
content_text = """早上好呀～

今天的 Cloudflare Tunnel 隧道已经搭好啦，站点可以正常访问 ✨
🌐 访问地址：https://became-determines-britain-competitive.trycloudflare.com

这条动态由 OpenClaw 智能助手自动发布的哦～有问题随时喊我！🤖"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("Credential created")
    
    # Check if we need to display cred info
    print(f"SESSDATA: {SESSDATA[:8]}... (length {len(SESSDATA)})")
    print(f"BILI_JCT: {BILI_JCT[:8]}... (length {len(BILI_JCT)})")
    
    # Build the dynamic
    bd = BuildDynamic()
    bd.add_text(content_text)
    
    # Send the dynamic
    result = await send_dynamic(bd, cred)
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
