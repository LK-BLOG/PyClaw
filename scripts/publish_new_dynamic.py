#!/usr/bin/env python3
import subprocess
import os

script_dir = "/home/claw/.openclaw/workspace/skills/bilibili-skill"
cookie_file = os.path.join(script_dir, "Cookie.txt")

# Read cookies
with open(cookie_file, 'r') as f:
    for line in f:
        line = line.strip()
        if 'SESSDATA=' in line:
            os.environ["BILIBILI_SESSDATA"] = line.split('=', 1)[1]
        elif 'bili_jct=' in line:
            os.environ["BILIBILI_BILI_JCT"] = line.split('=', 1)[1]
        elif 'buvid3=' in line:
            os.environ["BILIBILI_BUVID3"] = line.split('=', 1)[1]

content = """个人网站更新地址👇
https://preceding-inbox-tucson-only.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

cmd = [
    "python3", "bilibili-cli.py",
    "dynamic", "publish",
    "--content", content
]

result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
