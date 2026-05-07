#!/usr/bin/env python3
"""日常动态发布脚本 - 包含隧道链接 + 自动发布声明"""
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

# 当前隧道链接
tunnel_url = "https://strategies-apparatus-appreciate-limit.trycloudflare.com"

content = f"""🌐 网站又上线啦～
{tunnel_url}

Cloudflare 隧道把本地服务暴露到公网，免费又好用！
点进动态详情才能打开链接哦～（自动发布）"""

print("准备发布日常动态...")

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
        raise

asyncio.run(main())
