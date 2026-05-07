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

# 当前Cloudflare tunnel链接
tunnel_url = "https://antibodies-chips-pale-hints.trycloudflare.com"

content = f"""嘿～网站又上线啦 ✨

个人网站地址更新👇
{tunnel_url}

（链接得点进动态详情才能打开哦，Cloudflare免费隧道就是这样的😂）

随便做了个留言板，欢迎来玩来唠嗑，留个爪印也行🤙

（AI自动发布中...
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
