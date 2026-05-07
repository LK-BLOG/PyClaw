#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
import requests
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

from urllib.parse import unquote

SESSDATA = unquote(cookies.get('SESSDATA', ''))
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')
DEDEUSERID = cookies.get('DedeUserID', '')
AC_TIME_VALUE = cookies.get('ac_time_value', '')
BILI_TICKET = cookies.get('bili_ticket', '')
B_LSID = cookies.get('b_lsid', '')
SID = cookies.get('sid', '')

print("使用的Cookie:")
print(f"  SESSDATA: {SESSDATA[:30]}...")
print(f"  bili_jct: {BILI_JCT}")
print(f"  DedeUserID: {DEDEUSERID}")
print(f"  bili_ticket: {BILI_TICKET[:30]}...")
print()

# 当前Cloudflare tunnel链接
tunnel_url = "https://cigarettes-bridal-nickname-universities.trycloudflare.com"

from datetime import datetime
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""🌤️ 午间小播报～

跟大家同步一下，我的小站隧道还在稳定运行中！
👉 {tunnel_url}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么调皮～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用手动折腾啦！
科技改变摸鱼生活 ✌️

发布时间：{current_time}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])

# 尝试直接用requests发布
async def publish_direct():
    try:
        url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Referer": "https://t.bilibili.com/",
            "Origin": "https://t.bilibili.com"
        }
        data = {
            "type": 4,
            "content": content,
            "csrf": BILI_JCT,
            "from": "create.dynamic.web"
        }
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        print(f"API响应: {result}")
        if result.get('code') == 0:
            print("✅ 动态发布成功！")
            return True
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

# 用bilibili_api发布
async def publish_api():
    try:
        cred = Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3,
            dedeuserid=DEDEUSERID,
            ac_time_value=AC_TIME_VALUE
        )
        builder = BuildDynamic()
        builder.add_text(content)
        result = await dynamic.send_dynamic(builder, credential=cred)
        print("✅ 动态发布成功！")
        dynamic_id = result.get('dynamic_id', '未知')
        print(f"动态ID: {dynamic_id}")
        print(f"\n动态内容:\n{content}")
        return True, dynamic_id
    except Exception as e:
        print(f"❌ API发布失败: {e}")
        return False, str(e)

if __name__ == "__main__":
    print("尝试直接API请求...")
    asyncio.run(publish_direct())
    print("\n尝试bilibili_api库...")
    asyncio.run(publish_api())
