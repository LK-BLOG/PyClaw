#!/bin/bash
cd "$(dirname "$0")"

export BILIBILI_SESSDATA="b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
export BILIBILI_BILI_JCT="928556c5646e53252457b6a3ccc298ee"
export BILIBILI_BUVID3="971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"

CONTENT="🌐 日常小播报！

跟大家同步一下，我的小站隧道又稳定运行啦～
👉 https://witnesses-jerry-integral-generated.trycloudflare.com

💡 友情提示：得点进动态详情页才能打开链接哦，Cloudflare就是这么傲娇的哈哈哈～
欢迎来我的个人主页逛逛，留言板随时恭候！

🤖 悄悄说：这条动态是OpenClaw机器人自动发布的哦～
现在每5分钟就会自动检查隧道状态，掉线了会自己重连还会发动态通知，再也不用我手动操作啦！
科技改变摸鱼生活 ✌️

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"

python3 bilibili-cli.py dynamic publish --content "$CONTENT"
