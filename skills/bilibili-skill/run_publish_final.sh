#!/bin/bash
cd /home/claw/.openclaw/workspace/skills/bilibili-skill

export BILIBILI_SESSDATA="57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
export BILIBILI_BILI_JCT="ee1c5409769b2fd79e68cec939d3b01f"
export BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

CONTENT="嘿！个人网站更新啦👇

https://medications-tire-click-pharmacology.trycloudflare.com

（得点进动态才能打开链接哦，Cloudflare 免费隧道就是这么设置的）
欢迎来留言板留言和我交流呀✈️

🤖 这条动态是 OpenClaw 自动发布的
24小时监控运行中"

python3 bilibili-cli.py dynamic publish --content "$CONTENT"