#!/usr/bin/env python3
"""Test VC domain API with correct formats."""

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

content_text = "🌐 内网穿透服务状态更新：\n当前可用地址：https://major-ants-clean.loca.lt\n\n🤖 此动态由 OpenClaw AI 助手自动发布"

async def test_format(name, url, payload):
    print(f"\n=== Testing: {name} ===")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=payload, cookies=cookies, headers=headers)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
            if data.get("code") == 0:
                print("✅ SUCCESS! Dynamic published!")
                return True
        except:
            print(f"Response: {resp.text[:500]}")
    return False

async def main():
    base_url = f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_dynamic?csrf={bili_jct}"
    
    # Test various formats for VC API
    tests = [
        ("Plain content, no JSON", {
            "content": content_text,
            "type": 4,
        }),
        ("dyn_req with content", {
            "dyn_req": json.dumps({"content": content_text}),
            "type": 4,
        }),
        ("Content with pictures", {
            "content": json.dumps({"content": content_text, "pictures": []}),
            "type": 4,
        }),
        ("Content with words", {
            "content": json.dumps({"words": content_text}),
            "type": 4,
        }),
        ("Contents array format", {
            "content": json.dumps({
                "contents": [{"raw_text": content_text, "type": 1}]
            }),
            "type": 4,
        }),
        ("Extra fields: at_uids, control", {
            "content": content_text,
            "type": 4,
            "at_uids": "",
            "control": "[]",
        }),
        ("With from field", {
            "content": content_text,
            "type": 4,
            "from": "create.dynamic.web",
        }),
        ("With platform field", {
            "content": content_text,
            "type": 4,
            "platform": "pc",
        }),
    ]
    
    for name, payload in tests:
        success = await test_format(name, base_url, payload)
        if success:
            print("\n🎉 Found working format!")
            break

if __name__ == "__main__":
    asyncio.run(main())
