#!/bin/bash
# 网站监控和自动恢复脚本
# 当网站无法访问时，重新建立Cloudflare隧道并发布B站动态

set -e

# 配置
CURRENT_URL_FILE="/home/claw/.openclaw/workspace/.current-tunnel-url"
COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
BILIBILI_CLI="/home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py"
LOG_FILE="/home/claw/.openclaw/workspace/logs/tunnel-monitor.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$CURRENT_URL_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 读取当前保存的URL
if [ -f "$CURRENT_URL_FILE" ]; then
    CURRENT_URL=$(cat "$CURRENT_URL_FILE")
else
    CURRENT_URL="https://blank-nec-part-talk.trycloudflare.com"
fi

log "开始监控网站: $CURRENT_URL"

# 检查网站是否可访问
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$CURRENT_URL" 2>/dev/null || echo "000")

log "HTTP状态码: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "403" ] || [ "$HTTP_STATUS" = "404" ]; then
    log "网站正常运行，无需操作"
    exit 0
fi

log "网站无法访问！开始恢复流程..."

# 1. 杀掉旧的cloudflared和lt进程
log "杀掉旧的隧道进程..."
pkill -f cloudflared 2>/dev/null || true
pkill -f "lt-" 2>/dev/null || true
sleep 2

# 确保所有进程都被杀掉
pkill -9 -f cloudflared 2>/dev/null || true

# 2. 启动新的Cloudflare quick tunnel
log "启动新的Cloudflare隧道..."

# 后台运行cloudflared并捕获输出
TUNNEL_OUTPUT=$(mktemp)
cloudflared tunnel --url http://localhost:80 > "$TUNNEL_OUTPUT" 2>&1 &
CLOUDFLARED_PID=$!

# 等待隧道启动并获取URL
sleep 15
NEW_URL=""
for i in {1..20}; do
    NEW_URL=$(grep -o 'https://[^ ]*trycloudflare.com' "$TUNNEL_OUTPUT" | head -1)
    if [ -n "$NEW_URL" ]; then
        break
    fi
    sleep 2
done

if [ -z "$NEW_URL" ]; then
    log "无法获取新的隧道URL！"
    kill $CLOUDFLARED_PID 2>/dev/null || true
    rm -f "$TUNNEL_OUTPUT"
    exit 1
fi

log "获取到新的公网链接: $NEW_URL"

# 保存新URL
echo "$NEW_URL" > "$CURRENT_URL_FILE"

# 更新TOOLS.md中的链接
sed -i "s|当前公网链接:.*|当前公网链接: $NEW_URL|" /home/claw/.openclaw/workspace/TOOLS.md

# 3. 通过bilibili发布动态
log "准备发布B站动态..."

# 读取Cookie
source "$COOKIE_FILE" 2>/dev/null || true

# 动态内容
DYNAMIC_CONTENT="个人网站更新地址👇
$NEW_URL
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

# 发布动态
log "发布动态内容: $DYNAMIC_CONTENT"

# 使用publish_dynamic_now.py发布
cd /home/claw/.openclaw/workspace/skills/bilibili-skill
python3 publish_dynamic_now.py "$NEW_URL" 2>&1 | tee -a "$LOG_FILE"

log "恢复流程完成！新链接: $NEW_URL"
echo "NEW_TUNNEL_URL=$NEW_URL" >> "$LOG_FILE"

# 清理
rm -f "$TUNNEL_OUTPUT"
