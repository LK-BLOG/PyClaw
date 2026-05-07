#!/usr/bin/env python3
"""
执行链追踪测试 - 验证架构每一层是否真的在运行
"""
import sys
import time
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.bootstrap import bootstrap
from pyclaw.core.runtime import RuntimeState


def test_execution_trace():
    print("=" * 80)
    print("🧪 Execution Trace Test - 验证PyClaw v0.7.2架构执行链")
    print("=" * 80)

    # 启动系统
    print("🔧 1. 启动系统")
    runtime = bootstrap()
    print("✅ 系统启动成功")
    print()

    # 设置任务
    print("🎯 2. 设置测试任务")
    test_task = "运行详细测试"
    runtime.set_task(test_task)
    print(f"✅ 任务: {test_task}")
    print()

    # 验证Planner是否真的拆了任务
    print("📋 3. 验证任务拆解（Planner层）")
    print(f"   总步骤数: {len(runtime.current_plan)}")
    assert len(runtime.current_plan) > 0, "Planner未生成任务计划"

    for i, step in enumerate(runtime.current_plan, 1):
        print(f"   步骤 {i}:")
        print(f"     动作: {step.action}")
        print(f"     描述: {step.description}")
        print(f"     参数: {step.params}")
    print("✅ Planner任务拆解正常")
    print()

    # 验证执行链
    print("🏃‍♂️ 4. 执行并追踪每一步（Runtime层）")
    print("-" * 60)

    results = []
    while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR:
        result = runtime.step()
        results.append(result)

        print(f"   Step {result.step}:")
        print(f"     状态: {runtime.state.value}")
        print(f"     观察: {result.observation}")
        if result.intent:
            print(f"     动作: {result.intent.type.value}")
        if result.tool_result:
            print(f"     结果: {result.tool_result}")
        print()

        time.sleep(0.3)

    print("-" * 60)
    print()

    # 验证Evaluator是否真的评估了每一步
    print("📊 5. 验证评估结果（Evaluator层）")
    if any("失败" in res.observation for res in results) or any("成功" in res.observation for res in results):
        print("✅ Evaluator工作正常（成功/失败标记已显示）")
    else:
        print("⚠️  Evaluator可能未正确标记执行结果")

    # 验证Memory是否真的记录了
    print("💾 6. 验证Memory记录")
    memory_data = runtime.short_term.all()
    print(f"   记录条目数: {len(memory_data)}")
    assert len(memory_data) > 1, "Memory记录过少"

    has_task_record = any(key == "task" for key in memory_data)
    has_step_records = any(key.startswith("step_") for key in memory_data)

    assert has_task_record, "Memory未记录任务信息"
    assert has_step_records, "Memory未记录步骤执行信息"

    print("✅ Memory记录完整")
    print()

    # 输出执行报告
    print("📈 7. 执行报告")
    print("=" * 60)
    print(f"任务: {test_task}")
    print(f"总步骤: {len(results)}")
    print(f"状态: {runtime.state.value}")
    print()

    failed_steps = sum(1 for res in results if "失败" in res.observation)
    succeeded_steps = sum(1 for res in results if "成功" in res.observation)
    replans = sum(1 for res in results if "重规划" in res.observation)

    print(f"✅ 成功: {succeeded_steps}")
    print(f"❌ 失败: {failed_steps}")
    print(f"🔄 重规划: {replans}")
    print()

    if runtime.state == RuntimeState.FINISHED:
        print("🎉 执行链追踪测试通过！")
    else:
        print("⚠️  测试未完全成功，请检查输出")

    print("=" * 80)


if __name__ == "__main__":
    test_execution_trace()
