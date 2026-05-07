#!/usr/bin/env python3
"""Test Bilibili dynamic API format."""

import asyncio
import json
import os
import httpx

sessdata = os.environ.get("BILIBILI_SESSDATA", "")
bili_jct = os.environ.get("BILIBILI_BILI_JCT", "")
buvid3 = os.environ.get("BILIBILI_BUVID3", "")

cookies = {
    "SESSDATA": sessdata,
    "bili_jct": bili_jct,
    "buvid3": buvid3,
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
}

url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

content_text = "🤖 Test dynamic from OpenClaw AI assistant\n\nThis is a test message."

async def test_format(name, payload):
    print(f"\n=== Testing: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=payload, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"Response: {resp.text[:200]}")

async def main():
    # Test different payload formats
    tests = [
        ("Format 1 - simple content", {
            "content": content_text,
            "type": 4,
            "csrf": bili_jct,
        }),
        ("Format 2 - dyn_req with content", {
            "dyn_req": json.dumps({"content": content_text}),
            "csrf": bili_jct,
        }),
        ("Format 3 - dyn_req with full structure", {
            "dyn_req": json.dumps({
                "content": content_text,
                "at_uids": "",
                "control": "[]",
            }),
            "csrf": bili_jct,
        }),
        ("Format 4 - JSON content", {
            "content": json.dumps({"content": content_text}),
            "type": 4,
            "csrf": bili_jct,
        }),
        ("Format 5 - with platform", {
            "content": json.dumps({"content": content_text}),
            "type": 4,
            "csrf": bili_jct,
            "platform": "pc",
            "from": "create.dynamic.web",
        }),
    ]
    
    for name, payload in tests:
        await test_format(name, payload)

if __name__ == "__main__":
    asyncio.run(main())
