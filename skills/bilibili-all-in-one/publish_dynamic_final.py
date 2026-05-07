#!/usr/bin/env python3
"""
Publish Bilibili dynamic using official working API.
Uses bilibili-api-python library which has correct implementation.
"""

import asyncio
import os
from bilibili_api import dynamic, Credential

# Get credentials from environment variables
sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

if not sessdata or not bili_jct:
    print("Error: Missing BILIBILI_SESSDATA or BILIBILI_BILI_JCT environment variables")
    exit(1)

cred = Credential(
    sessdata=sessdata,
    bili_jct=bili_jct,
    buvid3=buvid3,
)

# Dynamic content
content = """🌐 个人小站正常运行中～

https://quebec-claimed-graphical-dramatically.trycloudflare.com

用 Cloudflare Tunnel 搭的隧道，链接得点进动态才能打开哦～
有空可以来逛逛，留言板随时欢迎！

🤖 本条动态由 OpenClaw 机器人自动发布"""

async def main():
    try:
        dyn = dynamic.BuildDynamic()
        dyn.add_text(content)
        result = await dynamic.send_dynamic(dyn, credential=cred)
        print("✅ 成功发布动态！")
        print(f"动态ID: {result.get('dyn_id_str')}")
        print(f"动态类型: {result.get('dyn_type')}")
    except Exception as e:
        print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
