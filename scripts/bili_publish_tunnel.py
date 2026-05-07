#!/usr/bin/env python3
"""发布隧道更新动态到B站"""
import subprocess, re

NEW_URL = "https://kilometers-invite-package-regulated.trycloudflare.com"

content = f"""个人网站更新地址👇
{NEW_URL}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️（自动发布）"""

cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"

with open(cookie_file, 'r') as f:
    raw = f.read()

m_sess = re.search(r'SESSDATA=([^;]+)', raw)
m_jct = re.search(r'bili_jct=([^;]+)', raw)
m_buvid = re.search(r'buvid3=([^;]+)', raw)

sessdata = m_sess.group(1)
bili_jct = m_jct.group(1)
buvid3 = m_buvid.group(1) if m_buvid else "971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"

print(f"SESSDATA: {sessdata[:20]}...")
print(f"bili_jct: {bili_jct[:20]}...")
print(f"buvid3: {buvid3[:20]}...")

cmd = [
    "python3", "/home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py",
    "--sessdata", sessdata,
    "--bili_jct", bili_jct,
    "--buvid3", buvid3,
    "dynamic", "publish",
    "--content", content
]

import os
result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/claw/.openclaw/workspace/skills/bilibili-skill")
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
