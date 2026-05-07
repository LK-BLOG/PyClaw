#!/usr/bin/env python3
import asyncio
import re
from bilibili_api.dynamic import BuildDynamic
from bilibili_api import Credential
from bilibili_api.dynamic import send_dynamic
import bilibili_api

# Try to register client
try:
    from bilibili_api.clients import HTTPXClient
    bilibili_api.client = HTTPXClient()
except Exception as e:
    print(f"Warning registering client: {e}")

# Read cookie from file
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
with open(cookie_file, 'r') as f:
    cookie_str = f.read().strip()

# Parse cookies
cookies = {}
for part in cookie_str.split(';'):
    if '=' in part:
        key, value = part.split('=', 1)
        cookies[key.strip()] = value.strip()

# Create credentials
cred = Credential(
    sessdata=cookies.get('SESSDATA', ''),
    bili_jct=cookies.get('bili_jct', ''),
    buvid3=cookies.get('buvid3', cookies.get('b_lsid', ''))
)

# Content with new URL
content_text = """个人网站更新地址啦👇
https://nine-bottles-bow.loca.lt

欢迎来留言板留言交流✈️(自动发布)"""

async def main():
    try:
        print("Sending dynamic...")
        # Create BuildDynamic object
        info = BuildDynamic()
        info.add_text(content_text)
        
        # Send it
        result = await send_dynamic(info, cred)
        print("Success! Result:")
        print(result)
        print("\n✅ 动态发布成功！")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ 发布失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
