#!/usr/bin/env python3
"""Publish Bilibili dynamic with latest tunnel info."""

import asyncio
import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

# Dynamic content - daily style
content = """🌐 今日服务状态更新

Cloudflare quick tunnel 还是不太稳定，目前继续用 loca.lt 做内网穿透～

当前家里服务器的公网访问地址：
https://major-ants-clean.loca.lt

🤖 这条动态是 AI 助手自动发布的，链接会定期更新，有需要的朋友可以收藏一下！

#内网穿透 #home_server #自动发布"""

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
