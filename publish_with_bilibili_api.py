#!/usr/bin/env python3
"""Publish dynamic using bilibili-api-python library."""

import asyncio
from bilibili_api import Credential, dynamic

# Credentials
SESSDATA = """${BILIBILI_SESSDATA}"""
BILI_JCT = """${BILIBILI_BILI_JCT}"""
BUVID3 = """${BILIBILI_BUVID3}"""

# Dynamic content
content = """当前内网穿透服务临时切换到 loca.lt 了，地址在这里：
https://chilly-swans-retire.loca.lt

这条动态由 OpenClaw 智能助手自动发布 🤖"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("Credential created")
    
    result = await dynamic.send_dynamic(content, cred)
    print("\nResult:")
    print(result)
    
    if result.get("code") == 0:
        print("\n✅ Dynamic published successfully!")
        data = result.get("data", {})
        print(f"Dynamic ID: {data.get('dyn_id')}")
    else:
        print(f"\n❌ Failed: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(main())
