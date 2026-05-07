#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
from bilibili_api import Credential, user

# 从 Cookie.txt 读取
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

SESSDATA = cookies.get('SESSDATA', '')
BILI_JCT = cookies.get('bili_jct', '')
BUVID3 = cookies.get('buvid3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')
DEDEUSERID = cookies.get('DedeUserID', '')

print(f"SESSDATA: {SESSDATA[:30]}...")
print(f"bili_jct: {BILI_JCT}")
print(f"DedeUserID: {DEDEUSERID}")
print(f"buvid3: {BUVID3}")

cred = Credential(
    sessdata=SESSDATA,
    bili_jct=BILI_JCT,
    buvid3=BUVID3
)

async def check_login():
    try:
        # 获取自己的信息
        if DEDEUSERID:
            self_user = user.User(uid=int(DEDEUSERID), credential=cred)
            info = await self_user.get_user_info()
            print(f"\n✅ 登录成功！")
            print(f"用户名: {info.get('name', '未知')}")
            print(f"等级: {info.get('level', 0)}")
            print(f"粉丝: {info.get('fans', 0)}")
        else:
            print("⚠️  没有 DedeUserID，跳过用户信息验证")
    except Exception as e:
        print(f"\n❌ 登录验证失败: {e}")

asyncio.run(check_login())