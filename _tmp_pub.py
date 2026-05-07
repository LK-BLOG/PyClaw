#!/usr/bin/env python3
"""Temporary publish script for B站 dynamic"""
import os
import sys
import re

# Read cookies from file
with open('/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt') as f:
    cookie_text = f.read()

def get_cookie_val(key):
    m = re.search(rf'{key}=([^;]+)', cookie_text)
    return m.group(1) if m else ''

sessdata = get_cookie_val('SESSDATA')
bili_jct = get_cookie_val('bili_jct')
buvid3 = get_cookie_val('buvid3')

os.environ['BILIBILI_SESSDATA'] = sessdata
os.environ['BILIBILI_BILI_JCT'] = bili_jct
os.environ['BILIBILI_BUVID3'] = buvid3

sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')

from bilibili_cli import main

content = """🌐 网站还在跑着呢~

Cloudflare Tunnel 自动连接中 🔄
🔗 https://giant-mutual-papers-champions.trycloudflare.com

（本动态由服务器自动发布，隧道每5分钟检测一次，断开自动重连）

#日常 #Cloudflare #服务器状态"""

sys.argv = [
    'bilibili-cli.py',
    'dynamic', 'publish',
    '--content', content
]

print("正在发布B站动态...")
main()
