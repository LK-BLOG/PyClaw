#!/bin/bash
cd /home/claw/.openclaw/workspace/skills/bilibili-skill

tunnel_url="https://witnesses-jerry-integral-generated.trycloudflare.com"

content="""嘿～晚上好呀 🌙

个人网站隧道正常运行中👇
${tunnel_url}

（小提示：链接要复制到浏览器或者点进动态详情页才能打开哦，Cloudflare免费隧道就是这么设置的😉）

网站弄了个简单的留言板，路过的朋友可以留个爪印打个卡唠唠嗑～

🤖 本条动态由OpenClaw定时任务自动发布
#技术日常 #CloudflareTunnel #自动发布"""

./bilibili-wrapper.sh dynamic publish --content "$content"
