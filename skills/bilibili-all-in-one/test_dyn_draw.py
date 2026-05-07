#!/usr/bin/env python3
"""Test Bilibili dynamic draw/create API."""

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

url = "https://api.bilibili.com/x/dynamic/v2/draw/create"

content_text = "Test from OpenClaw AI - draw/create API"

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
    # Test draw/create API
    tests = [
        ("Basic draw create", {
            "content": content_text,
            "csrf": bili_jct,
            "from": "create.dynamic.web",
        }),
        ("With at_control", {
            "content": content_text,
            "at_control": "[]",
            "csrf": bili_jct,
            "from": "create.dynamic.web",
        }),
        ("With topics", {
            "content": content_text,
            "at_control": "[]",
            "topics": "[]",
            "csrf": bili_jct,
            "from": "create.dynamic.web",
        }),
        ("JSON content", {
            "content": json.dumps({"content": content_text}),
            "csrf": bili_jct,
            "from": "create.dynamic.web",
        }),
    ]
    
    for name, payload in tests:
        await test_format(name, payload)

if __name__ == "__main__":
    asyncio.run(main())
