#!/bin/bash
cd /home/claw/.openclaw/workspace/skills/bilibili-skill

NEW_URL="https://freedom-arabia-boundaries-wma.trycloudflare.com"
CONTENT="个人网站更新地址👇
${NEW_URL}
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

python3 bilibili-cli.py \
  --sessdata "$BILIBILI_SESSDATA" \
  --bili_jct "$BILIBILI_BILI_JCT" \
  --buvid3 "$BILIBILI_BUVID3" \
  dynamic publish --content "$CONTENT"
