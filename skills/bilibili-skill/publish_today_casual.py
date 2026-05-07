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
    cookie_str = f.read().strip()
    # 按分号分割cookie项
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')

# 当前Cloudflare tunnel链接
tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"

content = f"""嘿～下午好呀 ☀️

个人网站正常运行中👇
{tunnel_url}

（提示：链接要复制到浏览器或者点进动态详情页才能打开哦，Cloudflare免费隧道就是这样的特性😂）

弄了个简单的留言板功能，路过的朋友可以留个爪印打个卡～

🤖 本条动态由AI自动发布
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
    print("✅ 发布成功！")
    print(f"动态ID: {result.get('dynamic_id', '未知')}")
    print(f"动态链接: https://t.bilibili.com/{result.get('dynamic_id', '')}")

asyncio.run(publish())
