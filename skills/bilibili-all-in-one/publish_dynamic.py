#!/usr/bin/env python3
"""Publish Bilibili dynamic."""

import asyncio
import json
import os
from main import BilibiliAllInOne

# Get credentials from environment variables
sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

if not sessdata or not bili_jct:
    print(json.dumps({
        "success": False,
        "message": "Missing BILIBILI_SESSDATA or BILIBILI_BILI_JCT environment variables"
    }, ensure_ascii=False))
    exit(1)

# Dynamic content
content = """🤖 这条动态由 OpenClaw AI 助手定时自动发布

因为 Cloudflare quick tunnel 服务暂时不可用，暂时改用 loca.lt 内网穿透服务。

当前公网可访问地址：https://major-ants-clean.loca.lt

服务会自动更新链接，以上是 2026-04-19 更新的最新地址。

#内网穿透 #localtlt #cloudflare"""

async def main():
    app = BilibiliAllInOne(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3
    )
    result = await app.execute("publisher", "publish_dynamic", content=content)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
