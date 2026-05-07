#!/bin/bash
export BILIBILI_SESSDATA="b17145ac,1792500142,ad4af*41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
export BILIBILI_BILI_JCT="928556c5646e53252457b6a3ccc298ee"
export BILIBILI_BUVID3="971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"
python3 /home/claw/.openclaw/workspace/skills/bilibili-skill/bilibili-cli.py dynamic publish --content "测试动态 $(date +%H:%M)"
