#!/bin/bash
# 发布Cloudflare隧道状态动态

COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

export BILIBILI_SESSDATA=$(grep SESSDATA "$COOKIE_FILE" | cut -d= -f2-)
export BILIBILI_BILI_JCT=$(grep bili_jct "$COOKIE_FILE" | cut -d= -f2-)
export BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

TUNNEL_URL="https://brooklyn-instruction-joint-displays.trycloudflare.com"

CONTENT="🌙 凌晨更新！

个人网站隧道已自动恢复上线 ✅
访问地址 👉 $TUNNEL_URL

（点进动态才能打开链接哦，Cloudflare免费隧道就是这样的）

🤖 本条动态由 OpenClaw 自动发布
隧道监控 24 小时运行中，断了就自动重连～

#个人网站 #Cloudflare #自动发布 #OpenClaw"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "$CONTENT"
