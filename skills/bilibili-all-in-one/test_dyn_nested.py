#!/usr/bin/env python3
"""Test Bilibili dynamic API with nested dyn_req structure."""

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
    "Referer": "https://t.bilibili.com/",
    "Origin": "https://t.bilibili.com",
}

url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

content_text = "Test from OpenClaw AI - nested format"

async def test_format(name, payload):
    print(f"\n=== Testing: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=payload, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"Response: {resp.text[:500]}")

async def main():
    # Test nested dyn_req structure
    tests = [
        ("Nested dyn_req with contents array", {
            "dyn_req": json.dumps({
                "content": {
                    "contents": [
                        {
                            "raw_text": content_text,
                            "type": 1,
                            "biz_id": ""
                        }
                    ]
                },
                "orig": {},
                "type": 4,
                "rid": 0,
                "ctrl": [],
            }),
            "csrf": bili_jct,
        }),
        ("Simplified dyn_req content", {
            "dyn_req": json.dumps({
                "content": {
                    "contents": [{"raw_text": content_text, "type": 1}]
                },
                "type": 4,
            }),
            "csrf": bili_jct,
        }),
        ("dyn_req with words", {
            "dyn_req": json.dumps({
                "content": {
                    "words": content_text,
                },
                "type": 4,
            }),
            "csrf": bili_jct,
        }),
        ("With pictures field empty", {
            "dyn_req": json.dumps({
                "content": {
                    "contents": [{"raw_text": content_text, "type": 1}],
                    "pictures": [],
                },
                "type": 4,
            }),
            "csrf": bili_jct,
        }),
    ]
    
    for name, payload in tests:
        await test_format(name, payload)

if __name__ == "__main__":
    asyncio.run(main())
