#!/usr/bin/env python3
"""
USB架构功能测试
验证沙箱化、状态存储和恢复功能
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.state_store import StateStore
from pyclaw.bootstrap import bootstrap


def test_sandbox():
    """测试沙箱化功能"""
    print("🧪 测试沙箱化功能")
    print("-" * 50)

    # 测试workspace目录是否自动创建
    if not os.path.exists("./pyclaw/sandbox/workspace"):
        print("❌ 工作区目录不存在")
        return False

    print("✅ 工作区目录已创建")

    # 测试安全路径验证
    test_cases = [
        ("./pyclaw/sandbox/workspace/test.txt", True, "允许访问"),
        ("test.txt", True, "相对路径访问"),
        ("/etc/passwd", False, "禁止访问系统目录"),
        ("../../../../../etc/passwd", False, "禁止访问上级目录"),
        ("C:/Windows/System32", False, "禁止访问Windows系统目录"),
    ]

    all_passed = True

    for path, should_succeed, description in test_cases:
        try:
            safe_path = FileGuard.safe_path(path)
            if should_succeed:
                print(f"✅ {description}: {path}")
            else:
                print(f"❌ {description}: {path} 应该被阻止，但成功了")
                all_passed = False
        except Exception as e:
            if not should_succeed:
                print(f"✅ {description}: {path}")
            else:
                print(f"❌ {description}: {path} 失败，错误: {e}")
                all_passed = False

    print()
    return all_passed


def test_state_store():
    """测试状态存储和加载"""
    print("🧪 测试状态存储和加载")
    print("-" * 50)

    state_store = StateStore()

    # 保存测试状态
    test_state = {
        "task_id": "test-12345",
        "task": "测试任务",
        "current_step": 3,
        "plan": [{"id": 1, "action": "read_file", "params": {"path": "test.txt"}}],
        "plan_index": 1,
        "replan_count": 0,
        "state": "executing",
        "memory": {"test_key": "test_value"}
    }

    try:
        state_store.save(test_state)
        print("✅ 状态保存成功")
    except Exception as e:
        print(f"❌ 状态保存失败: {e}")
        return False

    # 加载状态
    try:
        loaded_state = state_store.load()
        if loaded_state:
            print("✅ 状态加载成功")

            # 验证加载的状态
            assert loaded_state["task_id"] == test_state["task_id"]
            assert loaded_state["task"] == test_state["task"]
            assert loaded_state["current_step"] == test_state["current_step"]
            assert loaded_state["state"] == test_state["state"]

            print("✅ 状态内容验证通过")
        else:
            print("❌ 状态加载失败: 返回None")
            return False
    except Exception as e:
        print(f"❌ 状态加载失败: {e}")
        return False

    # 清除测试状态
    state_store.clear()
    print("✅ 状态清除成功")

    print()
    return True


def test_bootstrap():
    """测试启动过程"""
    print("🧪 测试启动过程")
    print("-" * 50)

    try:
        runtime = bootstrap()
        print("✅ Runtime初始化成功")

        # 检查是否有工具注册
        # 这里应该有至少3个工具
        handlers = len(runtime.intent_router.handlers)
        if handlers >= 3:
            print(f"✅ 工具链已注册 ({handlers}个工具)")
        else:
            print(f"⚠️  工具链数量不足 ({handlers}个)")

        return True
    except Exception as e:
        print(f"❌ Runtime初始化失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_agent_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能")
    print("-" * 50)

    try:
        # 启动Runtime
        runtime = bootstrap()
        runtime.set_task("测试工作区创建和文件操作")

        # 测试任务规划
        if len(runtime.current_plan) > 0:
            print(f"✅ 任务规划成功 (共 {len(runtime.current_plan)} 步)")
        else:
            print("❌ 任务规划失败")
            return False

        # 执行一步测试
        result = runtime.step()
        print("✅ 单步执行成功")
        print(f"   结果: {result.observation}")

        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def main():
    print("🎯 USB架构功能测试")
    print("=" * 50)

    tests = [
        ("沙箱化功能", test_sandbox),
        ("状态存储", test_state_store),
        ("系统启动", test_bootstrap),
        ("基本功能", test_agent_functionality),
    ]

    passed_count = 0
    total_count = len(tests)

    for test_name, test_func in tests:
        print()
        if test_func():
            passed_count += 1
        else:
            print(f"❌ 测试失败: {test_name}")

    print()
    print("=" * 50)
    print(f"📊 测试结果: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("🎉 所有测试通过！USB架构功能正常")
        return True
    else:
        print("⚠️  部分测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
