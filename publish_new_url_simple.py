#!/usr/bin/env python3
"""直接调用 Bilibili API 发布动态"""

import requests
import json

# 使用脚本中的有效 cookies
SESSDATA = "57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
bili_jct = "ee1c5409769b2fd79e68cec939d3b01f"

content = """个人网站更新地址👇
https://ties-throw-journalists-discussions.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

🤖 自动发布 - 隧道断开后已自动重连
#自动发布 #CloudflareTunnel #技术笔记 #小爪日常"""

# Bilibili 发布动态 API
url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

headers = {
    "Cookie": f"SESSDATA={SESSDATA}; bili_jct={bili_jct}",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://t.bilibili.com/"
}

# 构造动态内容（文字动态）
data = {
    "type": 4,  # 文字动态
    "content": content,
    "csrf": bili_jct
}

try:
    response = requests.post(url, headers=headers, data=data, timeout=10)
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == 0:
        print("\n✅ 动态发布成功！")
    else:
        print(f"\n❌ 发布失败: {result.get('message')}")
        
except Exception as e:
    print(f"错误: {e}")
