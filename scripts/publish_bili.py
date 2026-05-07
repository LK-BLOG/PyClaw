#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/skills/bilibili-skill'))

import urllib.parse
from bilibili_api import Credential
from bilibili_api import dynamic
from bilibili_api.dynamic import BuildDynamic
import asyncio
import json

# 解析Cookie
cookie_path = os.path.expanduser('~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt')
cookie_str = open(cookie_path).read().strip()

def get_cookie_val(key):
    for item in cookie_str.split('; '):
        if item.startswith(key + '='):
            return item.split('=', 1)[1]
    return ''

SESSDATA = urllib.parse.unquote(get_cookie_val('SESSDATA'))
bili_jct = get_cookie_val('bili_jct')
buvid3 = get_cookie_val('buvid3')

print(f'SESSDATA: {len(SESSDATA)} chars')
print(f'bili_jct: {len(bili_jct)} chars')

cred = Credential(sessdata=SESSDATA, bili_jct=bili_jct, buvid3=buvid3)

# 从文件读取当前隧道URL
tunnel_url = open(os.path.expanduser('~/.openclaw/workspace/scripts/current-tunnel-url.txt')).read().strip()

# 动态内容
content = f"""网站正常访问中~

🔗 {tunnel_url}

🤖 本动态由OpenClaw自动发布"""

async def main():
    builder = BuildDynamic()
    builder.add_text(content.strip())
    result = await dynamic.send_dynamic(builder, cred)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    dyn_id = result.get('data', {}).get('dyn_id')
    if dyn_id:
        print(f'\n✅ 发布成功！动态ID: {dyn_id}')
        print(f'动态链接: https://t.bilibili.com/{dyn_id}')
    else:
        print('发布完成')

asyncio.run(main())
