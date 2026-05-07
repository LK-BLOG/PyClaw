#!/usr/bin/env python3
"""
B站动态发布脚本 - 隧道更新
"""
import os
import requests

def post_bilibili_dynamic():
    # 从环境变量获取认证信息
    SESSDATA = os.environ.get('BILIBILI_SESSDATA', '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC')
    BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', 'ee1c5409769b2fd79e68cec939d3b01f')
    BUVID3 = os.environ.get('BILIBILI_BUVID3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')
    
    # 新的隧道链接
    tunnel_url = "https://unnecessary-oaks-vbulletin-lone.trycloudflare.com"
    
    # 动态内容
    content = f"""个人网站更新地址👇
{tunnel_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)

#Cloudflare #个人网站 #自动发布"""
    
    # 构造请求
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
    
    try:
        response = requests.post(
            url,
            cookies=cookies,
            headers=headers,
            json=payload
        )
        
        result = response.json()
        
        if result.get('code') == 0:
            print("✅ 动态发布成功！")
            print(f"动态ID: {result.get('data', {}).get('dyn_id')}")
            print(f"新链接: {tunnel_url}")
            return True
        else:
            print(f"❌ 动态发布失败: {result.get('message')}")
            print(f"错误码: {result.get('code')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求出错: {e}")
        return False

if __name__ == "__main__":
    post_bilibili_dynamic()
