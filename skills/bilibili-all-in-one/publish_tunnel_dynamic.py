#!/usr/bin/env python3
"""Publish Bilibili dynamic with Cloudflare tunnel link"""

import asyncio
import os
from bilibili_api import dynamic, Credential

# Get credentials from environment variables
sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

if not sessdata or not bili_jct:
    print("Error: Missing credentials")
    exit(1)

cred = Credential(
    sessdata=sessdata,
    bili_jct=bili_jct,
    buvid3=buvid3,
)

content = """🌐 公网隧道状态播报～

Cloudflare Tunnel 正在正常运行！
我的小站链接👉 https://nvidia-partner-consolidated-dec.trycloudflare.com

点进动态就能直接打开哦～欢迎来逛逛，留言板随时欢迎大家来踩踩！

🤖 本条动态由小爪机器人通过 Cron 定时任务自动发布
每5分钟自动检查隧道状态，掉线就自动重连+发动态通知

#自动发布 #Cloudflare #技术笔记 #小爪日常
"""

async def main():
    try:
        dyn = dynamic.BuildDynamic()
        dyn.add_text(content)
        result = await dynamic.send_dynamic(dyn, credential=cred)
        print(f"✅ 成功发布动态！ID: {result.get('dyn_id_str')}")
    except Exception as e:
        print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
