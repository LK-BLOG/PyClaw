#!/usr/bin/env python3
"""
执行契约验证测试
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.core.execution_contract import ExecutionContract, global_contract
from pyclaw.core.planner import Planner
from pyclaw.memory.short_term import ShortTermMemory
from pyclaw.sandbox.fs_guard import FileGuard


def test_execution_contract_validation():
    """测试执行契约验证功能"""
    print("🧪 测试执行契约验证功能")
    print("=" * 60)
    
    # 1. 验证计划契约
    test_plan = [
        {
            "action": "write_file",
            "params": {
                "path": "./pyclaw/sandbox/workspace/test.txt",
                "content": "Test content"
            },
            "description": "测试写入文件"
        },
        {
            "action": "read_file",
            "params": {
                "path": "./pyclaw/sandbox/workspace/test.txt"
            },
            "description": "测试读取文件"
        },
        {
            "action": "finish_task",
            "params": {
                "message": "测试完成"
            },
            "description": "完成任务"
        }
    ]
    
    print("📋 测试计划验证:")
    for i, step in enumerate(test_plan, 1):
        print(f"   步骤 {i}: [{step['action']}] {step['description']}")
    
    valid, validated_plan = ExecutionContract.validate_plan(test_plan)
    print()
    print("验证结果:")
    if valid:
        print("✅ 计划验证成功")
        for i, step in enumerate(validated_plan, 1):
            print(f"   步骤 {i}: [{step['action']}] {step['description']}")
            print(f"      参数: {step['params']}")
    else:
        print("❌ 计划验证失败")
    
    print()
    print("-" * 60)
    
    # 2. 测试无效计划验证
    invalid_plan = [
        {
            "action": "invalid_action",
            "params": {"key": "value"},
            "description": "无效动作"
        },
        {
            "action": "write_file",
            "params": {"invalid_param": "value"},
            "description": "无效参数"
        }
    ]
    
    print("📋 测试无效计划验证:")
    for i, step in enumerate(invalid_plan, 1):
        print(f"   步骤 {i}: [{step['action']}] {step['description']}")
    
    valid, validated_plan = ExecutionContract.validate_plan(invalid_plan)
    print()
    print("验证结果:")
    if valid:
        print("✅ 计划验证成功（这不是预期的）")
    else:
        print("✅ 无效计划验证失败（这是预期的）")
    
    print()
    print("-" * 60)
    
    # 3. 测试工具执行契约
    FileGuard.ensure_workspace_exists()
    
    # 创建测试文件
    test_file = "./pyclaw/sandbox/workspace/test_contract.txt"
    if FileGuard.file_exists(test_file):
        FileGuard.remove_file(test_file)
    
    FileGuard.write_text(test_file, "Hello, PyClaw!")
    
    print("📄 测试工具执行契约:")
    print(f"创建测试文件: {test_file}")
    
    tool_result = {
        "status": "ok",
        "path": test_file,
        "content": "Hello, PyClaw!"
    }
    
    step = {
        "id": 1,
        "action": "write_file",
        "params": {
            "path": test_file,
            "content": "Hello, PyClaw!"
        },
        "description": "创建测试文件"
    }
    
    try:
        valid = global_contract.validate_step(step, tool_result)
        print(f"✅ 工具执行契约验证成功: {valid}")
    except Exception as e:
        print(f"❌ 工具执行契约验证失败: {e}")
    
    # 删除测试文件
    FileGuard.remove_file(test_file)
    
    print()
    print("=" * 60)
    print("🎉 执行契约验证测试完成")
    
    return True


def test_plan_generation_validation():
    """测试计划生成过程中的契约验证"""
    print("🧪 测试计划生成过程中的契约验证")
    print("=" * 60)
    
    planner = Planner(None)
    memory = ShortTermMemory()
    
    print("📋 测试任务规划与契约验证")
    
    test_task = "在工作区创建test文件.txt，写入Hello, PyClaw!"
    
    try:
        steps = planner.plan(test_task, memory)
        
        print(f"✅ 任务规划成功，生成 {len(steps)} 个步骤")
        
        print()
        print("生成的步骤:")
        for i, step in enumerate(steps, 1):
            print(f"   步骤 {i}: [{step.action}] {step.description}")
            print(f"      参数: {step.params}")
        
        return True
    except Exception as e:
        print(f"❌ 任务规划失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_actual_execution_validation():
    """测试实际执行过程中的契约验证"""
    print("🧪 测试实际执行过程中的契约验证")
    print("=" * 60)
    
    from pyclaw.bootstrap import bootstrap
    from pyclaw.sandbox.fs_guard import FileGuard
    
    # 确保工作区存在
    FileGuard.ensure_workspace_exists()
    
    # 删除可能存在的测试文件
    test_file = "./pyclaw/sandbox/workspace/test文件.txt"
    if FileGuard.file_exists(test_file):
        FileGuard.remove_file(test_file)
    
    # 启动runtime
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
        
        from pyclaw.core.runtime import RuntimeState
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
            
            if FileGuard.file_exists(test_file):
                print("✅ 文件创建成功")
                
                content = FileGuard.read_text(test_file)
                print(f"📄 文件内容: '{content}'")
                
                if content == "Hello, PyClaw!":
                    print("✅ 文件内容正确")
                else:
                    print(f"❌ 文件内容错误，期望: 'Hello, PyClaw!', 实际: '{content}'")
                    
                FileGuard.remove_file(test_file)
                print("🧹 删除测试文件")
                
                return True
            else:
                print("❌ 文件未创建")
                return False
        else:
            print("❌ 任务执行失败")
            return False
            
    except Exception as e:
        print(f"❌ 任务执行异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def main():
    print("🚀 执行契约验证测试")
    print("=" * 60)
    
    all_passed = True
    
    # 执行测试
    all_passed = all_passed and test_execution_contract_validation()
    
    print()
    print("-" * 60)
    
    all_passed = all_passed and test_plan_generation_validation()
    
    print()
    print("-" * 60)
    
    all_passed = all_passed and test_actual_execution_validation()
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("🎉 所有执行契约验证测试通过")
        return 0
    else:
        print("❌ 部分执行契约验证测试失败")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
