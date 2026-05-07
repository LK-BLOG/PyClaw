#!/usr/bin/env python3
"""Test credentials and publish dynamic"""

import asyncio
import json
import sys
import os

# Try to get credentials from various sources

# 1. Environment variables
sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

print(f"1. Environment variables:")
print(f"   SESSDATA: {'✅ 设置' if sessdata else '❌ 未设置'} (长度: {len(sessdata)})")
print(f"   bili_jct: {'✅ 设置' if bili_jct else '❌ 未设置'} (长度: {len(bili_jct)})")
print(f"   buvid3: {'✅ 设置' if buvid3 else '❌ 未设置'}")

# 2. Try bilibili_creds.json
if not sessdata or not bili_jct:
    cred_file = "/home/claw/.openclaw/workspace/bilibili_creds.json"
    if os.path.exists(cred_file):
        try:
            with open(cred_file, "r") as f:
                cred = json.load(f)
            if not sessdata and cred.get("sessdata"):
                sessdata = cred["sessdata"]
                print(f"\n2. 从 bilibili_creds.json 读取 SESSDATA")
            if not bili_jct and cred.get("bili_jct"):
                bili_jct = cred["bili_jct"]
                print(f"2. 从 bilibili_creds.json 读取 bili_jct")
            if not buvid3 and cred.get("buvid3"):
                buvid3 = cred["buvid3"]
        except Exception as e:
            print(f"\n2. 读取 bilibili_creds.json 失败: {e}")

# 3. Try credentials in skill directory
if not sessdata or not bili_jct:
    skill_cred = "/home/claw/.openclaw/workspace/skills/bilibili-all-in-one/credentials.json"
    if os.path.exists(skill_cred):
        try:
            with open(skill_cred, "r") as f:
                cred = json.load(f)
            if not sessdata and cred.get("sessdata"):
                sessdata = cred["sessdata"]
                print(f"\n3. 从 skill credentials.json 读取 SESSDATA")
            if not bili_jct and cred.get("bili_jct"):
                bili_jct = cred["bili_jct"]
                print(f"3. 从 skill credentials.json 读取 bili_jct")
        except Exception as e:
            print(f"\n3. 读取 skill credentials.json 失败: {e}")

print("\n" + "="*50)

if not sessdata or not bili_jct:
    print("\n❌ 没有找到有效的B站凭证！")
    print("需要重新扫码登录获取新凭证。")
    sys.exit(1)

print("\n✅ 找到凭证，正在验证...")

# Verify credentials
try:
    from bilibili_api import user, Credential
    
    cred = Credential(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3,
    )
    
    # Test credential
    self_user = user.User(uid=0, credential=cred)
    info = asyncio.run(self_user.get_self_info())
    print(f"✅ 凭证有效！登录用户: {info.get('name', '未知')}")
    
except Exception as e:
    print(f"❌ 凭证验证失败: {type(e).__name__}: {e}")
    print("需要重新扫码登录获取新凭证。")
    sys.exit(1)

# Now publish dynamic
print("\n" + "="*50)
print("正在发布动态...")

from bilibili_api import dynamic

content = """🌐 隧道状态更新～

Cloudflare Tunnel 正在正常运行！
我的小站链接👉 https://academy-muze-potatoes-consortium.trycloudflare.com

点进动态就能直接打开哦～欢迎来逛逛，留言板随时欢迎大家来踩踩！

🤖 本条动态由小爪机器人通过 Cron 定时任务自动发布
每5分钟自动检查隧道状态，掉线就自动重连+发动态通知

#自动发布 #Cloudflare #技术笔记 #小爪日常
"""

try:
    dyn = dynamic.BuildDynamic()
    dyn.add_text(content)
    result = asyncio.run(dynamic.send_dynamic(dyn, credential=cred))
    dyn_id = result.get('dyn_id_str')
    print(f"✅ 成功发布动态！ID: {dyn_id}")
    print(f"动态链接: https://t.bilibili.com/{dyn_id}")
    sys.exit(0)
except Exception as e:
    print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
    sys.exit(1)
