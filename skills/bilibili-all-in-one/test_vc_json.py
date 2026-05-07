#!/usr/bin/env python3
"""Test VC domain API with JSON format and create_text."""

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

content_text = "🌐 内网穿透服务状态更新"

async def test_format(name, url, json_data, use_json=True):
    print(f"\n=== Testing: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        if use_json:
            resp = await client.post(url, json=json_data, cookies=cookies, headers=headers)
        else:
            resp = await client.post(url, data=json_data, cookies=cookies, headers={k: v for k, v in headers.items() if k != "Content-Type"})
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
            if data.get("code") == 0:
                print("✅ SUCCESS! Dynamic published!")
                return True
        except Exception as e:
            print(f"Error: {e}")
            print(f"Response: {resp.text[:500]}")
    return False

async def main():
    # Test create_text endpoint
    url1 = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_text?csrf={bili_jct}"
    
    tests = [
        ("create_text JSON - simple", url1, {"content": content_text}, True),
        ("create_text JSON - full", url1, {
            "content": content_text,
            "at_uids": "",
            "control": "[]",
        }, True),
        ("create_text form - simple", url1, {"content": content_text}, False),
        ("create_text form - full", url1, {
            "content": content_text,
            "at_uids": "",
            "control": "[]",
        }, False),
    ]
    
    # Also test create_dynamic with JSON
    url2 = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_dynamic?csrf={bili_jct}"
    tests.extend([
        ("create_dynamic JSON", url2, {
            "content": {"content": content_text},
            "type": 4,
        }, True),
        ("create_dynamic JSON full", url2, {
            "content": content_text,
            "type": 4,
            "at_uids": "",
            "control": [],
        }, True),
    ])
    
    for name, url, payload, use_json in tests:
        success = await test_format(name, url, payload, use_json)
        if success:
            print("\n🎉 Found working format!")
            break

if __name__ == "__main__":
    asyncio.run(main())
