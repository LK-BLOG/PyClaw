#!/usr/bin/env python3
"""
B站动态发布脚本 - 使用 bilibili-api-python 库
"""
import asyncio
from bilibili_api import Credential, dynamic
from bilibili_api.dynamic import BuildDynamic

async def publish_dynamic():
    # 从Cookie.txt中提取的有效认证信息
    SESSDATA = "b17145ac%2C1792500142%2Cad4af%2A41CjA98inJdtSfJvok7oH4I4iCHehRV1_fuKYkDWoVirgEPbEmLxDFpF949Mn5d3ZONlQSVkZudGpFUUtRV1RGQ3VyTl8zZE5MMEp1VmhNLTFwT2ZNTzlzc29ueFYyMG1mMmxnV1g0NmNaRnJPUmNyVUVTQ2FOeElQa21DQU9rTEdfSVVOaV84YnN3IIEC"
    BILI_JCT = "928556c5646e53252457b6a3ccc298ee"
    BUVID3 = "971B9829-2CAC-6EFE-48F9-BBEB536B235541879infoc"
    
    # 隧道链接
    tunnel_url = "https://monday-stats-begun-philip.trycloudflare.com"
    
    # 动态内容 - 日常风格
    content = f"""🌐 日常播报～

跟大家说个事，我的Cloudflare小隧道又跑起来啦！
个人网站地址在这里 👉 {tunnel_url}

💡 温馨提示：得点进动态详情才能打开链接哦，Cloudflare免费隧道就是这么傲娇的～
欢迎来我的小站逛逛，留言板已经准备好了，有空来踩踩呀！

🤖 偷偷说一句，这条动态是OpenClaw机器人自动发的哦～
现在每5分钟就会自动检查一次隧道状态，掉线了会自己重连还会发动态通知大家，再也不用我手动折腾啦！

#日常分享 #Cloudflare #技术摸鱼 #小爪在干活"""
    
    try:
        # 创建凭证
        cred = Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3
        )
        
        # 检查登录状态
        print("正在检查登录状态...")
        try:
            login_info = await cred.check_valid()
            if not login_info:
                print("❌ Cookie 无效或已过期")
                return False
            print("✅ 登录状态有效")
        except:
            print("⚠️  跳过登录状态检查，直接尝试发布...")
        
        # 构建动态
        print("正在构建动态...")
        builder = BuildDynamic()
        builder.add_text(content)
        
        # 发布动态
        print("正在发布动态...")
        result = await dynamic.send_dynamic(builder, credential=cred)
        
        print("✅ 动态发布成功！")
        print(f"结果: {result}")
        
        # 提取动态ID
        if isinstance(result, dict) and 'dyn_id' in result.get('data', {}):
            dyn_id = result['data']['dyn_id']
            print(f"动态ID: {dyn_id}")
            print(f"动态链接: https://t.bilibili.com/{dyn_id}")
        
        print(f"\n内容预览:\n{content}")
        return True
        
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(publish_dynamic())
