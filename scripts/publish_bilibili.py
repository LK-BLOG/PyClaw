#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布B站动态脚本"""

import os
import sys
import re
from urllib.parse import unquote

# 读取Cookie文件
cookie_path = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
with open(cookie_path, 'r', encoding='utf-8') as f:
    cookie_content = f.read()

# 提取Cookie值
sessdata_match = re.search(r'SESSDATA=([^;]+)', cookie_content)
bili_jct_match = re.search(r'bili_jct=([^;]+)', cookie_content)
buvid3_match = re.search(r'buvid3=([^;]+)', cookie_content)

if not all([sessdata_match, bili_jct_match, buvid3_match]):
    print("错误：无法从Cookie文件提取完整信息", file=sys.stderr)
    sys.exit(1)

# URL解码并设置环境变量
os.environ['BILIBILI_SESSDATA'] = unquote(sessdata_match.group(1).strip())
os.environ['BILIBILI_BILI_JCT'] = bili_jct_match.group(1).strip()
os.environ['BILIBILI_BUVID3'] = buvid3_match.group(1).strip()

print("Cookie已加载")

# 读取当前隧道链接
tools_path = "/home/claw/.openclaw/workspace/TOOLS.md"
with open(tools_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取当前公网链接
match = re.search(r'当前公网链接: (https://\S+)', content)
if not match:
    print("错误：未找到当前公网链接", file=sys.stderr)
    sys.exit(1)

current_url = match.group(1)
print(f"当前隧道链接: {current_url}")

# 准备动态内容
dynamic_content = f"""个人网站更新地址👇

{current_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️
(定时自动发布)"""

print("动态内容:")
print(dynamic_content)

# 设置工作目录
os.chdir("/home/claw/.openclaw/workspace")
sys.path.insert(0, "/home/claw/.openclaw/workspace/skills/bilibili-skill")

# 导入并执行发布
import subprocess
result = subprocess.run([
    "python3", 
    "skills/bilibili-skill/bilibili-cli.py", 
    "dynamic", 
    "publish", 
    "--content", 
    dynamic_content
], capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
