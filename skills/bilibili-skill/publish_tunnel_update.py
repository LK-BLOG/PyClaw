#!/usr/bin/env python3
import os
import sys
import asyncio
import json
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# Read cookies
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
sessdata = ""
bili_jct = ""

with open(cookie_file, 'r') as f:
    for line in f:
        if 'SESSDATA' in line:
            sessdata = line.strip().split('=', 1)[1]
        elif 'bili_jct' in line:
            bili_jct = line.strip().split('=', 1)[1]

buvid3 = "BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

content = """个人网站更新地址👇

https://jewel-absence-replication-nonprofit.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

(自动发布)"""

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

try:
    result = asyncio.run(publish())
    print(f"发布成功！动态ID: {result.get('data', {}).get('dyn_id', '未知')}")
except Exception as e:
    print(f"发布失败: {e}")
    sys.exit(1)
