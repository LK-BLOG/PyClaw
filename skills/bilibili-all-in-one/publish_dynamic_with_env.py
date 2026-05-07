#!/usr/bin/env python3
"""Publish Bilibili dynamic with credentials from process environment."""

import asyncio
import os
import json
import sys

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import BilibiliAllInOne

# Get credentials from the environment that was passed to this script
sessdata = os.environ.get('BILIBILI_SESSDATA')
bili_jct = os.environ.get('BILIBILI_BILI_JCT')
buvid3 = os.environ.get('BILIBILI_BUVID3')

if not sessdata or not bili_jct:
    print(json.dumps({
        "success": False,
        "message": "Missing BILIBILI_SESSDATA or BILIBILI_BILI_JCT environment variables"
    }, ensure_ascii=False))
    sys.exit(1)

# Dynamic content with link and auto-publish statement
content = """当前内网穿透服务临时切换到 loca.lt 了，地址在这里：
https://chilly-swans-retire.loca.lt

这条动态由 OpenClaw 智能助手自动发布 🤖"""

async def publish():
    app = BilibiliAllInOne(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3
    )
    result = await app.execute("publisher", "publish_dynamic", content=content)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(publish())
