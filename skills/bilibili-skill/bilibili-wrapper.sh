#!/bin/bash
# Bilibili Skill wrapper - 读取Cookie并执行bilibili-cli命令

# 从Cookie.txt读取环境变量
COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

# 正确提取每个Cookie值（用分号分隔）
export BILIBILI_SESSDATA=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "SESSDATA=" | cut -d= -f2-)
export BILIBILI_BILI_JCT=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "bili_jct=" | cut -d= -f2-)
export BILIBILI_BUVID3=$(cat "$COOKIE_FILE" | tr ';' '\n' | grep "buvid3=" | cut -d= -f2-)

# 调试输出
echo "DEBUG: SESSDATA = ${BILIBILI_SESSDATA:0:20}..."
echo "DEBUG: bili_jct = ${BILIBILI_BILI_JCT}"

# 执行bilibili-cli
python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py "$@"
