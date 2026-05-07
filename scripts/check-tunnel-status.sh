#!/bin/bash
# 检查隧道状态和恢复通知

WORKSPACE="/home/claw/.openclaw/workspace"
NOTIFY_FILE="$WORKSPACE/logs/tunnel-restore-notify.txt"
TOOLS_FILE="$WORKSPACE/TOOLS.md"
LOG_FILE="$WORKSPACE/logs/tunnel-monitor.log"

echo "=== 隧道状态检查 ==="
echo ""

# 当前URL
CURRENT_URL=$(grep -oP '当前公网链接: \K[^\n]+' "$TOOLS_FILE" 2>/dev/null)
echo "当前公网链接: $CURRENT_URL"
echo ""

# 检查网站状态
echo "检查网站连接..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$CURRENT_URL" 2>/dev/null)
CURL_EXIT=$?

if [ $CURL_EXIT -eq 0 ] && [ -n "$HTTP_STATUS" ] && [ "$HTTP_STATUS" != "000" ]; then
    echo "✅ 网站正常运行 (HTTP $HTTP_STATUS)"
else
    echo "❌ 网站无法访问"
fi
echo ""

# 检查是否有未读的恢复通知
if [ -f "$NOTIFY_FILE" ]; then
    echo "📢 未读的恢复通知:"
    cat "$NOTIFY_FILE"
    echo ""
    read -p "是否清除通知? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$NOTIFY_FILE"
        echo "通知已清除"
    fi
else
    echo "✅ 没有未读的恢复通知"
fi
echo ""

# 最近的监控日志
echo "最近的监控日志 (最后10条):"
if [ -f "$LOG_FILE" ]; then
    tail -10 "$LOG_FILE"
else
    echo "暂无日志"
fi
