#!/usr/bin/env python3
import os
import subprocess

# 设置环境变量
os.environ["BILIBILI_SESSDATA"] = "57bca764,1791886883,90408*41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
os.environ["BILIBILI_BILI_JCT"] = "ee1c5409769b2fd79e68cec939d3b01f"
os.environ["BILIBILI_BUVID3"] = "E3562839_19D9B1A42A2"

content = """个人网站更新地址👇
https://sweet-jeans-smash.loca.lt
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

cmd = [
    "python3",
    "/home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py",
    "dynamic", "publish",
    "--content", content
]

result = subprocess.run(cmd)
print(f"Exit code: {result.returncode}")
