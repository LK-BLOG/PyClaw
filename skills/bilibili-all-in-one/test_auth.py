#!/usr/bin/env python3
"""Test Bilibili authentication"""

import asyncio
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-all-in-one')

from src.auth import BilibiliAuth

auth = BilibiliAuth(
    sessdata="57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC",
    bili_jct="ee1c5409769b2fd79e68cec939d3b01f",
    buvid3="BEDF1095-927E-9F61-3920-7364E75F194027291infoc",
)

async def main():
    print(f"Is authenticated: {auth.is_authenticated}")
    print(f"Cookies: {list(auth.cookies.keys())}")
    result = await auth.verify()
    print(f"Verify result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
