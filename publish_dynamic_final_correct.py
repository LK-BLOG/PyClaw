#!/usr/bin/env python3
"""Publish dynamic using bilibili-api-python reading from actual environment."""

import asyncio
import os
from bilibili_api import Credential
from bilibili_api.dynamic import BuildDynamic, send_dynamic

# Get credentials directly from environment
SESSDATA = os.environ.get('BILIBILI_SESSDATA', '')
BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', '')
BUVID3 = os.environ.get('BILIBILI_BUVID3', '')

# Debug
print(f"Got from environment:")
print(f"  SESSDATA length: {len(SESSDATA) if SESSDATA else 'None'}")
print(f"  BILI_JCT length: {len(BILI_JCT) if BILI_JCT else 'None'}")
print(f"  BUVID3 length: {len(BUVID3) if BUVID3 else 'None'}")

# Check if we have data
if not SESSDATA or not BILI_JCT:
    print("ERROR: Missing required credentials in environment!")
    exit(1)

# Dynamic content
content_text = """当前内网穿透服务临时切换到 loca.lt 了，地址在这里：
https://chilly-swans-retire.loca.lt

这条动态由 OpenClaw 智能助手自动发布 🤖"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("\nCredential created successfully")
    
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
