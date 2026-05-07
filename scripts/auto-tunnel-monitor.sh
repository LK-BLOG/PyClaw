#!/bin/bash
# 自动监控Cloudflare隧道，断开时自动重连并发布Bilibili动态

set -e

WORKSPACE="/home/claw/.openclaw/workspace"
TOOLS_FILE="$WORKSPACE/TOOLS.md"
COOKIE_FILE="$WORKSPACE/skills/bilibili-skill/Cookie.txt"
BILIBILI_CLI="$WORKSPACE/skills/bilibili-skill/bilibili-cli.py"
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/tunnel-monitor.log"
TUNNEL_OUTPUT="$LOG_DIR/tunnel-output.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 开始隧道监控检查 ==="

# 从TOOLS.md读取当前链接
CURRENT_URL=$(grep -oP '当前公网链接: \K[^ ]+' "$TOOLS_FILE" 2>/dev/null)

if [ -z "$CURRENT_URL" ]; then
    log "警告: 无法从TOOLS.md读取当前链接，使用默认值"
    CURRENT_URL="https://dude-bridges-framed-living.trycloudflare.com"
fi

log "当前配置链接: $CURRENT_URL"

# 检查网站是否可访问（重试2次）
HTTP_STATUS="failed"
for i in 1 2; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 8 --max-time 15 "$CURRENT_URL" 2>/dev/null || echo "failed")
    if [ "$HTTP_STATUS" != "failed" ] && [ "$HTTP_STATUS" != "000" ]; then
        break
    fi
    log "第 $i 次检查失败，重试..."
    sleep 3
done

# 检查是否成功
if [ "$HTTP_STATUS" != "failed" ] && [ "$HTTP_STATUS" != "000" ] && [ "$HTTP_STATUS" -ge 200 ] && [ "$HTTP_STATUS" -lt 500 ]; then
    log "✅ 网站正常运行 (HTTP $HTTP_STATUS)"
    # 更新TOOLS.md中的状态
    sed -i "s/最后检查: .*/最后检查: $(date '+%Y-%m-%d %H:%M')/" "$TOOLS_FILE"
    sed -i "s/状态: .*/状态: ✅ 正常运行 (HTTP $HTTP_STATUS)/" "$TOOLS_FILE"
    log "=== 监控检查完成，无需重连 ==="
    exit 0
fi

log "❌ 网站无法访问 (状态: $HTTP_STATUS)，开始自动重连流程..."

# ========== 1. 杀掉旧的隧道进程 ==========
log "步骤 1/4: 清理旧隧道进程..."
pkill -9 -f "cloudflared tunnel" 2>/dev/null || true
pkill -9 -f "cloudflared --url" 2>/dev/null || true
pkill -9 -f "lt --port" 2>/dev/null || true
sleep 2

# 确认杀掉
if pgrep -f "cloudflared" > /dev/null; then
    log "警告: 仍有cloudflared进程运行，强制清理..."
    killall -9 cloudflared 2>/dev/null || true
    sleep 1
fi

# ========== 2. 启动新的Cloudflare Tunnel ==========
log "步骤 2/4: 启动新的Cloudflare Quick Tunnel..."

# 清空输出文件
> "$TUNNEL_OUTPUT"

# 后台启动cloudflared
nohup cloudflared tunnel --url http://localhost:80 > "$TUNNEL_OUTPUT" 2>&1 &
TUNNEL_PID=$!
log "Cloudflared 已启动，PID: $TUNNEL_PID"

# 等待隧道启动并提取URL（最多等待30秒）
NEW_URL=""
for i in {1..15}; do
    sleep 2
    NEW_URL=$(grep -oP 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$TUNNEL_OUTPUT" | head -1)
    if [ -n "$NEW_URL" ]; then
        break
    fi
    log "等待隧道启动... ($i/15)"
done

if [ -z "$NEW_URL" ]; then
    log "❌ 错误: 无法获取新的Cloudflare隧道链接"
    log "隧道输出:"
    cat "$TUNNEL_OUTPUT" | tail -20 | tee -a "$LOG_FILE"
    exit 1
fi

log "✅ 获取到新的公网链接: $NEW_URL"

# 验证新链接是否可访问
sleep 3
VERIFY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$NEW_URL" 2>/dev/null || echo "failed")
log "新链接验证状态: $VERIFY_STATUS"

# ========== 3. 更新TOOLS.md ==========
log "步骤 3/4: 更新TOOLS.md配置..."
sed -i "s|当前公网链接: https://[^ ]*|当前公网链接: $NEW_URL|" "$TOOLS_FILE"
sed -i "s/最后检查: .*/最后检查: $(date '+%Y-%m-%d %H:%M')/" "$TOOLS_FILE"
sed -i "s/状态: .*/状态: ✅ 已自动重连 (HTTP $VERIFY_STATUS)/" "$TOOLS_FILE"

# ========== 4. 发布Bilibili动态 ==========
log "步骤 4/4: 发布Bilibili动态..."

# 从Cookie文件读取认证信息
BILIBILI_SESSDATA=$(grep SESSDATA "$COOKIE_FILE" | cut -d= -f2-)
BILIBILI_BILI_JCT=$(grep bili_jct "$COOKIE_FILE" | cut -d= -f2-)
BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

DYNAMIC_CONTENT="个人网站更新地址👇
$NEW_URL

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

log "动态内容准备就绪"

# 调用bilibili-cli发布
cd "$(dirname "$BILIBILI_CLI")"
PUBLISH_RESULT=$(python3 "$(basename "$BILIBILI_CLI")" \
    --sessdata "$BILIBILI_SESSDATA" \
    --bili_jct "$BILIBILI_BILI_JCT" \
    --buvid3 "$BILIBILI_BUVID3" \
    dynamic publish --content "$DYNAMIC_CONTENT" 2>&1)

echo "$PUBLISH_RESULT" | tee -a "$LOG_FILE"

# 提取动态ID
DYN_ID=$(echo "$PUBLISH_RESULT" | grep -oP 'dyn_id["'\'']:\s*["'\'']?\K[0-9]+' | head -1)
if [ -n "$DYN_ID" ]; then
    sed -i "s/最后动态发布: .*/最后动态发布: $(date '+%Y-%m-%d %H:%M') - 动态ID: $DYN_ID/" "$TOOLS_FILE"
    log "✅ 动态发布成功，ID: $DYN_ID"
else
    sed -i "s/最后动态发布: .*/最后动态发布: $(date '+%Y-%m-%d %H:%M') - 动态ID: 发布完成/" "$TOOLS_FILE"
    log "⚠️ 动态已发布，但无法提取ID"
fi

# ========== 完成 ==========
log "========================================"
log "✅ 自动重连全部完成！"
log "新链接: $NEW_URL"
log "隧道PID: $TUNNEL_PID"
log "========================================"

# 输出新链接供cron任务捕获
echo ""
echo "NEW_URL=$NEW_URL"
echo "TUNNEL_PID=$TUNNEL_PID"

exit 0
