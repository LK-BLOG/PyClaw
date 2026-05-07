#!/usr/bin/env python3
"""Test Bilibili dynamic API with words format."""

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

content_text = "Test from OpenClaw - words format"

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
    # Test different payload formats with words structure
    tests = [
        ("Words array in content", {
            "content": json.dumps({
                "words": content_text,
            }),
            "type": 4,
            "csrf": bili_jct,
        }),
        ("Full words structure", {
            "content": json.dumps({
                "words": content_text,
                "at_control": [],
                "topics": [],
            }),
            "type": 4,
            "csrf": bili_jct,
        }),
        ("Words with pictures empty", {
            "content": json.dumps({
                "words": content_text,
                "pictures": [],
            }),
            "type": 4,
            "csrf": bili_jct,
        }),
        ("dyn_req with words", {
            "dyn_req": json.dumps({
                "words": content_text,
                "type": 4,
            }),
            "csrf": bili_jct,
        }),
        ("Full content with type inside", {
            "content": json.dumps({
                "type": 4,
                "words": content_text,
            }),
            "csrf": bili_jct,
        }),
    ]
    
    for name, payload in tests:
        await test_format(name, payload)

if __name__ == "__main__":
    asyncio.run(main())
