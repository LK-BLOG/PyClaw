#!/usr/bin/env python3
"""
Publish Bilibili dynamic with Cloudflare tunnel info.
"""

import asyncio
import os
import sys

# Add venv to path
sys.path.insert(0, '/home/claw/.openclaw/workspace/venv/lib/python3.12/site-packages')

from bilibili_api import dynamic, Credential

# Get credentials from environment variables
sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

if not sessdata or not bili_jct:
    print("Error: Missing BILIBILI_SESSDATA or BILIBILI_BILI_JCT environment variables")
    exit(1)

cred = Credential(
    sessdata=sessdata,
    bili_jct=bili_jct,
    buvid3=buvid3,
)

# Dynamic content - daily style
tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"
content = f"""🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

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
        print(f"动态链接: https://t.bilibili.com/{result.get('dyn_id_str')}")
    except Exception as e:
        print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
