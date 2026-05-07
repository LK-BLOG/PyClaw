#!/usr/bin/env python3
"""PyClaw Skill 工具调用测试脚本"""
import asyncio
import sys

sys.path.insert(0, '/home/claw/.openclaw/workspace/pyclaw-public')

from pyclaw.skill import SkillManager

async def test_skill_tools():
    print("=" * 50)
    print("🧪 PyClaw Skill 插件工具测试")
    print("=" * 50)
    
    # 初始化 SkillManager
    skill_manager = SkillManager(skill_dir="/home/claw/.openclaw/workspace/pyclaw-public/skills")
    discovered = skill_manager.discover_skills()
    initialized = await skill_manager.initialize_all()
    print(f"\n📦 发现 {len(discovered)} 个 Skill，成功初始化 {initialized} 个")
    
    for skill_id, skill in skill_manager.skills.items():
        meta = skill_manager.skill_metadata[skill_id]
        print(f"   - {meta.name} v{meta.version} by {meta.author}")
    
    # 获取所有注册的工具
    all_tools = skill_manager.get_all_tools()
    print(f"\n🔧 已注册工具总数: {len(all_tools)}")
    
    # 测试工具: 从第一个 Skill 取工具直接执行
    if all_tools:
        first_tool = all_tools[0]
        print(f"\n1️⃣ 测试工具执行: {first_tool.definition.name}")
        try:
            # 直接调用工具的 execute 方法
            result = await first_tool.execute({})
            if result and result.success:
                print(f"✅ 成功!")
                print(f"   预览: {result.content[:120]}...")
            elif result:
                print(f"❌ 失败: {result.error}")
        except Exception as e:
            print(f"⚠️ 执行需要参数，跳过: {e}")
    else:
        print("\n⚠️ 没有找到可测试的工具")
    
    print("\n" + "=" * 50)
    print("🏁 PyClaw Skill 工具测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_skill_tools())
