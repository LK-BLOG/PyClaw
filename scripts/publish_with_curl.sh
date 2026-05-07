#!/bin/bash
# 使用curl直接调用B站API发布动态

COOKIE_FILE="/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
COOKIE=$(cat "$COOKIE_FILE")

# CSRF Token (bili_jct)
BILI_JCT=$(echo "$COOKIE" | grep -o 'bili_jct=[^;]*' | cut -d'=' -f2)

# 动态内容
CONTENT="个人网站更新地址👇
https://warrant-independence-bacon-attempt.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"

echo "使用curl发布动态..."
echo "CSRF Token: $BILI_JCT"

# 调用动态发布API
# 使用正确的API端点
RESULT=$(curl -s -X POST "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Cookie: $COOKIE" \
  -H "Referer: https://t.bilibili.com/" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  --data-urlencode "csrf=$BILI_JCT" \
  --data-urlencode "content=$CONTENT" \
  --data-urlencode "type=4" \
  --connect-timeout 15 \
  --max-time 30)

echo "API响应:"
echo "$RESULT"

# 检查结果
if echo "$RESULT" | grep -q '"code":0'; then
    echo ""
    echo "✅ 动态发布成功！"
    DYN_ID=$(echo "$RESULT" | grep -o '"dyn_id":[0-9]*' | cut -d':' -f2)
    echo "动态ID: $DYN_ID"
    echo "动态链接: https://t.bilibili.com/$DYN_ID"
    exit 0
else
    echo ""
    echo "❌ 发布失败"
    echo "$RESULT" | grep -o '"message":"[^"]*"'
    exit 1
fi
