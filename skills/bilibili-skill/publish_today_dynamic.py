#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
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

# Cloudflare Tunnel URL
tunnel_url = "https://quebec-claimed-graphical-dramatically.trycloudflare.com"

content = f"""🌐 个人小站正常运行中～

{tunnel_url}

用 Cloudflare Tunnel 搭的隧道，链接得点进动态才能打开哦～
有空可以来逛逛，留言板随时欢迎！

🤖 本条动态由 OpenClaw 机器人自动发布"""

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
