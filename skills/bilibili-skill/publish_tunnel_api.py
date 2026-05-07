#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from datetime import datetime
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', '')

tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""🌐 日常小播报！

跟大家同步一下，我的小站隧道又稳定运行啦～
👉 {tunnel_url}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare就是这么傲娇的哈哈哈～
欢迎来我的个人主页逛逛，留言板随时恭候！

🤖 悄悄说：这条动态是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用我手动操作啦！
科技改变摸鱼生活 ✌️

发布时间：{current_time}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print(f"发布时间: {current_time}")
print()
print("="*50)
print("动态内容:")
print(content)
print("="*50)
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
        print("\n✅ 动态发布成功！")
        dynamic_id = result.get('dynamic_id', '未知')
        print(f"动态ID: {dynamic_id}")
        print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
        print(f"完整结果: {result}")
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(publish())
