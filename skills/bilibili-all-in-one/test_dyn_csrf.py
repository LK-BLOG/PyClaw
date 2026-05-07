#!/usr/bin/env python3
"""Test Bilibili dynamic API with csrf in query params."""

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

content_text = "🤖 Test from OpenClaw AI - with csrf in query"

async def test_format(name, url, payload, use_json=False):
    print(f"\n=== Testing: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        if use_json:
            resp = await client.post(url, json=payload, cookies=cookies, headers=headers)
        else:
            resp = await client.post(url, data=payload, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"Response: {resp.text[:500]}")

async def main():
    base_url = "https://api.bilibili.com/x/dynamic/feed/create/dyn"
    
    # Test different approaches with csrf
    tests = [
        ("CSRF in query + form dyn_req", 
         f"{base_url}?csrf={bili_jct}", 
         {"dyn_req": json.dumps({
             "content": {
                 "contents": [{"raw_text": content_text, "type": 1}]
             },
             "type": 4,
             "rid": 0,
             "ctrl": [],
         })},
         False),
        ("CSRF in form data", 
         base_url, 
         {
             "dyn_req": json.dumps({
                 "content": {
                     "contents": [{"raw_text": content_text, "type": 1}]
                 },
                 "type": 4,
                 "rid": 0,
                 "ctrl": [],
             }),
             "csrf": bili_jct,
             "csrf_token": bili_jct,
         },
         False),
        ("CSRF in query + JSON payload", 
         f"{base_url}?csrf={bili_jct}", 
         {
             "dyn_req": {
                 "content": {
                     "contents": [{"raw_text": content_text, "type": 1}]
                 },
                 "type": 4,
                 "rid": 0,
                 "ctrl": [],
             },
         },
         True),
    ]
    
    for name, url, payload, use_json in tests:
        await test_format(name, url, payload, use_json)

if __name__ == "__main__":
    asyncio.run(main())
