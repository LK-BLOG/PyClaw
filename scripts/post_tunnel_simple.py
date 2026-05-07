#!/usr/bin/env python3
import os
import requests
import sys

def post_dynamic(tunnel_url):
    SESSDATA = os.environ.get('BILIBILI_SESSDATA', '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC')
    BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', 'ee1c5409769b2fd79e68cec939d3b01f')
    BUVID3 = os.environ.get('BILIBILI_BUVID3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')
    
    content = f"""个人网站更新地址👇
{tunnel_url}
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""
    
    url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
    
    cookies = {
        'SESSDATA': SESSDATA,
        'bili_jct': BILI_JCT,
        'buvid3': BUVID3,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://t.bilibili.com/',
        'Content-Type': 'application/json',
    }
    
    payload = {
        "dyn_req": {
            "content": {
                "contents": [{"raw_text": content, "type": 1, "biz_id": "", "size": None}]
            },
            "scene": 4,
            "attach_card": None,
            "meta": {"app_meta": {"appid": 1, "mobi_app": "web", "version": "1.0.0"}}
    }
    
    response = requests.post(url, cookies=cookies, headers=headers, json=payload)
    result = response.json()
    
    if result.get('code') == 0:
        print(f"SUCCESS:{result.get('data', {}).get('dyn_id')}")
        return True
    else:
        print(f"FAILED:{result.get('code')}:{result.get('message')}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        post_dynamic(sys.argv[1])
    else:
        print("Usage: python post_tunnel_simple.py <tunnel_url>")
