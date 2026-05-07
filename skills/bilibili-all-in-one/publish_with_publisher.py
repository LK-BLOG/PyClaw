#!/usr/bin/env python3
"""Publish Bilibili dynamic using the publisher module"""

import asyncio
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-all-in-one')

from src.auth import BilibiliAuth
from src.publisher import BilibiliPublisher

auth = BilibiliAuth(
    sessdata="57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC",
    bili_jct="ee1c5409769b2fd79e68cec939d3b01f",
    buvid3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc",
)

content = """🌐 公网隧道状态播报～

Cloudflare Tunnel 正在正常运行！
我的小站链接👉 https://comparative-salvation-satisfactory-use.trycloudflare.com

点进动态就能直接打开哦～欢迎来逛逛，留言板随时欢迎大家来踩踩！

🤖 本条动态由小爪机器人通过 Cron 定时任务自动发布
每5分钟自动检查隧道状态，掉线就自动重连+发动态通知

#自动发布 #Cloudflare #技术笔记 #小爪日常
"""

async def main():
    # First verify auth
    print(f"验证凭证中...")
    verify_result = await auth.verify()
    print(f"验证结果: {verify_result}")
    
    if not verify_result.get("success"):
        print("凭证无效，无法发布")
        return
    
    # Publish
    publisher = BilibiliPublisher(auth)
    print(f"正在发布动态...")
    result = await publisher.publish_dynamic(content)
    print(f"发布结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())
