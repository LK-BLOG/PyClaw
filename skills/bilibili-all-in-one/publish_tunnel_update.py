#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish Bilibili dynamic with Cloudflare tunnel update.
"""

import asyncio
import os
from bilibili_api import dynamic, Credential

# Read from Cookie.txt - same method as successful script
cookie_file = os.path.expanduser("~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    # Cookie may be semicolon-separated single line
    for part in cookie_content.split(';'):
        part = part.strip()
        if '=' in part:
            key, value = part.split('=', 1)
            cookies[key] = value

sessdata = cookies.get('SESSDATA', '')
bili_jct = cookies.get('bili_jct', '')
buvid3 = cookies.get('buvid3', '')

if not sessdata or not bili_jct:
    print("Error: Missing SESSDATA or bili_jct in Cookie.txt")
    print(f"Found keys: {list(cookies.keys())}")
    exit(1)

print(f"SESSDATA length: {len(sessdata)}")
print(f"BILI_JCT length: {len(bili_jct)}")
print(f"BUVID3: {buvid3}")
print()

cred = Credential(
    sessdata=sessdata,
    bili_jct=bili_jct,
    buvid3=buvid3,
)

# Dynamic content - daily style with tunnel link and auto-publish statement
content = """🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 https://became-determines-britain-competitive.trycloudflare.com

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"""

async def main():
    try:
        dyn = dynamic.BuildDynamic()
        dyn.add_text(content)
        result = await dynamic.send_dynamic(dyn, credential=cred)
        print("✅ 成功发布动态！")
        print(f"动态ID: {result.get('dyn_id_str')}")
        print(f"动态类型: {result.get('dyn_type')}")
    except Exception as e:
        print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
