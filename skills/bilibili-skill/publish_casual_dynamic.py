#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            cookies[key] = value

# 当前Cloudflare tunnel链接 - 从TOOLS.md获取
tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"

content = f"""🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
BILI_JCT = cookies.get('bili_jct', '')

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print()
print("="*50)
print("动态内容:")
print(content)
print("="*50)
print()

# 尝试直接用requests发布
def publish_direct():
    try:
        url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Referer": "https://t.bilibili.com/",
            "Origin": "https://t.bilibili.com"
        }
        data = {
            "type": 4,
            "content": content,
            "csrf": BILI_JCT,
            "from": "create.dynamic.web"
        }
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        print(f"API响应: {result}")
        if result.get('code') == 0:
            print("\n✅ 动态发布成功！")
            dynamic_id = result.get('data', {}).get('dyn_id', '未知')
            print(f"动态ID: {dynamic_id}")
            return True
        else:
            print(f"\n❌ 发布失败: {result.get('message', '未知错误')}")
            return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    publish_direct()
