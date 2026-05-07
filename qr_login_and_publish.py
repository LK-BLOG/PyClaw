#!/usr/bin/env python3
"""QR code login and publish dynamic with tunnel link"""

import asyncio
import json
import sys
import os
from bilibili_api import login_v2, dynamic, Credential

# Add workspace to path
sys.path.insert(0, '/home/claw/.openclaw/workspace')

# Current tunnel URL from TOOLS.md
TUNNEL_URL = "https://ought-adjacent-las-lancaster.trycloudflare.com"

# Credential file path
CRED_FILE = "/home/claw/.openclaw/workspace/bilibili_credentials.json"


async def qr_login():
    """Perform QR code login and return credential"""
    print("正在生成B站登录二维码...")
    print("请使用B站APP扫码登录\n")
    
    # Create QR code login
    qr = login_v2.QrCodeLogin()
    
    # Generate QR code
    qr_picture = qr.get_qrcode_picture()
    print(f"二维码URL: {qr_picture}")
    print("\n请复制链接到浏览器打开，使用B站APP扫描二维码\n")
    
    # Generate terminal QR code
    try:
        import qrcode_terminal
        qrcode_terminal.draw(qr_picture)
    except Exception as e:
        print(f"无法显示终端二维码: {e}")
        print(f"请手动访问: {qr_picture}")
    
    # Poll for login result
    print("\n等待扫码登录...（60秒超时）")
    result = await qr.confirm(time=60)
    
    if result is None:
        print("❌ 登录超时")
        return None
    
    # Get credential
    credential = qr.get_credential()
    print(f"✅ 登录成功！")
    
    # Save credentials to file
    cred_data = {
        "sessdata": credential.sessdata,
        "bili_jct": credential.bili_jct,
        "buvid3": credential.buvid3,
    }
    
    # Save with secure permissions
    os.makedirs(os.path.dirname(CRED_FILE) or ".", exist_ok=True)
    fd = os.open(CRED_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cred_data, f, indent=2)
        print(f"✅ 凭证已保存到: {CRED_FILE}")
    except Exception:
        os.close(fd)
        raise
    
    return credential


async def publish_dynamic_with_credential(credential):
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
        result = await dynamic.send_dynamic(dyn, credential=credential)
        dynamic_id = result.get('dyn_id_str')
        print(f"✅ 成功发布动态！ID: {dynamic_id}")
        print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
        return True, dynamic_id
    except Exception as e:
        print(f"❌ 发布失败: {type(e).__name__}: {str(e)}")
        return False, str(e)


async def main():
    # First, try to load existing credentials
    credential = None
    if os.path.exists(CRED_FILE):
        print(f"找到凭证文件: {CRED_FILE}")
        try:
            with open(CRED_FILE, "r", encoding="utf-8") as f:
                cred_data = json.load(f)
            credential = Credential(
                sessdata=cred_data.get("sessdata", ""),
                bili_jct=cred_data.get("bili_jct", ""),
                buvid3=cred_data.get("buvid3", ""),
            )
            # Test if credential is valid
            print("正在验证凭证是否有效...")
            from bilibili_api import user
            self_user = user.User(uid=0, credential=credential)
            await self_user.get_self_info()
            print("✅ 凭证有效！")
        except Exception as e:
            print(f"❌ 凭证无效: {e}")
            credential = None
    
    # If no valid credential, do QR login
    if not credential:
        credential = await qr_login()
        if not credential:
            print("❌ 无法获取有效凭证")
            return 1
    
    # Publish dynamic
    success, result = await publish_dynamic_with_credential(credential)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
