#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')

import os
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

content = """个人网站更新地址👇
https://hunter-holdings-jpg-kelkoo.trycloudflare.com
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

print(f"SESSDATA长度: {len(sessdata)}")
print(f"bili_jct长度: {len(bili_jct)}")
print(f"buvid3长度: {len(buvid3)}")

if not all([sessdata, bili_jct]):
    print("错误：Cookie信息不完整")
    sys.exit(1)

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    print(result)

asyncio.run(publish())
