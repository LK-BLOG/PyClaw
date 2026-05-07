#!/bin/bash
# 隧道监控脚本 - 检查网站可用性，自动重连并发布B站动态

WORKSPACE="/home/claw/.openclaw/workspace"
TOOLS_FILE="$WORKSPACE/TOOLS.md"
CURRENT_URL=$(grep "当前公网链接" "$TOOLS_FILE" | sed 's/.*: //')

# 检查网站是否可访问（200=正常，503/530=失败）
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CURRENT_URL" --connect-timeout 10 --max-time 15 2>/dev/null)

if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ] || [ "$STATUS" = "302" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 隧道正常: $CURRENT_URL (HTTP $STATUS)"
    exit 0
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 隧道断开，开始恢复..."

# 杀掉旧进程
pkill -9 -f cloudflared 2>/dev/null
pkill -9 -f "lt " 2>/dev/null
sleep 2

# 启动新隧道
rm -f /tmp/cf.log
nohup cloudflared tunnel --url http://localhost:80 > /tmp/cf.log 2>&1 &
sleep 10

# 获取新链接
NEW_URL=$(grep -o "https://[^ ]*trycloudflare.com" /tmp/cf.log | head -1)

if [ -z "$NEW_URL" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 获取新链接失败"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 新链接: $NEW_URL"

# 更新TOOLS.md
sed -i "s|当前公网链接: https://.*trycloudflare.com|当前公网链接: $NEW_URL|" "$TOOLS_FILE"
sed -i "s|最后更新: .*|最后更新: $(date '+%Y-%m-%d %H:%M')|" "$TOOLS_FILE"

# 发布B站动态
cd "$WORKSPACE/skills/bilibili-skill"
bash bilibili-wrapper.sh dynamic publish --content "个人网站更新地址👇
$NEW_URL
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 完成恢复"
