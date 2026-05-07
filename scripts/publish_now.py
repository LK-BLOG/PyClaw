#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio

# 添加bilibili-api-python可能需要的路径
sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.12/site-packages"))

from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取
cookie_file = os.path.expanduser("/home/claw/.openclaw/workspace/pyclaw-public/skills/bilibili/Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    # Cookie可能是用分号分隔的一整行
    for part in cookie_content.split(';'):
        part = part.strip()
        if '=' in part:
            key, value = part.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', '')

print(f"解析到的Cookie keys: {list(cookies.keys())}")
print(f"SESSDATA长度: {len(SESSDATA)}")
print(f"BILI_JCT长度: {len(BILI_JCT)}")
print(f"BUVID3: {BUVID3[:20]}..." if BUVID3 else "BUVID3: None")
print()

# 当前隧道链接
tunnel_url = "https://sacrifice-roll-bradford-name.trycloudflare.com"

content = """🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活""".format(tunnel_url=tunnel_url)

print("即将发布的内容：")
print("=" * 50)
print(content)
print("=" * 50)
print()

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
        print("✅ 发布成功!")
        print("发布结果:")
        print(result)
        if isinstance(result, dict) and 'dynamic_id' in result:
            print(f"动态链接: https://t.bilibili.com/{result['dynamic_id']}")
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(publish())
