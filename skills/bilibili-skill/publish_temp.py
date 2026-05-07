#!/usr/bin/env python3
import asyncio
import json
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

# Direct cookies from file
cookie_line = "buvid3=971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc; b_nut=1775453241; _uuid=AE53FED2-462C-5A4B-EBF7-53ED8B10A2BEE42127infoc; buvid4=27BFD919-2719-7D2A-1BAF-38BE4320170342461-026040613-gfwqg2GtUR3jK2RgPhSZdg8VV1mhuZf1xGHePlPrOG09SdXFmC2xKUZXt3KfVu9a; buvid_fp=fd572c33f299bf8f2d6aa2ffbde45eed; DedeUserID=129131127; DedeUserID__ckMd5=2b4718fee47c7061; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; theme-switch-show=SHOWED; theme_style=dark; CURRENT_QUALITY=0; rpdid=0zbfAHLMg8|14Gm2lB2l|CJ|3w1W9Czk; CURRENT_LANGUAGE=; bmg_af_switch=1; bmg_src_def_domain=i1.hdslb.com; hit-dyn-v2=1; SESSDATA=b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC; bili_jct=928556c5646e53252457b6a3ccc298ee; sid=8jrfmkn0; bp_t_offset_129131127=1194472246588997632; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzcyMDc1MDIsImlhdCI6MTc3Njk0ODI0MiwicGx0IjotMX0.IegmGksQ0I15OO9RQJYzymJT7peRDPoN99dGlyjZewY; bili_ticket_expires=1777207442; CURRENT_FNVAL=4048; browser_resolution=1366-1024; home_feed_column=4; b_lsid=CD2E9C2D_19DBEE3D4B4"

# Parse cookies
sessdata = ""
bili_jct = ""
buvid3 = ""

for item in cookie_line.split('; '):
    if '=' in item:
        key, value = item.split('=', 1)
        if key == 'SESSDATA':
            sessdata = value
        elif key == 'bili_jct':
            bili_jct = value
        elif key == 'buvid3':
            buvid3 = value

print(f"SESSDATA: {sessdata[:20]}...")
print(f"bili_jct: {bili_jct}")
print(f"buvid3: {buvid3}")

cred = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

content = """个人网站更新地址👇

https://recycling-possibilities-lecture-jewel.trycloudflare.com

（链接需要点进动态才能打开，Cloudflare 免费隧道默认这样）
欢迎来留言板留言交流✈️

(自动发布)"""

async def publish():
    builder = BuildDynamic()
    builder.add_text(content)
    result = await dynamic.send_dynamic(builder, cred)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

result = asyncio.run(publish())
dyn_id = result.get('data', {}).get('dyn_id', '未知')
print(f"发布成功！动态ID: {dyn_id}")
print(f"动态链接: https://t.bilibili.com/{dyn_id}")
