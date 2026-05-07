#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取
cookie_file = os.path.expanduser("~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    content = f.read().strip()
    for part in content.split(';'):
        part = part.strip()
        if '=' in part:
            key, value = part.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', '')
DEDEUSERID = cookies.get('DedeUserID', '')
AC_TIME_VALUE = cookies.get('ac_time_value', '')

tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"

content = f"""🌤️ 今日摸鱼播报～

跟大家说个好玩的，我把家里的小网站搭起来啦！
用Cloudflare隧道搞的，现在大家都能访问到 👉 {tunnel_url}

⚠️ 温馨提示：得点进动态详情页才能打开链接哦～
目前里面放了我的无人机作品集，以后还会慢慢加东西，欢迎来踩踩！

🤖 偷偷告诉你们，这条动态是机器人自动发的
现在写了个脚本每5分钟检查一次，隧道掉线会自动重连还会发动态通知
我终于不用每次手动敲命令了，科技改变摸鱼生活hhhh

大家周末愉快呀～ ☀️

#日常分享 #Cloudflare #技术摸鱼 #OpenClaw #小爪在干活
"""

cred = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3,
    dedeuserid=DEDEUSERID,
    ac_time_value=AC_TIME_VALUE
)

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, credential=cred)
    print("发布结果:")
    print(result)
    if result.get('code') == 0:
        print("\n✅ 动态发布成功！")
        dynamic_id = result.get('data', {}).get('dyn_id', result.get('dynamic_id', '未知'))
        print(f"动态ID: {dynamic_id}")
        print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
    else:
        print(f"\n❌ 发布失败: {result.get('message', '未知错误')}")

asyncio.run(publish())
