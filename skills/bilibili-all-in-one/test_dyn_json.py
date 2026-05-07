#!/usr/bin/env python3
"""Test Bilibili dynamic API with JSON payload."""

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
    "Content-Type": "application/json",
}

url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"

content_text = "Test from OpenClaw AI - JSON payload"

async def test_format(name, json_data):
    print(f"\n=== Testing: {name} ===")
    print(f"Payload: {json.dumps(json_data, ensure_ascii=False)[:300]}")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=json_data, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"Response: {resp.text[:500]}")

async def main():
    # Test JSON payload formats
    tests = [
        ("JSON dyn_req with contents + csrf in query", {
            "dyn_req": {
                "content": {
                    "contents": [
                        {"raw_text": content_text, "type": 1}
                    ]
                },
                "type": 4,
                "rid": 0,
                "ctrl": [],
            },
        }),
        ("JSON with content directly", {
            "content": content_text,
            "type": 4,
        }),
        ("JSON with words field", {
            "content": {
                "words": content_text,
            },
            "type": 4,
        }),
    ]
    
    for name, json_data in tests:
        await test_format(name, json_data)

if __name__ == "__main__":
    asyncio.run(main())
