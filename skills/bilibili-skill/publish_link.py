#!/usr/bin/env python3
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

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

async def main():
    builder = BuildDynamic()
    builder.add_text("""个人网站更新地址👇
https://optimize-cherry-logical-alcohol.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)""")
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
