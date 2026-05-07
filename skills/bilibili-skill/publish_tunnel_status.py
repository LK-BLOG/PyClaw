#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime

# 从 Cookie.txt 读取所有Cookie
cookie_file = os.path.join(os.path.dirname(__file__), "Cookie.txt")
cookies = {}
with open(cookie_file, 'r') as f:
    cookie_content = f.read().strip()
    for item in cookie_content.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value

# 当前Cloudflare tunnel链接 - 最新链接
tunnel_url = "https://witnesses-jerry-integral-generated.trycloudflare.com"
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = f"""🌐 日常小播报！

跟大家同步一下，我的小站隧道又稳定运行啦～
👉 {tunnel_url}

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare就是这么傲娇的哈哈哈～
欢迎来我的个人主页逛逛，留言板随时恭候！

🤖 悄悄说：这条动态是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用我手动操作啦！
科技改变摸鱼生活 ✌️

发布时间：{current_time}

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活
"""

# 构造完整的Cookie头
cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
BILI_JCT = cookies.get('bili_jct', '')

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print(f"发布时间: {current_time}")
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
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应: {result}")
        if result.get('code') == 0:
            print("\n✅ 动态发布成功！")
            dynamic_id = result.get('data', {}).get('dyn_id', '未知')
            print(f"动态ID: {dynamic_id}")
            print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
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
