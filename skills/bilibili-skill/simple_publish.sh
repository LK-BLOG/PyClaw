#!/bin/bash
# 简单的B站动态发布脚本，使用curl

cd "$(dirname "$0")"

# 读取Cookie
COOKIE_CONTENT=$(cat Cookie.txt)

# URL解码SESSDATA
SESSDATA=$(echo "$COOKIE_CONTENT" | grep -oP 'SESSDATA=\K[^;]+' | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read().strip()))")
BILI_JCT=$(echo "$COOKIE_CONTENT" | grep -oP 'bili_jct=\K[^;]+')

TUNNEL_URL="https://warrant-independence-bacon-attempt.trycloudflare.com"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M")

CONTENT="🌙 晚间签到～

跟大家同步一下，我的个人网站隧道还在稳定运行！
👉 ${TUNNEL_URL}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么设置的～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知！
科技改变摸鱼生活 ✌️

发布时间：${CURRENT_TIME}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"

echo "准备发布动态..."
echo "隧道链接: $TUNNEL_URL"
echo "内容长度: ${#CONTENT}"
echo

# 使用curl发布动态
RESULT=$(curl -s -X POST "https://api.bilibili.com/x/dynamic/feed/create/dyn" \
  -H "Cookie: $COOKIE_CONTENT" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Referer: https://t.bilibili.com/" \
  -H "Origin: https://t.bilibili.com" \
  -d "type=4" \
  -d "content=$CONTENT" \
  -d "csrf=$BILI_JCT" \
  -d "from=create.dynamic.web" \
  --max-time 30)

echo "API响应:"
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

# 检查结果
CODE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('code', -1))" 2>/dev/null || echo "-1")

if [ "$CODE" = "0" ]; then
    DYN_ID=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('dyn_id', '未知'))" 2>/dev/null || echo "未知")
    echo
    echo "✅ 动态发布成功！"
    echo "动态ID: $DYN_ID"
    echo "动态链接: https://t.bilibili.com/$DYN_ID"
    echo "网站链接: $TUNNEL_URL"
    exit 0
else
    MESSAGE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', '未知错误'))" 2>/dev/null || echo "未知错误")
    echo
    echo "❌ 发布失败: $MESSAGE"
    exit 1
fi
