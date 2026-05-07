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

tunnel_url = "https://astronomy-color-pros-arm.trycloudflare.com"

content = f"""个人网站更新地址👇
{tunnel_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

print("准备发布动态...")

from bilibili_api import Credential, dynamic

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    builder = dynamic.BuildDynamic()
    builder.add_text(content)
    try:
        result = await dynamic.send_dynamic(builder, credential=cred)
        print(f"发布成功！结果: {result}")
    except Exception as e:
        print(f"发布失败: {e}")

asyncio.run(main())
