#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

# 读取Cookie.txt并正确解析
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")

with open(cookie_file, 'r') as f:
    cookie_line = f.read().strip()

# 解析各个cookie值
def get_cookie_value(key):
    match = re.search(rf'{key}=([^;]+)', cookie_line)
    if match:
        return match.group(1)
    return None

SESSDATA = get_cookie_value('SESSDATA')
BILI_JCT = get_cookie_value('bili_jct')
BUVID3 = get_cookie_value('buvid3')

print(f"SESSDATA: {SESSDATA[:30]}...")
print(f"bili_jct: {BILI_JCT}")
print(f"buvid3: {BUVID3[:30]}...")

# 当前Cloudflare tunnel链接
tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"

content = f"""🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

print("\n" + "="*50)
print("动态内容:")
print(content)
print("="*50 + "\n")

# 使用bilibili-api-python发布
from bilibili_api import Credential, dynamic
import asyncio

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    
    # 发布动态
    builder = dynamic.BuildDynamic()
    builder.add_text(content)
    
    try:
        result = await dynamic.send_dynamic(builder, credential=cred)
        print(f"\n✅ 发布成功！")
        print(f"结果: {result}")
        dyn_id = result.get('data', {}).get('dyn_id', '未知')
        print(f"动态ID: {dyn_id}")
        return True
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(main())
