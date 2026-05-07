#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布B站动态 - 独立脚本
"""

import os
import sys
import json
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

def urldecode(url_encoded):
    """URL解码"""
    return bytes(url_encoded, "utf-8").decode("unicode_escape")

def get_credential_from_file(cookie_file):
    """从Cookie文件读取凭证"""
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_content = f.read().strip()
    
    # 解析Cookie
    import re
    def get_cookie_value(key):
        match = re.search(rf'{key}=([^;]+)', cookie_content)
        if match:
            value = match.group(1).strip()
            # URL解码
            import urllib.parse
            return urllib.parse.unquote(value)
        return ""
    
    sessdata = get_cookie_value('SESSDATA')
    bili_jct = get_cookie_value('bili_jct')
    buvid3 = get_cookie_value('buvid3')
    
    if not all([sessdata, bili_jct]):
        print(f"错误：Cookie信息不完整", file=sys.stderr)
        print(f"SESSDATA: {'✓' if sessdata else '✗'}", file=sys.stderr)
        print(f"bili_jct: {'✓' if bili_jct else '✗'}", file=sys.stderr)
        sys.exit(1)
    
    return Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def publish_dynamic_async(content: str, cred):
    """发布文字动态"""
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    return result

def main():
    if len(sys.argv) < 2:
        print("用法: python publish_bilibili_dynamic.py <内容>")
        sys.exit(1)
    
    content = sys.argv[1]
    cookie_file = os.path.expanduser("~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt")
    
    print("正在获取凭证...")
    cred = get_credential_from_file(cookie_file)
    
    print("正在发布动态...")
    try:
        result = asyncio.run(publish_dynamic_async(content, cred))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        dyn_id = result.get('data', {}).get('dyn_id', '未知')
        print(f"\n✅ 发布成功！")
        print(f"动态ID: {dyn_id}")
        print(f"动态链接: https://t.bilibili.com/{dyn_id}")
        
    except Exception as e:
        print(f"❌ 发布失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
