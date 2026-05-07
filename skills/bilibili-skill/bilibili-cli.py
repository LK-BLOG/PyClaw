#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易B站动态发布脚本
基于bilibili-api-python
"""

import os
import sys
import argparse
from bilibili_api import Credential, dynamic, sync

def get_credential():
    """从Cookie.txt文件或环境变量获取凭证"""
    # 优先从Cookie.txt读取
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_file = os.path.join(script_dir, "Cookie.txt")
    sessdata = ""
    bili_jct = ""
    buvid3 = os.environ.get("BILIBILI_BUVID3", "971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc")
    
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r') as f:
            cookie_content = f.read().strip()
            for item in cookie_content.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    if key == 'SESSDATA':
                        sessdata = value
                    elif key == 'bili_jct':
                        bili_jct = value
                    elif key == 'buvid3':
                        buvid3 = value
    
    # 环境变量覆盖
    if os.environ.get("BILIBILI_SESSDATA", ""):
        sessdata = os.environ.get("BILIBILI_SESSDATA", "")
    if os.environ.get("BILIBILI_BILI_JCT", ""):
        bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
    if os.environ.get("BILIBILI_BUVID3", ""):
        buvid3 = os.environ.get("BILIBILI_BUVID3", buvid3)
    
    if not all([sessdata, bili_jct]):
        print("错误：未找到完整的Cookie信息", file=sys.stderr)
        sys.exit(1)
    
    return Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

import asyncio
from bilibili_api.dynamic import BuildDynamic

async def publish_dynamic_async(content: str, cred):
    """发布文字异步函数"""
    # 使用 BuildDynamic 创建纯文字动态
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    return result

def publish_dynamic(content: str):
    """发布文字动态"""
    cred = get_credential()
    result = asyncio.run(publish_dynamic_async(content, cred))
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"发布成功！动态ID: {result.get('data', {}).get('dyn_id', '未知')}")
    return True

def main():
    parser = argparse.ArgumentParser(description='B站动态发布工具')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # 发布动态
    publish_parser = subparsers.add_parser('dynamic', help='动态操作')
    publish_subparsers = publish_parser.add_subparsers(dest='action', required=True)
    
    # publish
    publish_publish = publish_subparsers.add_parser('publish', help='发布动态')
    publish_publish.add_argument('--content', '-c', required=True, help='动态内容')
    
    args = parser.parse_args()
    
    if args.command == 'dynamic' and args.action == 'publish':
        publish_dynamic(args.content)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
