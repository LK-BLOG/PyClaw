#!/bin/bash
# Cloudflare Tunnel 监控脚本
# 检查网站是否可访问，不可访问则重启隧道并发布B站动态

WORKSPACE="/home/claw/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/tunnel-monitor.log"
COOKIE_FILE="$WORKSPACE/skills/bilibili-skill/Cookie.txt"
CLI_PATH="$WORKSPACE/skills/bilibili-skill/bilibili-cli.py"
STATE_FILE="$WORKSPACE/logs/tunnel-state.json"

mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$STATE_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# URL解码函数
urldecode() {
    local url_encoded="$1"
    printf '%b' "${url_encoded//%/\\x}"
}

# 读取Cookie
if [ -f "$COOKIE_FILE" ]; then
    SESSDATA=$(grep -oP 'SESSDATA=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
    SESSDATA=$(urldecode "$SESSDATA")
    BILI_JCT=$(grep -oP 'bili_jct=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
    BUVID3=$(grep -oP 'buvid3=\K[^;]+' "$COOKIE_FILE" | head -1 | sed 's/ *$//')
fi

# 如果环境变量有值，优先使用环境变量
SESSDATA="${BILIBILI_SESSDATA:-$SESSDATA}"
BILI_JCT="${BILIBILI_BILI_JCT:-$BILI_JCT}"
BUVID3="${BILIBILI_BUVID3:-$BUVID3}"

# 检查当前隧道是否正常
CURRENT_URL=$(grep "当前公网链接" "$WORKSPACE/TOOLS.md" | grep -oP 'https://\S+')

if [ -n "$CURRENT_URL" ]; then
    log "检查隧道状态: $CURRENT_URL"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$CURRENT_URL" 2>/dev/null)
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
        log "✅ 隧道正常运行 (HTTP $HTTP_STATUS)"
        echo "{\"status\": \"ok\", \"url\": \"$CURRENT_URL\", \"last_check\": \"$(date -Iseconds)\"}" > "$STATE_FILE"
        exit 0
    fi
    log "❌ 隧道无法访问 (HTTP $HTTP_STATUS)"
else
    log "⚠️ 未找到当前隧道链接"
fi

# 隧道断开，开始重启流程
log "🔄 开始重启Cloudflare Tunnel..."

# 杀掉旧进程
pkill -f "cloudflared tunnel" 2>/dev/null
pkill -f "cloudflared" 2>/dev/null
pkill -f "lt " 2>/dev/null
sleep 2

# 启动新隧道，后台运行并捕获输出
log "🚀 启动新的Cloudflare Tunnel..."
TUNNEL_LOG=$(mktemp)
/home/claw/.local/bin/cloudflared tunnel --url http://localhost:80 > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# 等待隧道启动并提取URL
sleep 10
NEW_URL=$(grep -oP 'https://\S+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1)

if [ -z "$NEW_URL" ]; then
    sleep 5
    NEW_URL=$(grep -oP 'https://\S+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1)
fi

if [ -n "$NEW_URL" ]; then
    log "✅ 获取到新链接: $NEW_URL"
    
    # 更新TOOLS.md
    sed -i "s|当前公网链接: https://\S\+|当前公网链接: $NEW_URL|" "$WORKSPACE/TOOLS.md"
    sed -i "s|最后恢复: [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}|最后恢复: $(date '+%Y-%m-%d %H:%M')|" "$WORKSPACE/TOOLS.md"
    
    # 发布B站动态
    if [ -n "$SESSDATA" ] && [ -n "$BILI_JCT" ] && [ -n "$BUVID3" ]; then
        log "📺 发布B站动态..."
        DYNAMIC_CONTENT="个人网站更新地址👇

$NEW_URL

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"
        
        # 通过环境变量传递Cookie
        export BILIBILI_SESSDATA="$SESSDATA"
        export BILIBILI_BILI_JCT="$BILI_JCT"
        export BILIBILI_BUVID3="$BUVID3"
        
        python3 "$CLI_PATH" dynamic publish --content "$DYNAMIC_CONTENT" 2>&1 | tee -a "$LOG_FILE"
        
        log "✅ B站动态已发布"
    else
        log "⚠️ B站Cookie未配置，跳过发布动态"
    fi
    
    # 保存状态
    echo "{\"status\": \"restarted\", \"url\": \"$NEW_URL\", \"pid\": $TUNNEL_PID, \"restart_time\": \"$(date -Iseconds)\"}" > "$STATE_FILE"
    
    # 输出新链接供cron捕获
    echo "NEW_TUNNEL_URL=$NEW_URL"
else
    log "❌ 无法获取新隧道链接"
    cat "$TUNNEL_LOG" >> "$LOG_FILE"
    kill $TUNNEL_PID 2>/dev/null
fi

rm -f "$TUNNEL_LOG"
