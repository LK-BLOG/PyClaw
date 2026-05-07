#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')

# 从命令行参数获取内容，如果没有则使用默认内容
if len(sys.argv) > 1:
    content = sys.argv[1]
else:
    content = """🤖 【自动发布测试】

个人网站隧道已更新！Cloudflare 免费隧道地址：
👉 https://example.trycloudflare.com

（PS：链接需要点进动态详情才能打开，这是 Cloudflare 免费隧道的正常现象～）

欢迎来留言板随便逛逛、留个言交流！

这条动态由 OpenClaw 自动发布 ✨
#自动发布 #OpenClaw #个人网站"""

cred = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3
)

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    print(result)

asyncio.run(publish())
