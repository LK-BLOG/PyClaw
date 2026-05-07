#!/usr/bin/env python3
"""
B站动态发布脚本 - 使用有效的Cookie
"""
import requests

def post_bilibili_dynamic():
    # 从Cookie.txt中提取的有效认证信息
    SESSDATA = "b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
    BILI_JCT = "928556c5646e53252457b6a3ccc298ee"
    BUVID3 = "971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"
    
    # 隧道链接
    tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"
    
    # 动态内容 - 日常风格（21:13版本）
    content = f"""🌐 晚间日常播报～

又是一个愉快的夜晚！我的Cloudflare小隧道依然在稳稳运行中～
个人网站地址在这里 👉 {tunnel_url}

💡 小提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么有个性～
欢迎来我的小站逛逛，留言板随时欢迎大家来踩踩！

🤖 对啦，这条动态又是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知，太省心啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活 #晚间播报"""
    
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
            dyn_id = result.get('data', {}).get('dyn_id')
            print("✅ 动态发布成功！")
            print(f"动态ID: {dyn_id}")
            print(f"动态链接: https://t.bilibili.com/{dyn_id}")
            print(f"隧道链接: {tunnel_url}")
            print("\n内容预览:")
            print(content)
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
