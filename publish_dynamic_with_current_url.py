#!/usr/bin/env python3
"""Publish Bilibili dynamic with current Cloudflare tunnel URL"""

import asyncio
import json
import sys
from bilibili_api import Credential, dynamic, user

# Current tunnel URL from TOOLS.md
TUNNEL_URL = "https://thing-mistress-kingston-legitimate.trycloudflare.com"

# Read cookies from Cookie.txt
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
sessdata = ""
bili_jct = ""
buvid3 = "BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('SESSDATA='):
            sessdata = line.split('=', 1)[1]
        elif line.startswith('bili_jct='):
            bili_jct = line.split('=', 1)[1]
        elif line.startswith('buvid3='):
            buvid3 = line.split('=', 1)[1]

print(f"SESSDATA: {sessdata[:20]}...")
print(f"bili_jct: {bili_jct[:10]}...")
print(f"buvid3: {buvid3}\n")

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def test_credential():
    """Test if credential is valid"""
    try:
        print("正在验证凭证...")
        self_user = user.User(uid=0, credential=cred)
        info = await self_user.get_self_info()
        print(f"✅ 凭证有效！用户名: {info.get('name', '未知')}")
        return True
    except Exception as e:
        print(f"❌ 凭证无效: {type(e).__name__}: {str(e)}")
        return False

async def publish_dynamic():
    """Publish dynamic with tunnel link"""
    
    content = f"""🌐 隧道状态更新～

Cloudflare Tunnel 正在正常运行！
我的小站链接👉 {TUNNEL_URL}

点进动态就能直接打开哦～欢迎来逛逛，留言板随时欢迎大家来踩踩！

🤖 本条动态由小爪机器人自动发布
每5分钟自动检查隧道状态，掉线就自动重连+发动态通知

#自动发布 #Cloudflare #技术笔记 #小爪日常
"""
    
    print("\n正在发布动态...")
    print(f"内容:\n{content}\n")
    
    try:
        dyn = dynamic.BuildDynamic()
        dyn.add_text(content)
        result = await dynamic.send_dynamic(dyn, credential=cred)
        print("发布结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        dynamic_id = result.get('dyn_id_str') or result.get('data', {}).get('dyn_id_str')
        if dynamic_id:
            print(f"\n✅ 成功发布动态！ID: {dynamic_id}")
            print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
        return True
    except Exception as e:
        print(f"\n❌ 发布失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    # Test credential first
    if not await test_credential():
        print("\n凭证无效，无法发布动态")
        return 1
    
    # Publish dynamic
    success = await publish_dynamic()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
