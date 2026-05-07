#!/usr/bin/env python3
"""发布B站动态"""
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# 凭据
SESSDATA = '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC'
BILI_JCT = 'ee1c5409769b2fd79e68cec939d3b01f'
BUVID3 = 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc'

async def main():
    cred = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
    
    # 隧道链接
    tunnel_url = "https://wrestling-provisions-menu-stunning.trycloudflare.com"
    
    # 动态内容 - 日常风格
    content = f"""个人网站更新地址👇
{tunnel_url}

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️(自动发布)"""
    
    builder = BuildDynamic()
    builder.add_text(content)
    
    result = await dynamic.send_dynamic(builder, cred)
    print(f"Result code: {result.get('code')}")
    print(f"Message: {result.get('message')}")
    
    if result.get('code') == 0:
        print(f"✅ 发布成功！动态ID: {result.get('data', {}).get('dyn_id')}")
    else:
        print(f"❌ 发布失败")

if __name__ == "__main__":
    asyncio.run(main())
