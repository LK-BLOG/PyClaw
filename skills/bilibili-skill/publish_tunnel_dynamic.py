#!/usr/bin/env python3
import os
import re
import asyncio

# 读取Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
with open(cookie_file, 'r') as f:
    cookie_line = f.read().strip()

def get_cookie_value(key):
    match = re.search(rf'{key}=([^;]+)', cookie_line)
    if match:
        return match.group(1)
    return None

SESSDATA = get_cookie_value('SESSDATA')
BILI_JCT = get_cookie_value('bili_jct')
BUVID3 = get_cookie_value('buvid3')

tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"

content = f"""嘿！我的个人小站又上线啦 😄

👉 {tunnel_url}

（链接要点进动态详情页才能打开哦，Cloudflare免费隧道就是这样的~）

欢迎来留言板随便逛逛、留个言！有什么想聊的都可以说~

这是机器人自动发布的，隧道健康运行中 ✨"""

print("准备发布动态...")
print(f"内容:\n{content}")
print()

from bilibili_api import Credential, dynamic

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    builder = dynamic.BuildDynamic()
    builder.add_text(content)
    try:
        result = await dynamic.send_dynamic(builder, credential=cred)
        print(f"✅ 发布成功！")
        print(f"结果: {result}")
        if isinstance(result, dict) and 'dyn_id' in result:
            print(f"动态ID: {result['dyn_id']}")
            print(f"动态链接: https://t.bilibili.com/{result['dyn_id']}")
    except Exception as e:
        print(f"❌ 发布失败: {e}")

asyncio.run(main())
