#!/bin/bash
# 循环监控隧道状态

WORKSPACE="/home/claw/.openclaw/workspace"
LOG_FILE="$WORKSPACE/scripts/logs/tunnel-monitor.log"
CHECK_INTERVAL=300  # 5分钟检查一次

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 隧道监控循环启动 ==="
log "检查间隔: ${CHECK_INTERVAL}秒"

while true; do
    # 执行监控脚本
    OUTPUT=$(cd "$WORKSPACE" && bash scripts/monitor-tunnel.sh 2>&1)
    echo "$OUTPUT" >> "$LOG_FILE"
    
    # 检查是否重连成功
    if echo "$OUTPUT" | grep -q "NEW_TUNNEL_URL:"; then
        NEW_URL=$(echo "$OUTPUT" | grep "NEW_TUNNEL_URL:" | cut -d':' -f2-)
        log "!!! 检测到隧道重连成功: $NEW_URL"
        
        # 保存到通知文件
        echo "$NEW_URL" > "$WORKSPACE/scripts/.last-reconnect"
        echo "$(date '+%Y-%m-%d %H:%M:%S')" >> "$WORKSPACE/scripts/.last-reconnect"
    fi
    
    sleep $CHECK_INTERVAL
done
