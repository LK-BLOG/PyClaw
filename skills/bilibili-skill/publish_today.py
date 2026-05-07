#!/usr/bin/env python3
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic
from datetime import datetime

# 读取Cookie
cookies = {}
with open('/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt', 'r') as f:
    cookie_line = f.read().strip()
    for item in cookie_line.split('; '):
        if '=' in item:
            key, val = item.split('=', 1)
            cookies[key.strip()] = val.strip()

credential = Credential(
    sessdata=cookies.get('SESSDATA', ''),
    bili_jct=cookies.get('bili_jct', ''),
    buvid3=cookies.get('buvid3', '')
)

current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
tunnel_url = "https://removing-comparison-plymouth-relying.trycloudflare.com"

async def main():
    builder = BuildDynamic()
    builder.add_text(f"""🌤️ 晚间小播报～

跟大家同步一下，我的小站隧道还在稳定运行中！
👉 {tunnel_url}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么调皮～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用手动折腾啦！
科技改变摸鱼生活 ✌️

发布时间：{current_time}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活""")
    
    result = await dynamic.send_dynamic(builder, credential)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get('code') == 0:
        dyn_id = result.get('data', {}).get('dyn_id')
        print(f"✅ 发布成功！动态ID: {dyn_id}")
        print(f"✅ 动态链接: https://t.bilibili.com/{dyn_id}")
    else:
        print(f"❌ 发布失败: {result.get('message')}")

asyncio.run(main())
