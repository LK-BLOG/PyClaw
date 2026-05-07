#!/usr/bin/env python3
"""
Publish Bilibili dynamic with new website URL
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
content = """个人网站更新地址👇
https://white-assumptions-within-africa.trycloudflare.com
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

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
