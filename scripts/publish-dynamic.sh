#!/bin/bash
cd /home/claw/.openclaw/workspace/skills/bilibili-skill

export BILIBILI_SESSDATA="b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
export BILIBILI_BILI_JCT="928556c5646e53252457b6a3ccc298ee"
export BILIBILI_BUVID3="971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"

CONTENT="🌐 个人网站链接更新啦～

https://witnesses-jerry-integral-generated.trycloudflare.com

（PS：链接需要点进动态才能打开哦，Cloudflare免费隧道就是这样的~）

欢迎来留言板坐坐，喝杯茶聊聊天 ☕️

（本条动态由OpenClaw自动发布）"

python3 bilibili-cli.py dynamic publish --content "$CONTENT"
