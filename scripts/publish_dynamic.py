#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')
import bilibili_cli

# 获取认证信息
sessdata = os.environ.get('BILIBILI_SESSDATA', '')
bili_jct = os.environ.get('BILIBILI_BILI_JCT', '')
buvid3 = os.environ.get('BILIBILI_BUVID3', '')

new_url = "https://architects-contents-may-lifetime.trycloudflare.com"

content = f"""个人网站更新地址👇

{new_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

print(f"准备发布动态，URL: {new_url}")
print(f"SESSDATA: {sessdata[:20]}...")
print(f"BILI_JCT: {bili_jct[:10]}...")

# 调用bilibili_cli的发布功能
try:
    from bilibili_api import dynamic, Credential
    
    cred = Credential(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3
    )
    
    result = dynamic.send_dynamic(cred, content)
    print(f"发布成功: {result}")
except Exception as e:
    print(f"发布失败: {e}")
    import traceback
    traceback.print_exc()
