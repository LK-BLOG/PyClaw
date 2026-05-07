#!/bin/bash
cd /home/claw/.openclaw/workspace

# 读取Cookie
COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

urldecode() {
    local url_encoded="$1"
    printf '%b' "${url_encoded//%/\\x}"
}

if [ -f "$COOKIE_FILE" ]; then
    SESSDATA=$(grep -oP 'SESSDATA=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
    SESSDATA=$(urldecode "$SESSDATA")
    BILI_JCT=$(grep -oP 'bili_jct=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
    BUVID3=$(grep -oP 'buvid3=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
fi

# 环境变量优先
SESSDATA="${BILIBILI_SESSDATA:-$SESSDATA}"
BILI_JCT="${BILIBILI_BILI_JCT:-$BILI_JCT}"
BUVID3="${BILIBILI_BUVID3:-$BUVID3}"

export BILIBILI_SESSDATA="$SESSDATA"
export BILIBILI_BILI_JCT="$BILI_JCT"
export BILIBILI_BUVID3="$BUVID3"

CURRENT_URL="https://ten-ghosts-bake.loca.lt"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "个人网站更新地址👇
$CURRENT_URL

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"
