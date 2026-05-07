#!/usr/bin/env python3
"""Simple Bilibili dynamic publisher"""

import asyncio
import json
import sys
from bilibili_api import Credential, dynamic

# Current tunnel URL
TUNNEL_URL = "https://thing-mistress-kingston-legitimate.trycloudflare.com"

# Read cookies
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
sessdata = ""
bili_jct = ""
buvid3 = "BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('SESSDATA='):
            sessdata = line.split('=', 1)[1]
        elif line.startswith('bili_jct='):
            bili_jct = line.split('=', 1)[1]

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def publish():
    content = f"""个人网站更新地址👇

{TUNNEL_URL}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

(自动发布)"""

    print("正在发布动态...")
    print(f"内容:\n{content}\n")
    
    try:
        builder = dynamic.BuildDynamic()
        builder.add_text(content)
        result = await dynamic.send_dynamic(builder, cred)
        print("发布成功!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"发布失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(publish())
    sys.exit(0 if success else 1)
