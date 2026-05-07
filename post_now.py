#!/usr/bin/env python3
import requests
import json

SESSDATA = "57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
BILI_JCT = "ee1c5409769b2fd79e68cec939d3b01f"
BUVID3 = "BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"

content = """🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 https://monday-stats-begun-philip.trycloudflare.com

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"""

url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

cookies = {
    'SESSDATA': SESSDATA,
    'bili_jct': BILI_JCT,
    'buvid3': BUVID3,
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://t.bilibili.com/',
    'Content-Type': 'application/json',
}

payload = {
    "dyn_req": {
        "content": {
            "contents": [
                {
                    "raw_text": content,
                    "type": 1,
                    "biz_id": "",
                    "size": None
                }
            ]
        },
        "scene": 4,
        "attach_card": None,
        "meta": {
            "app_meta": {
                "appid": 1,
                "mobi_app": "web",
                "version": "1.0.0"
            }
        }
    }
}

response = requests.post(url, cookies=cookies, headers=headers, json=payload)
result = response.json()

if result.get('code') == 0:
    print("✅ 动态发布成功！")
    print(f"动态ID: {result.get('data', {}).get('dyn_id')}")
else:
    print(f"❌ 动态发布失败: {result.get('message')}")
    print(f"错误码: {result.get('code')}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
