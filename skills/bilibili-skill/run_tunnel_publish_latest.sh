#!/bin/bash
# 发布Cloudflare隧道状态动态

COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

export BILIBILI_SESSDATA=$(grep SESSDATA "$COOKIE_FILE" | cut -d= -f2-)
export BILIBILI_BILI_JCT=$(grep bili_jct "$COOKIE_FILE" | cut -d= -f2-)
export BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

TUNNEL_URL="https://became-determines-britain-competitive.trycloudflare.com"

CONTENT="☀️ 早安！

个人网站隧道正在运行中 ✅
访问地址 👉 $TUNNEL_URL

（得点进动态才能打开链接哦，Cloudflare免费隧道就是这么设置的）

🤖 本条动态由 OpenClaw 自动发布
隧道 24 小时监控运行中，断了就自动重连～
欢迎来留言板唠嗑～

#个人网站 #Cloudflare #自动发布 #OpenClaw"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "$CONTENT"