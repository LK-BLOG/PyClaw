#!/usr/bin/env python3
"""Publish Bilibili dynamic using direct HTTP request"""

import json
import sys
import requests

# Current tunnel URL
TUNNEL_URL = "https://thing-mistress-kingston-legitimate.trycloudflare.com"

# Read cookies from Cookie.txt
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
cookies = {}

with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

print(f"Cookies loaded: {list(cookies.keys())}")
print(f"SESSDATA: {cookies.get('SESSDATA', '')[:20]}...")
print(f"bili_jct: {cookies.get('bili_jct', '')[:10]}...\n")

# Build content
content = f"""个人网站更新地址👇

{TUNNEL_URL}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

(自动发布)"""

print("发布内容:")
print(content)
print()

# Build request
url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://t.bilibili.com/",
    "Origin": "https://t.bilibili.com",
    "Content-Type": "application/json",
}

# Build dynamic data - simple text dynamic
dyn_data = {
    "type": 4,  # Text dynamic
    "rid": 0,
    "content": content,
    "extension": '{"emoji_type":1}',
    "at_uids": "",
    "ctrl": [],
}

data = {
    "dyn_req": {
        "content": {
            "contents": [
                {
                    "type": 1,
                    "text": content
                }
            ]
        },
        "scene": 2,
    }
}

csrf = cookies.get("bili_jct", "")

params = {
    "csrf": csrf,
}

print("正在发布动态...")
try:
    response = requests.post(
        url,
        headers=headers,
        cookies=cookies,
        json=data,
        params=params,
        timeout=30,
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == 0:
        print("\n✅ 发布成功！")
        dyn_id = result.get("data", {}).get("dyn_id_str")
        if dyn_id:
            print(f"动态链接: https://t.bilibili.com/{dyn_id}")
        sys.exit(0)
    else:
        print(f"\n❌ 发布失败: {result.get('message', '未知错误')}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ 请求失败: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
