#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

COOKIE_FILE = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

def read_cookies():
    cookies = {}
    with open(COOKIE_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                cookies[key] = value
    return cookies

async def test_publish():
    cookies = read_cookies()
    SESSDATA = cookies.get('SESSDATA', '')
    BILI_JCT = cookies.get('bili_jct', '')
    BUVID3 = cookies.get('buvid3', '')
    
    cred = Credential(
        sessdata=SESSDATA,
        bili_jct=BILI_JCT,
        buvid3=BUVID3
    )
    
    content = "测试动态发布（监控脚本验证）"
    
    try:
        builder = BuildDynamic()
        builder.add_text(content)
        result = await dynamic.send_dynamic(builder, cred)
        print("✅ 发布成功！")
        print(f"结果: {result}")
        return True
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_publish())
