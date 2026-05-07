#!/usr/bin/env python3
"""Final tests for Bilibili dynamic API."""

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

url = f"https://api.bilibili.com/x/dynamic/feed/create/dyn?csrf={bili_jct}"

content_text = "🤖 Test from OpenClaw AI assistant"

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
    # Test various content formats
    tests = [
        ("Simple text content", {
            "content": json.dumps({"content": content_text}),
            "type": 4,
        }),
        ("Content with type inside JSON", {
            "content": json.dumps({"content": content_text, "type": 4}),
        }),
        ("Just content string", {
            "content": content_text,
            "type": 4,
        }),
        ("Content with pictures", {
            "content": json.dumps({"content": content_text, "pictures": []}),
            "type": 4,
        }),
        ("Content with at_control", {
            "content": json.dumps({"content": content_text, "at_control": [], "topics": []}),
            "type": 4,
        }),
        ("Content as JSON string no extra", {
            "content": json.dumps(content_text),
            "type": 4,
        }),
    ]
    
    for name, payload in tests:
        await test_format(name, payload)

if __name__ == "__main__":
    asyncio.run(main())
