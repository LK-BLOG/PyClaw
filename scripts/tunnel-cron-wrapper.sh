#!/bin/bash
# Cron包装脚本 - 每5分钟运行一次隧道监控

LOG_FILE="/home/claw/.openclaw/workspace/logs/tunnel-cron-wrapper.log"
MONITOR_SCRIPT="/home/claw/.openclaw/workspace/scripts/tunnel-monitor.sh"

mkdir -p "$(dirname "$LOG_FILE")"

# 记录执行时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行隧道监控" >> "$LOG_FILE"

# 执行监控脚本
OUTPUT=$(bash "$MONITOR_SCRIPT")
EXIT_CODE=$?

echo "$OUTPUT" >> "$LOG_FILE"

# 检查是否重新连接了
if echo "$EXIT_CODE" -eq 0; then
    if echo "$OUTPUT" | grep -q "TUNNEL_RECONNECTED:"; then
        NEW_URL=$(echo "$OUTPUT" | grep "TUNNEL_RECONNECTED:" | sed 's/TUNNEL_RECONNECTED://')
        echo "隧道已重新连接: $NEW_URL" >> "$LOG_FILE"
    fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行完成，退出码: $EXIT_CODE" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
