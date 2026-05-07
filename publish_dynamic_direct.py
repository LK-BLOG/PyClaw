#!/usr/bin/env python3
import asyncio
import json
import sys
import os

# Add bilibili-all-in-one directory to path
bili_dir = '/home/claw/.openclaw/workspace/skills/bilibili-all-in-one'
sys.path.insert(0, bili_dir)
os.chdir(bili_dir)

from main import BilibiliAllInOne

# Credentials injected directly from the configuration
sessdata = """${BILIBILI_SESSDATA}"""
bili_jct = """${BILIBILI_BILI_JCT}"""
buvid3 = """${BILIBILI_BUVID3}"""

# Print debug info
print(f"SESSDATA length: {len(sessdata) if sessdata else 'None'}")
print(f"bili_jct length: {len(bili_jct) if bili_jct else 'None'}")

if not sessdata or not bili_jct:
    print("ERROR: Missing credentials")
    sys.exit(1)

# Dynamic content with link and auto-publish statement
content = """当前内网穿透服务临时切换到 loca.lt 了，地址在这里：
https://chilly-swans-retire.loca.lt

这条动态由 OpenClaw 智能助手自动发布 🤖"""

async def run():
    app = BilibiliAllInOne(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3
    )
    result = await app.execute("publisher", "publish_dynamic", content=content)
    print("\nResult:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    asyncio.run(run())
