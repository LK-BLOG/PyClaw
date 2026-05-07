#!/bin/bash
export BILIBILI_SESSDATA="57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
export BILIBILI_BILI_JCT="ee1c5409769b2fd79e68cec939d3b01f"
export BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

CONTENT="🤖 【自动发布】服务器状态更新 ✅

大家好！我的个人网站隧道已重新连接啦~ 🌐

🔗 访问地址：https://association-everyday-flights-believed.trycloudflare.com

这是通过 Cloudflare Tunnel 自动监控发布的动态，隧道每5分钟会自动检查一次，如果断开就会自动重连并通知大家~

服务器一直在线中，欢迎来玩！😉

#服务器状态 #自动发布 #Cloudflare #技术分享"

python3 bilibili-cli.py dynamic publish --content "$CONTENT"
