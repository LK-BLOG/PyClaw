#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取 (格式: key=value; key2=value2; ...)
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
import re
with open(cookie_file, 'r') as f:
    raw = f.read().strip()

cookies = {}
for m in re.finditer(r'([^=;\s]+)=([^;]+)', raw):
    cookies[m.group(1)] = m.group(2)

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')

# 新的Cloudflare tunnel链接
tunnel_url = "https://documents-neither-surgery-securities.trycloudflare.com"

content = f"""个人网站更新地址👇
{tunnel_url}
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)
"""

cred = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3
)

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    print("发布成功！")
    print(f"动态ID: {result.get('dynamic_id', '未知')}")
    print(result)

asyncio.run(publish())
