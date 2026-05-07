#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import re
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cookie.txt")
with open(cookie_file, 'r') as f:
    raw = f.read().strip()

cookies = {}
for m in re.finditer(r'([^=;\s]+)=([^;]+)', raw):
    cookies[m.group(1)] = m.group(2)

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', '')

tunnel_url = "https://cigarette-jewish-teams-brooklyn.trycloudflare.com"

text = f"""个人网站更新地址👇
{tunnel_url}
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)
"""

cred = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3
)

async def main():
    builder = BuildDynamic()
    builder.add_text(text)
    result = await dynamic.send_dynamic(builder, cred)
    print("发布成功！")
    print(f"动态ID: {result.get('dynamic_id', '未知')}")
    print(result)

asyncio.run(main())
