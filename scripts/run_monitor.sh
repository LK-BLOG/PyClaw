#!/bin/bash
# Cloudflare Tunnel 监控脚本 - 由 cron 调用

cd /home/claw/.openclaw/workspace/scripts

# 日志文件
LOG_FILE="/home/claw/.openclaw/workspace/logs/tunnel_monitor.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 运行 Python 脚本
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"
python3 monitor_and_publish.py 2>&1 | tee -a "$LOG_FILE"
