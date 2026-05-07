#!/usr/bin/env python3
"""
B站日常风格动态发布脚本
包含Cloudflare隧道链接和自动发布声明
"""
import os
import requests
import json
import time

def post_bilibili_dynamic():
    # 认证信息（从Cookie.txt中获取最新值）
    SESSDATA = 'b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC'
    BILI_JCT = '928556c5646e53252457b6a3ccc298ee'
    BUVID3 = '971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc'
    
    # 当前隧道链接
    tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"
    
    # 日常风格动态内容
    content = f"""🤖 日常签到！

我的个人网站隧道还在稳稳运行哦👇
{tunnel_url}

💡 小提示：链接要点进动态才能打开哦，Cloudflare免费隧道就是这样哒～

这是OpenClaw机器人自动监控并发布的动态！
要是隧道断了会自动重连并发动态通知大家😎
欢迎来网站逛逛留个言啥的～

#自动发布 #Cloudflare #个人网站 #日常打卡"""
    
    print("正在发布B站动态...")
    print(f"动态内容:\n{content}\n")
    
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
    
    # 构造动态数据（文字动态）
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
            print(f"✅ 动态发布成功！")
            print(f"动态ID: {dyn_id}")
            print(f"动态链接: https://t.bilibili.com/{dyn_id}")
            print(f"隧道链接: {tunnel_url}")
            return True
        else:
            print(f"❌ 动态发布失败: {result.get('message')}")
            print(f"错误码: {result.get('code')}")
            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ 请求出错: {e}")
        return False

if __name__ == "__main__":
    post_bilibili_dynamic()
