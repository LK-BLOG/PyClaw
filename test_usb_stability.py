#!/usr/bin/env python3
"""
PyClaw USB架构稳定性测试套件
包含三个关键点的测试：
1. 干净运行测试（clean run test）
2. 状态恢复测试（state resume test）
3. 沙箱隔离测试（sandbox isolation test）
"""
import sys
import os
import subprocess
import time

sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.state_store import StateStore
from pyclaw.bootstrap import bootstrap
from pyclaw.core.runtime import RuntimeState


def test_clean_run():
    """测试1: 干净运行测试"""
    print("🧪 测试1: 干净运行测试")
    print("-" * 50)

    state_store = StateStore()
    state_store.clear()

    try:
        # 创建临时测试脚本
        test_script = """
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')
from pyclaw.bootstrap import bootstrap
from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.state_store import StateStore
from pyclaw.core.runtime import RuntimeState

# 启动
runtime = bootstrap()

# 设置任务
test_task = "创建一个临时测试文件，内容是'Clean run test'"
runtime.set_task(test_task)

# 执行任务
while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR:
    runtime.step()

# 验证文件创建
result = FileGuard.file_exists("temp_test.txt")

if result:
    content = FileGuard.read_text("temp_test.txt")
    if "Clean run test" in content:
        print("✅ 任务执行成功，文件内容正确")
    else:
        print(f"❌ 文件内容错误: {content}")

    FileGuard.remove_file("temp_test.txt")
else:
    print("❌ 文件未创建")

print(f"任务状态: {runtime.state}")
"""

        with open("temp_test_run.py", "w") as f:
            f.write(test_script)

        # 运行测试
        result = subprocess.run(
            [sys.executable, "temp_test_run.py"],
            capture_output=True,
            text=True
        )

        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)

        # 检查是否成功执行
        assert "任务状态: RuntimeState.FINISHED" in result.stdout
        print("✅ 干净运行测试通过")
        return True

    except Exception as e:
        print(f"❌ 干净运行测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists("temp_test_run.py"):
            os.remove("temp_test_run.py")
        if FileGuard.file_exists("temp_test.txt"):
            FileGuard.remove_file("temp_test.txt")
        state_store.clear()


def test_state_resume():
    """测试2: 状态恢复测试"""
    print("🧪 测试2: 状态恢复测试")
    print("-" * 50)

    state_store = StateStore()
    state_store.clear()

    try:
        # 1. 创建一个会多步执行的任务
        runtime = bootstrap()
        complex_task = "创建一个名为complex.txt的文件，写入内容'Line 1\nLine 2\nLine 3'，然后读取该文件"
        runtime.set_task(complex_task)

        print(f"任务规划: {len(runtime.current_plan)} 步")
        for i, step in enumerate(runtime.current_plan, 1):
            print(f"  步骤 {i}: {step.action}")

        # 确保任务规划正确
        assert len(runtime.current_plan) > 1
        print("任务规划包含多步骤，适合进行恢复测试")

        # 2. 执行前几步
        steps_to_execute = 1  # 只执行1步，确保任务未完成
        for i in range(steps_to_execute):
            if runtime.state != RuntimeState.FINISHED:
                result = runtime.step()
                print(f"步骤 {i+1}: {result.observation}")

        # 确保任务未完成
        assert runtime.state != RuntimeState.FINISHED
        print(f"执行了 {steps_to_execute} 步后状态: {runtime.state}")

        # 3. 保存状态
        state_store.save(runtime.export_state())

        # 4. 模拟kill并重新启动
        print("\n模拟程序重启...")
        del runtime
        time.sleep(0.1)

        # 5. 恢复状态
        saved_state = state_store.load()
        assert saved_state is not None
        print(f"从状态文件中恢复任务ID: {saved_state.get('task_id')}")

        # 6. 恢复执行
        runtime = bootstrap(saved_state)

        # 7. 继续执行任务
        while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR:
            result = runtime.step()
            print(f"恢复后步骤: {result.observation}")

        print(f"最终状态: {runtime.state}")

        # 8. 验证任务完成
        assert runtime.state == RuntimeState.FINISHED
        print("✅ 状态恢复测试通过")
        return True

    except Exception as e:
        print(f"❌ 状态恢复测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        if FileGuard.file_exists("complex.txt"):
            FileGuard.remove_file("complex.txt")
        state_store.clear()


def test_sandbox_isolation():
    """测试3: 沙箱隔离测试"""
    print("🧪 测试3: 沙箱隔离测试")
    print("-" * 50)

    state_store = StateStore()
    state_store.clear()

    try:
        runtime = bootstrap()

        # 测试1: 尝试访问系统文件
        print("测试系统文件访问拦截...")
        test_path = "/etc/passwd"
        try:
            safe_path = FileGuard.safe_path(test_path)
            print(f"❌ 文件访问未被正确拦截: {safe_path}")
        except Exception as e:
            print(f"✅ 系统文件访问被正确拦截: {e}")

        # 测试2: 尝试访问USB外文件
        print("\n测试USB外文件访问拦截...")
        test_path = "../test_outsider.txt"
        try:
            safe_path = FileGuard.safe_path(test_path)
            print(f"❌ 文件访问未被正确拦截: {safe_path}")
        except Exception as e:
            print(f"✅ USB外文件访问被正确拦截: {e}")

        # 测试3: 验证只能在workspace内创建文件
        print("\n测试文件创建范围限制...")
        valid_path = "valid_test_file.txt"
        invalid_path = "../../invalid_file.txt"

        # 有效路径
        result = FileGuard.write_text(valid_path, "Test content")
        assert result
        assert FileGuard.file_exists(valid_path)

        FileGuard.read_text(valid_path)
        FileGuard.remove_file(valid_path)
        assert not FileGuard.file_exists(valid_path)

        print("✅ 有效路径文件操作成功")

        # 无效路径
        try:
            FileGuard.write_text(invalid_path, "This should fail")
            print("❌ 无效路径文件创建未被拦截")
            return False
        except Exception as e:
            print(f"✅ 无效路径文件操作被正确拦截: {e}")

        print("✅ 沙箱隔离测试通过")
        return True

    except Exception as e:
        print(f"❌ 沙箱隔离测试失败: {e}")
        return False
    finally:
        if FileGuard.file_exists("valid_test_file.txt"):
            FileGuard.remove_file("valid_test_file.txt")
        state_store.clear()


def main():
    print("🎯 PyClaw USB架构稳定性测试套件")
    print("=" * 50)

    tests = [
        ("干净运行", test_clean_run),
        ("状态恢复", test_state_resume),
        ("沙箱隔离", test_sandbox_isolation)
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print()
        if test_func():
            passed += 1
            print(f"✅ {name}测试通过")
        else:
            print(f"❌ {name}测试失败")

    print()
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有稳定性测试通过！PyClaw USB架构稳定可用")
        return 0
    else:
        print("⚠️  部分稳定性测试失败，请检查并修复问题")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
