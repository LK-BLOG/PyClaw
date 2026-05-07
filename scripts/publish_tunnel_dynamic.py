#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布隧道状态动态"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

import urllib.parse, re

def get_credential_from_file(cookie_file):
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_content = f.read().strip()
    def get_cookie_value(key):
        match = re.search(rf'{key}=([^;]+)', cookie_content)
        if match:
            return urllib.parse.unquote(match.group(1).strip())
        return ""
    sessdata = get_cookie_value('SESSDATA')
    bili_jct = get_cookie_value('bili_jct')
    buvid3 = get_cookie_value('buvid3')
    if not all([sessdata, bili_jct]):
        print(f"Cookie不完整", file=sys.stderr)
        sys.exit(1)
    return Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def main():
    content = sys.argv[1]
    cookie_file = os.path.expanduser("~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt")
    cred = get_credential_from_file(cookie_file)
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    dyn_id = result.get('data', {}).get('dyn_id', '未知')
    print(f"✅ 发布成功！动态ID: {dyn_id}")
    print(f"https://t.bilibili.com/{dyn_id}")

if __name__ == "__main__":
    asyncio.run(main())
