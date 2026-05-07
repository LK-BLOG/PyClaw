#!/bin/bash
export BILIBILI_SESSDATA="b17145ac,1792500142,ad4af*41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
export BILIBILI_BILI_JCT="928556c5646e53252457b6a3ccc298ee"
export BILIBILI_BUVID3="971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"

CONTENT="🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 https://warrant-independence-bacon-attempt.trycloudflare.com

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"

cd /home/claw/.openclaw/workspace/skills/bilibili-skill
python3 bilibili-cli.py dynamic publish --content "$CONTENT"
