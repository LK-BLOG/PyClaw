#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布B站日常风格动态"""
import os
import json
import requests
from urllib.parse import urlencode

# 隧道链接
TUNNEL_URL = "https://engine-signature-primary-quarter.trycloudflare.com"

# 日常风格的动态内容
CONTENT = f"""✨ 自动发布测试
网站地址：{TUNNEL_URL}

这是一条通过cloudflared tunnel自动发布的B站动态~
隧道运行正常，网站可以正常访问啦！

#自动发布 #隧道监控 #日常记录
"""

def get_cookies():
    """从环境变量获取cookies"""
    sessdata = os.environ.get('BILIBILI_SESSDATA', '')
    bili_jct = os.environ.get('BILIBILI_BILI_JCT', '')
    buvid3 = os.environ.get('BILIBILI_BUVID3', '')
    
    if not all([sessdata, bili_jct, buvid3]):
        print("❌ 缺少Cookie环境变量")
        return None
    
    return {
        'SESSDATA': sessdata,
        'bili_jct': bili_jct,
        'buvid3': buvid3
    }

def publish_dynamic():
    """发布动态"""
    cookies = get_cookies()
    if not cookies:
        return False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://t.bilibili.com/',
        'Origin': 'https://t.bilibili.com'
    }
    
    url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
    
    # 构建动态数据
    content_obj = {
        "content": CONTENT
    }
    
    data = {
        "type": 4,  # 文字动态
        "content": json.dumps(content_obj, ensure_ascii=False),
        "csrf": cookies['bili_jct'],
        "from": "create.dynamic.web"
    }
    
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data, timeout=10)
        result = response.json()
        
        if result.get('code') == 0:
            dyn_id = result['data']['dyn_id']
            print(f"✅ 动态发布成功！")
            print(f"动态ID: {dyn_id}")
            print(f"动态链接: https://t.bilibili.com/{dyn_id}")
            print(f"\n内容:\n{CONTENT}")
            return True
        else:
            print(f"❌ 发布失败: {result.get('message', '未知错误')}")
            print(f"错误码: {result.get('code')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

if __name__ == "__main__":
    publish_dynamic()
