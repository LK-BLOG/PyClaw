#!/usr/bin/env python3
"""发布个人网站新地址到 B 站动态"""

import asyncio
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace/skills/bilibili-all-in-one')

from main import BilibiliAllInOne

SESSDATA = "57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC"
BILI_JCT = "ee1c5409769b2fd79e68cec939d3b01f"
BUVID3 = "BEDF1095-927E-9F61-3920-7364E75F194027291infoc"

NEW_URL = "https://easy-webs-stand.loca.lt"

CONTENT = f"""个人网站更新地址👇
{NEW_URL}
（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""

async def main():
    print("正在发布 B 站动态...")
    print(f"内容:\n{CONTENT}\n")
    
    app = BilibiliAllInOne(
        sessdata=SESSDATA,
        bili_jct=BILI_JCT,
        buvid3=BUVID3
    )
    
    result = await app.execute("publisher", "publish_dynamic", content=CONTENT)
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get('status') == 'success' or result.get('success'):
        print("\n✅ 动态发布成功！")
    else:
        print(f"\n❌ 发布失败: {result.get('message')}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
