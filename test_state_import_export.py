#!/usr/bin/env python3
"""
测试状态导入导出功能

验证系统状态是否可以正确地导出和导入。
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')


def test_state_import_export():
    """测试状态导入导出功能"""
    print("🚀 测试状态导入导出功能")
    print("=" * 60)
    
    from pyclaw import create_runtime
    
    # 创建第一个运行时
    runtime1 = create_runtime()
    print("✅ 运行时1创建成功")
    
    # 执行任务
    task = "在工作区创建test文件.txt，写入Hello, PyClaw!"
    print(f"🎯 执行任务: '{task}'")
    results1 = runtime1.run(task)
    
    # 验证任务执行结果
    assert len(results1) > 0
    print("✅ 任务执行成功")
    
    # 导出状态
    state1 = runtime1.export_state()
    print("✅ 状态导出成功")
    
    # 创建第二个运行时
    runtime2 = create_runtime()
    print("✅ 运行时2创建成功")
    
    # 导入状态
    success = runtime2.import_state(state1)
    assert success == True
    print("✅ 状态导入成功")
    
    # 验证导入后的状态
    # 检查内存中的任务信息
    assert runtime2._runtime.short_term.get("task") == task
    print("✅ 任务信息导入成功")
    
    # 验证任务执行的文件是否存在
    test_file = "/home/claw/.openclaw/workspace/pyclaw/sandbox/workspace/test文件.txt"
    assert os.path.exists(test_file)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert content.strip() == "Hello, PyClaw!"
        
    print("✅ 文件内容验证成功")
    
    # 清理测试文件
    os.remove(test_file)
    print("✅ 测试文件清理成功")
    
    print("\n" + "=" * 60)
    print("🎉 状态导入导出测试成功")
    
    return True


def test_invalid_state_import():
    """测试无效状态导入"""
    print("\n🧪 测试无效状态导入")
    print("=" * 60)
    
    from pyclaw import create_runtime
    
    runtime = create_runtime()
    
    invalid_states = [
        "not_a_dict",
        {},
        {"task": "测试任务"},
        {"task_id": "20240503-134500"},
        {"task_id": "20240503-134500", "task": "测试任务"}
    ]
    
    all_failed = True
    
    for i, invalid_state in enumerate(invalid_states, 1):
        try:
            # 调用 import_state 并检查返回值
            result = runtime.import_state(invalid_state)
            if result:
                print(f"❌ 测试 {i} 失败: 无效状态被成功导入")
                all_failed = False
            else:
                print(f"✅ 测试 {i} 成功: 无效状态被正确拒绝")
        except Exception as e:
            print(f"✅ 测试 {i} 成功: 无效状态被正确拒绝 ({e})")
    
    return all_failed


def main():
    """主测试函数"""
    print("🏗️ 运行状态导入导出测试")
    
    try:
        success1 = test_state_import_export()
        success2 = test_invalid_state_import()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 所有状态导入导出测试通过")
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ 部分状态导入导出测试失败")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback
        print(f"堆栈信息: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
