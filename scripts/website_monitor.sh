#!/bin/bash
set -e

# 配置
WORKSPACE="/home/claw/.openclaw/workspace"
TOOLS_FILE="$WORKSPACE/TOOLS.md"
CURRENT_URL=$(grep "当前公网链接" "$TOOLS_FILE" | head -1 | sed 's/.*: //')
LOCAL_PORT=80

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 检查网站是否可访问
check_website() {
    local url="$1"
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$url" 2>/dev/null || echo "000")
    
    if [ "$status_code" = "200" ] || [ "$status_code" = "301" ] || [ "$status_code" = "302" ]; then
        return 0
    else
        log "网站无法访问，状态码: $status_code"
        return 1
    fi
}

# 杀掉旧隧道进程
kill_old_tunnels() {
    log "正在杀掉旧的 cloudflared 和 lt 进程..."
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    pkill -f "lt --port" 2>/dev/null || true
    pkill -x "cloudflared" 2>/dev/null || true
    pkill -x "lt" 2>/dev/null || true
    sleep 2
    
    # 强制杀掉
    pkill -9 -f "cloudflared tunnel" 2>/dev/null || true
    pkill -9 -x "cloudflared" 2>/dev/null || true
    log "旧进程已清理"
}

# 启动Cloudflare快速隧道并获取URL
start_cloudflare_tunnel() {
    log "正在启动 Cloudflare Quick Tunnel..."
    
    # 创建临时文件存储输出
    local TUNNEL_LOG=$(mktemp)
    
    # 后台启动隧道
    nohup cloudflared tunnel --url http://localhost:$LOCAL_PORT > "$TUNNEL_LOG" 2>&1 &
    local TUNNEL_PID=$!
    
    log "隧道进程已启动，PID: $TUNNEL_PID"
    
    # 等待并提取URL
    for i in {1..30}; do
        if grep -q "https://.*trycloudflare.com" "$TUNNEL_LOG"; then
            local NEW_URL=$(grep -o "https://.*trycloudflare.com" "$TUNNEL_LOG" | head -1)
            log "成功获取新公网链接: $NEW_URL"
            
            # 保存PID以便管理
            echo "$TUNNEL_PID" > /tmp/cloudflared_monitor.pid
            
            # 清理临时文件
            rm -f "$TUNNEL_LOG"
            
            echo "$NEW_URL"
            return 0
        fi
        sleep 1
    done
    
    # 失败了，杀掉进程
    kill $TUNNEL_PID 2>/dev/null || true
    rm -f "$TUNNEL_LOG"
    log "无法获取隧道链接，启动失败"
    return 1
}

# 更新TOOLS.md
update_tools_file() {
    local new_url="$1"
    log "正在更新 TOOLS.md..."
    
    # 使用awk替换旧链接和状态，避免sed的特殊字符问题
    awk -v new_url="$new_url" -v update_time="$(date '+%Y-%m-%d %H:%M')" '
    /当前公网链接:/ { print "- 当前公网链接: " new_url; next }
    /最后更新:/ { print "- 最后更新: " update_time; next }
    /状态:/ { print "- 状态: ✅ 正常运行"; next }
    1
    ' "$TOOLS_FILE" > "${TOOLS_FILE}.tmp" && mv "${TOOLS_FILE}.tmp" "$TOOLS_FILE"
    
    log "TOOLS.md 已更新"
}

# 发布Bilibili动态
publish_bilibili_dynamic() {
    local new_url="$1"
    log "正在发布 Bilibili 动态..."
    
    # 加载环境变量
    export BILIBILI_SESSDATA=$(grep "SESSDATA" "$TOOLS_FILE" | sed 's/.*: //' | sed 's/\${//' | sed 's/}//')
    export BILIBILI_BILI_JCT=$(grep "bili_jct" "$TOOLS_FILE" | sed 's/.*: //' | sed 's/\${//' | sed 's/}//')
    export BILIBILI_BUVID3=$(grep "buvid3" "$TOOLS_FILE" | sed 's/.*: //' | sed 's/\${//' | sed 's/}//')
    
    # 如果环境变量中有值，直接使用环境变量（真实值会被注入）
    [ -z "$BILIBILI_SESSDATA" ] && BILIBILI_SESSDATA="${BILIBILI_SESSDATA}"
    [ -z "$BILIBILI_BILI_JCT" ] && BILIBILI_BILI_JCT="${BILIBILI_BILI_JCT}"
    [ -z "$BILIBILI_BUVID3" ] && BILIBILI_BUVID3="${BILIBILI_BUVID3}"
    
    local CONTENT="个人网站更新地址👇

$new_url

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

    cd "$WORKSPACE/skills/bilibili-skill"
    python3 bilibili-cli.py \
        --sessdata "$BILIBILI_SESSDATA" \
        --bili_jct "$BILIBILI_BILI_JCT" \
        --buvid3 "$BILIBILI_BUVID3" \
        dynamic publish --content "$CONTENT"
    
    log "Bilibili 动态已发布"
}

# ========== 主流程 ==========

log "=== 开始网站监控检查 ==="
log "当前配置的链接: $CURRENT_URL"

# 检查网站是否正常
if check_website "$CURRENT_URL"; then
    log "网站访问正常，无需操作"
    exit 0
fi

log "网站无法访问，开始恢复流程..."

# 1. 杀掉旧进程
kill_old_tunnels

# 2. 启动新隧道
NEW_URL=$(start_cloudflare_tunnel)
if [ -z "$NEW_URL" ]; then
    log "隧道启动失败，退出"
    exit 1
fi

# 3. 更新TOOLS.md
update_tools_file "$NEW_URL"

# 4. 发布Bilibili动态
publish_bilibili_dynamic "$NEW_URL"

log "=== 恢复完成 ==="
log "新公网链接: $NEW_URL"

# 输出结果供cron任务捕获
echo "NEW_URL=$NEW_URL"
