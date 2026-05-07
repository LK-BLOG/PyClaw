#!/usr/bin/env python3
"""
测试任务执行
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.bootstrap import bootstrap
from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.state_store import StateStore
from pyclaw.core.runtime import RuntimeState


def test_task_execution():
    """测试任务执行"""
    print("🧪 测试任务执行")
    print("=" * 60)
    
    state_store = StateStore()
    state_store.clear()
    
    # 删除可能存在的测试文件
    if FileGuard.file_exists("./pyclaw/sandbox/workspace/test文件.txt"):
        FileGuard.remove_file("./pyclaw/sandbox/workspace/test文件.txt")
    
    try:
        runtime = bootstrap()
        
        test_task = "在工作区创建test文件.txt，写入Hello, PyClaw!"
        print(f"🎯 任务: {test_task}")
        
        runtime.set_task(test_task)
        
        print()
        print("📋 任务规划:")
        for i, step in enumerate(runtime.current_plan, 1):
            print(f"   步骤 {i}: [{step.action}] {step.description}")
        
        print()
        print("🏃‍♂️ 执行任务:")
        
        while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR:
            result = runtime.step()
            
            print(f"\n📍 步骤 {result.step}:")
            print(f"   状态: {runtime.state}")
            print(f"   观察: {result.observation}")
            if result.intent:
                print(f"   意图: {result.intent.type.value}")
            if result.tool_result:
                print(f"   工具结果: {result.tool_result}")
        
        print()
        print("=" * 60)
        
        if runtime.state == RuntimeState.FINISHED:
            print("✅ 任务执行成功")
            
            if FileGuard.file_exists("./pyclaw/sandbox/workspace/test文件.txt"):
                print("✅ 文件创建成功")
                
                content = FileGuard.read_text("./pyclaw/sandbox/workspace/test文件.txt")
                print(f"📄 文件内容: '{content}'")
                
                if content == "Hello, PyClaw!":
                    print("✅ 文件内容正确")
                else:
                    print(f"❌ 文件内容错误，期望: 'Hello, PyClaw!', 实际: '{content}'")
            else:
                print("❌ 文件未创建")
        else:
            print("❌ 任务执行失败")
            if runtime.state == RuntimeState.ERROR:
                print("🚨 任务执行错误")
        
        # 删除测试文件
        if FileGuard.file_exists("./pyclaw/sandbox/workspace/test文件.txt"):
            FileGuard.remove_file("./pyclaw/sandbox/workspace/test文件.txt")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        
        # 删除测试文件
        if FileGuard.file_exists("./pyclaw/sandbox/workspace/test文件.txt"):
            FileGuard.remove_file("./pyclaw/sandbox/workspace/test文件.txt")
            
        return False
    finally:
        state_store.clear()


def main():
    print("🚀 任务执行测试")
    print("=" * 60)
    
    test_task_execution()


if __name__ == "__main__":
    main()
