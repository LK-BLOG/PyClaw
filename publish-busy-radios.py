#!/usr/bin/env python3
import asyncio
from bilibili_api.dynamic import BuildDynamic
from bilibili_api import Credential
from bilibili_api.dynamic import send_dynamic

# Read cookie from file - newline separated
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
with open(cookie_file, 'r') as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

# Parse cookies
cookies = {}
for line in lines:
    if '=' in line:
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        cookies[key] = value

# Create credentials
cred = Credential(
    sessdata=cookies.get('SESSDATA', ''),
    bili_jct=cookies.get('bili_jct', ''),
    buvid3=cookies.get('buvid3', cookies.get('b_lsid', ''))
)

# Content with new URL
content_text = """个人网站更新地址啦👇
https://busy-radios-make.loca.lt

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
