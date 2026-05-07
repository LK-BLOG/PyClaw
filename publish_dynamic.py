#!/usr/bin/env python3
import os
import sys

# 添加bilibili-skill目录到路径
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')

# 从环境变量获取cookies
SESSDATA = os.environ.get('BILIBILI_SESSDATA', '')
BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', '')
BUVID3 = os.environ.get('BILIBILI_BUVID3', '')

if not all([SESSDATA, BILI_JCT, BUVID3]):
    print("Error: Cookies not found in environment variables")
    print(f"SESSDATA: {'set' if SESSDATA else 'missing'}")
    print(f"BILI_JCT: {'set' if BILI_JCT else 'missing'}")
    print(f"BUVID3: {'set' if BUVID3 else 'missing'}")
    sys.exit(1)

print("Cookies loaded successfully!")

# 导入CLI模块
from bilibili_cli import main

# 动态内容
content = """🤖 【自动发布】服务器状态更新 ✅

大家好！我的个人网站隧道已重新连接啦~ 🌐

🔗 访问地址：https://association-everyday-flights-believed.trycloudflare.com

这是通过 Cloudflare Tunnel 自动监控发布的动态，隧道每5分钟会自动检查一次，如果断开就会自动重连并通知大家~

服务器一直在线中，欢迎来玩！😉

#服务器状态 #自动发布 #Cloudflare #技术分享"""

# 构造参数
sys.argv = [
    'bilibili-cli.py',
    '--sessdata', SESSDATA,
    '--bili_jct', BILI_JCT,
    '--buvid3', BUVID3,
    'dynamic', 'publish',
    '--content', content
]

print("Publishing dynamic...")
main()
