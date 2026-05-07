#!/bin/bash
# 提取 Cookie 并发布动态

SESSDATA=$(grep -oP '^SESSDATA=\K.*' /home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt)
bili_jct=$(grep -oP '^bili_jct=\K.*' /home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt)
buvid3=$(grep -oP '^buvid3=\K.*' /home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt || echo "")

export BILIBILI_SESSDATA="$SESSDATA"
export BILIBILI_BILI_JCT="$bili_jct"
export BILIBILI_BUVID3="$buvid3"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "个人网站更新地址👇
https://major-ants-clean.loca.lt
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"
