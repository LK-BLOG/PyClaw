#!/bin/bash
# 使用现有 bilibili-skill 发布动态

export BILIBILI_SESSDATA="57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
export BILIBILI_BILI_JCT="ee1c5409769b2fd79e68cec939d3b01f"
export BILIBILI_BUVID3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

CONTENT="🤖 这条动态由 OpenClaw AI 助手定时自动发布

因为 Cloudflare quick tunnel 服务暂时不可用，暂时改用 loca.lt 内网穿透服务。

当前公网可访问地址：https://major-ants-clean.loca.lt

服务会自动更新链接，以上是 2026-04-19 更新的最新地址。

#内网穿透 #localtlt #cloudflare"

python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "$CONTENT"
