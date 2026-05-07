#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
from bilibili_api import login_v2

async def qr_login():
    # 创建二维码登录实例
    qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
    
    # 生成二维码
    await qr.generate_qrcode()
    
    # 在终端打印二维码
    print("=" * 50)
    print("请使用 Bilibili App 扫描下方二维码登录")
    print("=" * 50)
    print()
    print(qr.get_qrcode_terminal())
    print()
    print("等待扫码中... (按 Ctrl+C 取消)")
    
    # 轮询检查登录状态
    max_wait = 180  # 最多等待3分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        state = await qr.check_state()
        
        if state == login_v2.QrCodeLoginEvents.SCAN:
            print("📱 二维码等待扫描...")
        elif state == login_v2.QrCodeLoginEvents.CONF:
            print("✅ 已扫码，请在手机上确认登录...")
        elif state == login_v2.QrCodeLoginEvents.DONE:
            print("\n🎉 登录成功！")
            cred = qr.get_credential()
            
            # 打印获取到的 cookie
            print("\n" + "=" * 50)
            print("获取到的 Credential:")
            print("=" * 50)
            print(f"SESSDATA: {cred.sessdata}")
            print(f"bili_jct: {cred.bili_jct}")
            print(f"buvid3: {cred.buvid3}")
            print(f"DedeUserID: {cred.dedeuserid}")
            print(f"ac_time_value: {cred.ac_time_value}")
            print()
            
            # 保存到 Cookie.txt
            cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
            with open(cookie_file, 'w') as f:
                f.write(f"SESSDATA={cred.sessdata}\n")
                f.write(f"bili_jct={cred.bili_jct}\n")
                f.write(f"buvid3={cred.buvid3}\n")
                if cred.dedeuserid:
                    f.write(f"DedeUserID={cred.dedeuserid}\n")
                if cred.ac_time_value:
                    f.write(f"ac_time_value={cred.ac_time_value}\n")
            
            print(f"✅ Cookie 已保存到: {cookie_file}")
            return cred
            
        elif state == login_v2.QrCodeLoginEvents.TIMEOUT:
            print("\n❌ 二维码已过期，请重新运行脚本")
            return None
        
        await asyncio.sleep(2)
    
    print("\n⏰ 等待超时")
    return None

if __name__ == "__main__":
    try:
        asyncio.run(qr_login())
    except KeyboardInterrupt:
        print("\n\n已取消")
