#!/bin/bash
# Cron 包装脚本 - 用于定时执行隧道监控

LOG_FILE="/home/claw/.openclaw/workspace/scripts/logs/monitor_cron.log"
PID_FILE="/home/claw/.openclaw/workspace/scripts/monitor.pid"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 记录时间
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"

# 检查是否已有进程在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "监控进程已在运行 (PID: $PID)，跳过本次执行" >> "$LOG_FILE"
        exit 0
    fi
fi

# 执行监控脚本，记录PID
python3 /home/claw/.openclaw/workspace/scripts/monitor_and_publish.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# 等待最多2分钟让脚本完成
sleep 120

# 检查进程是否还在运行，如果还在运行就杀掉（可能是cloudflared还在运行，我们就让它继续）
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        # 检查是否是cloudflared，如果是就保留，否则杀掉
        if ! ps aux | grep "$PID" | grep -q cloudflared; then
            kill "$PID" 2>/dev/null
        fi
    fi
    rm -f "$PID_FILE"
fi

echo "执行完成" >> "$LOG_FILE"
