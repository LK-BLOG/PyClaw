#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
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

# 设置环境变量
os.environ["BILIBILI_SESSDATA"] = cookies.get('SESSDATA', '')
os.environ["BILIBILI_BILI_JCT"] = cookies.get('bili_jct', '')
os.environ["BILIBILI_BUVID3"] = cookies.get('buvid3', '')

# 当前Cloudflare tunnel链接 - 最新链接
tunnel_url = "https://witch-sms-bicycle-use.trycloudflare.com"
current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

content = """🌙 深夜小播报～

跟大家同步一下，我的小站隧道还在稳定运行中！
👉 https://witch-sms-bicycle-use.trycloudflare.com

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare免费隧道就是这么调皮～
欢迎来我的个人主页逛逛，留言板随时恭候大驾！

🤖 本条动态由OpenClaw机器人自动发布
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用手动折腾啦！
科技改变摸鱼生活 ✌️

发布时间：""" + current_time + """

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"""

print("准备发布动态...")
print(f"隧道链接: {tunnel_url}")
print(f"发布时间: {current_time}")
print(f"内容长度: {len(content)}")

# 导入bilibili-cli的发布函数
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("bilibili_cli", os.path.join(os.path.dirname(__file__), "bilibili-cli.py"))
bilibili_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bilibili_cli)
get_credential = bilibili_cli.get_credential
publish_dynamic_async = bilibili_cli.publish_dynamic_async
import asyncio

try:
    cred = get_credential()
    result = asyncio.run(publish_dynamic_async(content, cred))
    import json
    print(f"API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    if result.get('code') == 0:
        print("\n✅ 动态发布成功！")
        dynamic_id = result.get('data', {}).get('dyn_id', '未知')
        print(f"动态ID: {dynamic_id}")
        print(f"动态链接: https://t.bilibili.com/{dynamic_id}")
    else:
        print(f"\n❌ 发布失败: {result.get('message', '未知错误')}")
except Exception as e:
    print(f"发生错误: {e}")
    import traceback
    traceback.print_exc()
