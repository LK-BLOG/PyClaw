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

# 当前Cloudflare tunnel最新链接
tunnel_url = "https://mhz-net-reviewer-convention.trycloudflare.com"

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
    try:
        builder = BuildDynamic()
        builder.add_text(content)
        result = await dynamic.send_dynamic(builder, cred)
        print("✅ 动态发布成功！")
        dynamic_id = result.get('dynamic_id', '未知')
        print(f"动态ID: {dynamic_id}")
        print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
        print(f"隧道链接: {tunnel_url}")
        print(f"内容风格：日常")
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

asyncio.run(publish())
