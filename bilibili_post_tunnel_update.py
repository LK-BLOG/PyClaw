#!/usr/bin/env python3
"""
B站动态发布脚本 - 日常风格
"""
import os
import requests
import json

def post_bilibili_dynamic():
    # 从环境变量获取认证信息
    SESSDATA = os.environ.get('BILIBILI_SESSDATA', '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC')
    BILI_JCT = os.environ.get('BILIBILI_BILI_JCT', 'ee1c5409769b2fd79e68cec939d3b01f')
    BUVID3 = os.environ.get('BILIBILI_BUVID3', 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc')
    
    if not all([SESSDATA, BILI_JCT, BUVID3]):
        print("错误：缺少B站认证信息")
        return False
    
    # 隧道链接
    tunnel_url = "https://kit-published-comes-petersburg.trycloudflare.com"
    
    # 动态内容 - 日常风格
    content = f"""🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"""
    
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
            print(f"内容预览: {content[:100]}...")
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
