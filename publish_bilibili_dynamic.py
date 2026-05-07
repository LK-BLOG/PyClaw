#!/usr/bin/env python3
"""Publish a dynamic to Bilibili"""

import asyncio
import json
import os
from sys import argv

from skills.bilibili-all-in-one.main import BilibiliAllInOne

# Get content from command line or use default
if len(argv) > 1:
    content = argv[1]
else:
    content = """晚上好呀～🌙

今天折腾了一下公网隧道，终于把本地的小网站挂到公网啦！虽然loca.lt这服务偶尔抽风，但至少现在能访问了～

👉 https://tough-sides-listen.loca.lt

🤖 悄悄说一句：这条动态是OpenClaw通过Cron定时任务自动发的哦，我在学习做一个会自己发动态的AI助手哈哈～

#自动发布 #OpenClaw #技术折腾"""

# Get credentials from environment variables
sessdata = os.environ.get('BILIBILI_SESSDATA')
bili_jct = os.environ.get('BILIBILI_BILI_JCT')
buvid3 = os.environ.get('BILIBILI_BUVID3', '')

if not sessdata or not bili_jct:
    print("ERROR: BILIBILI_SESSDATA and BILIBILI_BILI_JCT environment variables are required")
    print()
    print("Please set them before running:")
    print("  export BILIBILI_SESSDATA=your_sessdata")
    print("  export BILIBILI_BILI_JCT=your_bili_jct")
    print("  export BILIBILI_BUVID3=your_buvid3 (optional)")
    exit(1)

async def main():
    app = BilibiliAllInOne(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3
    )
    
    print(f"Publishing dynamic content:\n{content}\n")
    result = await app.execute("publisher", "publish_dynamic", content=content)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get('success'):
        print("\n✅ Dynamic published successfully!")
    else:
        print(f"\n❌ Failed: {result.get('message')}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
