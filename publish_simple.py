#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')
exec(open('/home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py').read().split('if __name__')[0])

content = """个人网站更新地址👇

https://holds-tucson-intense-removable.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

publish_dynamic(content)
