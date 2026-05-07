#!/usr/bin/env python3
"""
测试Runtime详细状态信息
用于调试任务执行无限循环问题
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.state_store import StateStore
from pyclaw.bootstrap import bootstrap
from pyclaw.core.runtime import RuntimeState


def test_runtime_details():
    print("🧪 测试Runtime详细状态信息")
    print("-" * 50)

    # 1. 初始化
    state_store = StateStore()
    state_store.clear()

    # 2. 创建测试任务
    task = "在工作区创建一个名为test文件.txt的文本文件，内容是'Hello, PyClaw!'"
    print(f"🎯 任务: {task}")
    
    # 3. 启动Runtime
    runtime = bootstrap()
    
    # 4. 设置任务
    runtime.set_task(task)
    
    # 5. 打印初始状态
    print(f"\n🚀 初始状态:")
    print(f"   状态: {runtime.state}")
    print(f"   当前步骤: {runtime.step_count}")
    print(f"   计划长度: {len(runtime.current_plan)}")
    print(f"   计划索引: {runtime.plan_index}")
    
    # 6. 显示计划内容
    print(f"\n📋 计划内容:")
    for i, step in enumerate(runtime.current_plan, 1):
        print(f"   步骤 {i}:")
        print(f"      动作: {step.action}")
        print(f"      参数: {step.params}")
        print(f"      描述: {step.description}")
    
    # 7. 逐步执行
    print(f"\n🏃‍♂️ 逐步执行:")
    max_steps = 15
    steps_completed = 0
    
    while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR and runtime.state != RuntimeState.WAITING_CONFIRM and steps_completed < max_steps:
        print(f"\n📍 步骤 {runtime.step_count + 1}:")
        
        result = runtime.step()
        
        print(f"   状态: {runtime.state}")
        print(f"   观察: {result.observation}")
        
        if result.intent:
            print(f"   意图: {result.intent.type.value}")
        
        if result.tool_result:
            print(f"   工具结果: {result.tool_result}")
        
        print(f"   计划索引: {runtime.plan_index}")
        print(f"   计划长度: {len(runtime.current_plan)}")
        steps_completed += 1
        
        # 检查是否真的完成了
        if runtime.state == RuntimeState.FINISHED:
            print("\n✅ 任务完成")
            break
        
        # 如果需要确认，停止
        if runtime.state == RuntimeState.WAITING_CONFIRM:
            print("\n⚠️ 需要用户确认")
            break
        
        # 如果错误，停止
        if runtime.state == RuntimeState.ERROR:
            print("\n❌ 任务出错")
            break
    
    # 8. 打印最终状态
    print(f"\n📊 最终状态:")
    print(f"   状态: {runtime.state}")
    print(f"   执行步骤: {steps_completed}")
    
    # 9. 保存状态（如果任务未完成）
    if runtime.state != RuntimeState.FINISHED:
        print(f"\n💾 保存状态:")
        state_store.save(runtime.export_state())
        print("✅ 状态已保存")
    
    # 10. 检查文件是否已创建（如果任务完成）
    if runtime.state == RuntimeState.FINISHED:
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
    else:
        print(f"\n❌ 任务未完成")
        
        # 检查为什么任务没有完成
        print(f"\n🔍 未完成原因分析:")
        if steps_completed >= max_steps:
            print("   任务未完成: 已达到最大执行步骤")
        else:
            print(f"   任务未完成: 当前状态为 {runtime.state}")


def main():
    print("🎯 PyClaw Runtime状态测试")
    print("=" * 50)
    
    try:
        test_runtime_details()
        return 0
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        print("🔍 详细错误信息:")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
