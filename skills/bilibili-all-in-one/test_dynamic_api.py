#!/usr/bin/env python3
"""Test Bilibili dynamic API endpoints."""

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

content = "Test dynamic from Python script"

async def test_endpoint(name, url, payload):
    print(f"\n=== Testing: {name} ===")
    print(f"URL: {url}")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=payload, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"Response (first 500 chars): {resp.text[:500]}")

async def main():
    # Test various endpoints
    tests = [
        ("Old send_text", "https://api.bilibili.com/x/dynamic/send_text", {
            "content": json.dumps({"content": content, "images": []}),
            "type": "4",
            "csrf": bili_jct,
        }),
        ("New v2 send", "https://api.bilibili.com/x/dynamic/v2/send", {
            "type": 4,
            "content": content,
            "csrf": bili_jct,
        }),
        ("Create dyn", "https://api.bilibili.com/x/dynamic/feed/create/dyn", {
            "dyn_req": json.dumps({"content": content, "ctrl": "[]"}),
            "csrf": bili_jct,
        }),
        ("Create endpoint", "https://api.bilibili.com/x/dynamic/create", {
            "type": 4,
            "content": json.dumps({"content": content}),
            "csrf": bili_jct,
        }),
        ("Web create", "https://api.bilibili.com/x/dynamic/web/create", {
            "type": 4,
            "content": content,
            "csrf": bili_jct,
        }),
    ]
    
    for name, url, payload in tests:
        await test_endpoint(name, url, payload)

if __name__ == "__main__":
    asyncio.run(main())
