#!/usr/bin/env python3
"""
简单任务验证测试
测试PyClaw USB的完整执行链
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.bootstrap import bootstrap
from pyclaw.memory.state_store import StateStore


def test_simple_task():
    print("🧪 测试PyClaw USB简单任务执行")
    print("-" * 50)
    
    state_store = StateStore()
    state_store.clear()
    
    try:
        # 1. 启动Runtime
        runtime = bootstrap()
        
        # 2. 设置简单任务
        task = "在工作区创建一个名为test文件.txt的文本文件，内容是'Hello, PyClaw!'"
        print(f"🎯 任务: {task}")
        
        runtime.set_task(task)
        
        print("\n📋 任务规划:")
        for i, step in enumerate(runtime.current_plan, 1):
            print(f"   Step {i}: [{step.action}] {step.description}")
        
        # 3. 执行任务
        print("\n🏃‍♂️ 开始执行任务")
        print("-" * 50)
        
        while runtime.state not in ["finished", "error", "waiting_confirm"]:
            result = runtime.step()
            
            print(f"\n📍 步骤 {result.step}: {result.observation}")
            if result.intent:
                print(f"   意图: {result.intent.type.value}")
            if result.tool_result:
                print(f"   工具结果: {result.tool_result}")
        
        print("-" * 50)
        
        if runtime.state == "finished":
            print("\n✅ 任务完成")
        elif runtime.state == "waiting_confirm":
            print("\n⚠️  需要用户确认")
        else:
            print("\n❌ 任务出错")
        
        # 4. 验证结果
        if runtime.state == "finished":
            from pyclaw.sandbox.fs_guard import FileGuard
            
            test_file_path = "test文件.txt"
            if FileGuard.file_exists(test_file_path):
                print(f"\n📄 文件创建成功: {FileGuard.safe_path(test_file_path)}")
                content = FileGuard.read_text(test_file_path)
                print(f"📝 文件内容: {repr(content)}")
                
                if "Hello, PyClaw!" in content:
                    print("✅ 文件内容正确")
                else:
                    print("❌ 文件内容错误")
                
                FileGuard.remove_file(test_file_path)
                print("🧹 测试文件已删除")
            else:
                print(f"\n❌ 文件 {test_file_path} 未找到")
        
        # 5. 验证状态保存
        print("\n💾 验证状态保存")
        saved_state = state_store.load()
        if saved_state:
            print("✅ 状态文件创建成功")
            print(f"   任务ID: {saved_state.get('task_id', '未知')}")
            print(f"   任务状态: {saved_state.get('state', '未知')}")
            
            state_store.clear()
        else:
            print("❌ 状态文件未创建")
            
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        print("🔍 详细错误信息:")
        print(traceback.format_exc())
        
        state_store.clear()
        return False
    finally:
        state_store.clear()


def main():
    print("🎯 PyClaw USB功能验证")
    print("=" * 50)
    
    success = test_simple_task()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 简单任务执行验证成功！PyClaw USB系统功能正常")
    else:
        print("❌ 简单任务执行验证失败")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
