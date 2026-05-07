#!/bin/bash
# 发布最新B站动态

COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

export BILIBILI_SESSDATA=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "SESSDATA=" | cut -d= -f2-)
export BILIBILI_BILI_JCT=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "bili_jct=" | cut -d= -f2-)
export BILIBILI_BUVID3=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "buvid3=" | cut -d= -f2-)

CONTENT="🌙 晚上好呀～

跟大家汇报一下，我的个人小网站还在稳稳运行中！
👉 https://recycling-possibilities-lecture-jewel.trycloudflare.com

💡 小提示：链接要复制到浏览器或者点进动态详情页才能打开哦，Cloudflare免费隧道就是这么傲娇的～
做了个简单的个人主页，放了些无人机作品，有空可以来逛逛呀，留言板也准备好了！

🤖 偷偷说，这条动态是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知，再也不用手动折腾啦！

#日常 #Cloudflare #技术摸鱼 #小爪在干活"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "$CONTENT"
