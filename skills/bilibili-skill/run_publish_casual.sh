#!/bin/bash
cd /home/claw/.openclaw/workspace/skills/bilibili-skill

# 从Cookie.txt读取环境变量
COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

export BILIBILI_SESSDATA=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "SESSDATA=" | cut -d= -f2-)
export BILIBILI_BILI_JCT=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "bili_jct=" | cut -d= -f2-)
export BILIBILI_BUVID3=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "buvid3=" | cut -d= -f2-)

echo "Cookie已加载"

# 动态内容
CONTENT="🌐 日常小播报～

跟大家同步一下，我的小站隧道又稳定运行啦！
👉 https://witnesses-jerry-integral-generated.trycloudflare.com

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare就是这么傲娇的哈哈哈～
欢迎来我的个人主页逛逛，留言板随时恭候！

🤖 悄悄说：这条动态是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用我手动操作啦！
科技改变摸鱼生活 ✌️

发布时间：$(date '+%Y-%m-%d %H:%M')

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"

echo "准备发布动态..."
echo "$CONTENT"
echo "===================="

python3 bilibili-cli.py dynamic publish --content "$CONTENT"
