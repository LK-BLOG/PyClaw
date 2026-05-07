#!/bin/bash
# 读取Cookie并设置环境变量
COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

# 从Cookie中提取各个值
SESSDATA=$(grep -o 'SESSDATA=[^;]*' "$COOKIE_FILE" | cut -d'=' -f2)
BILI_JCT=$(grep -o 'bili_jct=[^;]*' "$COOKIE_FILE" | cut -d'=' -f2)
BUVID3=$(grep -o 'buvid3=[^;]*' "$COOKIE_FILE" | cut -d'=' -f2)

export BILIBILI_SESSDATA="$SESSDATA"
export BILIBILI_BILI_JCT="$BILI_JCT"
export BILIBILI_BUVID3="$BUVID3"

echo "SESSDATA长度: ${#SESSDATA}"
echo "bili_jct: $BILI_JCT"
echo "buvid3: $BUVID3"

# 发布内容
CONTENT="个人网站更新地址👇
https://warrant-independence-bacon-attempt.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

cd /home/claw/.openclaw/workspace/skills/bilibili-skill
python3 bilibili-cli.py dynamic publish --content "$CONTENT"
