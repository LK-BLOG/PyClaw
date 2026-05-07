#!/usr/bin/env python3
"""Test getting user info and dynamic API endpoints."""

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
}

async def test_get(name, url):
    print(f"\n=== Testing GET: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
        except:
            print(f"Response: {resp.text[:200]}")

async def main():
    # Test navigation APIs
    tests = [
        ("User info", "https://api.bilibili.com/x/web-interface/nav"),
        ("Dynamic draft", "https://api.bilibili.com/x/dynamic/feed/draft/get"),
        ("Dynamic list", "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"),
    ]
    
    for name, url in tests:
        await test_get(name, url)

if __name__ == "__main__":
    asyncio.run(main())
