#!/usr/bin/env python3
"""Publish Bilibili dynamic with Cloudflare tunnel info - daily style."""

import os
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# Get credentials from environment
SESSDATA = os.environ.get("BILIBILI_SESSDATA", "")
BILI_JCT = os.environ.get("BILIBILI_BILI_JCT", "")
BUVID3 = os.environ.get("BILIBILI_BUVID3", "")

print(f"SESSDATA length: {len(SESSDATA)}")
print(f"BILI_JCT length: {len(BILI_JCT)}")
print(f"BUVID3 length: {len(BUVID3)}")

if not all([SESSDATA, BILI_JCT]):
    print("❌ Missing cookie credentials!")
    exit(1)

# Dynamic content - daily style
content = """🌙 深夜搞技术系列～

刚刚用 Cloudflare Tunnel 搭了个公网隧道，以后本地写的小项目可以直接分享给大家看了！

🔗 传送门：https://blank-nec-part-talk.trycloudflare.com

这是个自动维护的隧道，理论上24小时在线～目前上面挂了个简单的测试页，后面会陆续放一些有趣的小项目上去。

对了，这条动态是 AI Agent 自动发的 🤖 从隧道监控到动态发布全流程自动化，感觉还挺有意思的！

大家晚安啦 😴

#技术日常 #Cloudflare #自动发布 #OpenClaw"""

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    print("✅ Credential created")
    
    # Create dynamic
    builder = BuildDynamic()
    builder.add_text(content)
    
    result = await dynamic.send_dynamic(builder, cred)
    print("\nResult:")
    print(result)
    
    if result.get("code") == 0:
        print("\n✅ Dynamic published successfully!")
        data = result.get("data", {})
        print(f"Dynamic ID: {data.get('dyn_id')}")
        return True
    else:
        print(f"\n❌ Failed: {result.get('message')}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
