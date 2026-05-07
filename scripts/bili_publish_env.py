#!/usr/bin/env python3
"""发布隧道更新动态到B站 - 使用环境变量"""
import os, sys, re, subprocess, json

NEW_URL = "https://slight-graphic-bat-estimation.trycloudflare.com"

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

os.environ["BILIBILI_SESSDATA"] = m_sess.group(1)
os.environ["BILIBILI_BILI_JCT"] = m_jct.group(1)
os.environ["BILIBILI_BUVID3"] = m_buvid.group(1) if m_buvid else "971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"

cli_path = "/home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py"
result = subprocess.run(
    ["python3", cli_path, "dynamic", "publish", "--content", content],
    capture_output=True, text=True,
    cwd="/home/claw/.openclaw/workspace/skills/bilibili-skill",
    env=os.environ
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
