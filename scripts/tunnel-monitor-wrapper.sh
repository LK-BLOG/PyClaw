#!/bin/bash
# 隧道监控包装脚本 - 将结果输出到通知文件

WORKSPACE="/home/claw/.openclaw/workspace"
NOTIFY_FILE="$WORKSPACE/logs/tunnel-restore-notify.txt"
LOG_FILE="$WORKSPACE/logs/tunnel-monitor.log"

# 运行监控脚本并捕获输出
OUTPUT=$(cd "$WORKSPACE" && ./scripts/tunnel-monitor.sh 2>&1)
EXIT_CODE=$?

# 检查是否有新链接
NEW_URL=$(echo "$OUTPUT" | grep -oP 'TUNNEL_RECONNECTED:\K.*' | head -1)

if [ -n "$NEW_URL" ]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] 隧道已恢复！新链接: $NEW_URL" > "$NOTIFY_FILE"
    echo "[$TIMESTAMP] 隧道已恢复！新链接: $NEW_URL" >> "$LOG_FILE"
    # 保存最新URL供主会话读取
    echo "$NEW_URL" > "$WORKSPACE/logs/latest-tunnel-url.txt"
    echo "NEW_URL_DETECTED_AT: $TIMESTAMP" >> "$WORKSPACE/logs/latest-tunnel-url.txt"
fi

exit $EXIT_CODE
