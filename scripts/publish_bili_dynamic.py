#!/usr/bin/env python3
"""Publish Bilibili dynamic - standalone script"""
import os, sys, json
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-skill')

from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic
import asyncio

CONTENT = sys.argv[1] if len(sys.argv) > 1 else ""

sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

if not all([sessdata, bili_jct]):
    print("Error: Missing Cookie", file=sys.stderr)
    sys.exit(1)

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

async def publish():
    try:
        builder = BuildDynamic()
        builder.add_text(CONTENT)
        result = await dynamic.send_dynamic(builder, cred)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        dyn_id = result.get('data', {}).get('dyn_id', 'unknown')
        print(f"SUCCESS: dyn_id={dyn_id}")
        return True
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False

asyncio.run(publish())
