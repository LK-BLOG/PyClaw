#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import re
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
with open(cookie_file, 'r') as f:
    raw = f.read()

cookies = {}
for item in raw.split(';'):
    item = item.strip()
    if '=' in item:
        key, value = item.split('=', 1)
        cookies[key.strip()] = value.strip()

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', '')

print(f"SESSDATA: {SESSDATA[:20]}...")
print(f"bili_jct: {BILI_JCT[:10]}...")
print(f"buvid3: {BUVID3[:20]}...")

if not SESSDATA:
    print("错误: SESSDATA 为空，Cookie 可能已过期")
    sys.exit(1)

content = """个人网站更新地址👇

https://phi-trading-concluded-favorite.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

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
