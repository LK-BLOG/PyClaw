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

# 当前 Cloudflare Tunnel 链接
tunnel_url = "https://clearly-cache-power-favour.trycloudflare.com"

content = f"""🤖 自动发布打卡~

今天的 Cloudflare Tunnel 链接已经上线啦：
{tunnel_url}

（得点进动态才能打开链接哦，Cloudflare 免费隧道就是这么设置的）

这条动态是通过 OpenClaw 的 Cron 定时任务自动发布的，用来同步最新的隧道地址，这样大家随时都能访问到我本地的服务啦~ 😄

✅ 隧道状态：正常运行
⏰ 更新时间：2026-04-23 15:39

欢迎来留言板唠嗑～"""

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
