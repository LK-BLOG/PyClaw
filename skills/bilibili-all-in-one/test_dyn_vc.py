#!/usr/bin/env python3
"""Test Bilibili VC domain dynamic API."""

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

content_text = "🤖 Test from OpenClaw AI - VC domain"

async def test_format(name, url, payload):
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
    # Test VC domain APIs
    tests = [
        ("VC create_dynamic", 
         f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_dynamic?csrf={bili_jct}", 
         {
             "content": json.dumps({"content": content_text}),
             "type": 4,
         }),
        ("VC create text", 
         f"https://api.vc.bilibili.com/dynamic/v2/create/text?csrf={bili_jct}", 
         {
             "content": content_text,
         }),
        ("VC feed create dyn", 
         f"https://api.vc.bilibili.com/dynamic/feed/create/dyn?csrf={bili_jct}", 
         {
             "content": json.dumps({"content": content_text}),
             "type": 4,
         }),
        ("VC v1 create text", 
         f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_text?csrf={bili_jct}", 
         {
             "content": content_text,
             "at_uids": "",
             "control": "[]",
         }),
    ]
    
    for name, url, payload in tests:
        await test_format(name, url, payload)

if __name__ == "__main__":
    asyncio.run(main())
