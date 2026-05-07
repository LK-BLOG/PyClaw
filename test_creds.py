#!/usr/bin/env python3
import requests

SESSDATA = '57bca764%2C1791886883%2C90408%2A41CjDOxH6ksPbIkoD3OrjLLeYj6ywP8P-VZIIJaGbAqk8CbnEd91az5BKE6WUPZ4sIBxkSVjYtOGRwc294d1JsNnJKT21SRXRmX1M4TzFhTWU3bUc5NURsakpyeVQtS1ZKYWVjWXpzbEYwOHRscWRCaHNMb05TM2ZudHpOU1lEdlpqM09FbzJLVG9nIIEC'
BILI_JCT = 'ee1c5409769b2fd79e68cec939d3b01f'
BUVID3 = 'BEDF1095-927E-9F61-3920-7364E75F194027291infoc'

url = "https://api.bilibili.com/x/space/v2/myinfo"
cookies = {'SESSDATA': SESSDATA, 'bili_jct': BILI_JCT, 'buvid3': BUVID3}
headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://space.bilibili.com/'}

response = requests.get(url, cookies=cookies, headers=headers)
result = response.json()
print(f"Code: {result.get('code')}, Message: {result.get('message')}")
if result.get('code') == 0:
    print(f"User: {result.get('data', {}).get('profile', {}).get('name')}")
