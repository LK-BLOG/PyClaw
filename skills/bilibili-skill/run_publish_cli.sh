#!/bin/bash
cd "$(dirname "$0")"

tunnel_url="https://witch-sms-bicycle-use.trycloudflare.com"
current_time=$(date "+%Y-%m-%d %H:%M")

content="🌙 深夜小播报～

跟大家同步一下，我的小站隧道还在稳定运行中！
👉 https://witch-sms-bicycle-use.trycloudflare.com

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么调皮～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用手动折腾啦！
科技改变摸鱼生活 ✌️

发布时间：$current_time

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"

echo "准备发布动态..."
echo "隧道链接: $tunnel_url"
echo "发布时间: $current_time"

./bilibili-wrapper.sh dynamic publish --content "$content"
