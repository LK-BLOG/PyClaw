#!/usr/bin/env python3
"""
测试Runtime Trace System - 执行链可视化
"""
import sys
import time
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.bootstrap import bootstrap
from pyclaw.core.runtime import RuntimeState


def test_trace_system():
    print("=" * 80)
    print("🧪 Runtime Trace System 测试")
    print("=" * 80)

    # 启动系统（启用trace）
    print("🔧 1. 启动系统（启用执行链追踪）")
    runtime = bootstrap(trace=True)
    print("✅ 系统启动成功，执行链追踪已启用")
    print()

    # 设置任务
    print("🎯 2. 设置测试任务")
    test_task = "运行测试任务并记录执行链"
    runtime.set_task(test_task)
    print(f"✅ 任务: {test_task}")
    print()

    # 验证Trace系统已初始化
    assert runtime.trace_enabled, "执行链追踪未启用"
    assert runtime.trace is not None, "Trace对象未初始化"
    print("✅ 执行链追踪系统已初始化")
    print()

    # 执行任务直到完成
    print("🏃‍♂️ 3. 执行任务")
    print("-" * 60)

    results = []
    while runtime.state != RuntimeState.FINISHED and runtime.state != RuntimeState.ERROR:
        result = runtime.step()
        results.append(result)
        print(f"   Step {result.step}: {result.observation}")
        time.sleep(0.3)

    print("-" * 60)
    print()

    # 验证Trace记录
    print("📊 4. 验证Trace记录")
    print(f"   总记录数: {len(runtime.trace.records)}")
    assert len(runtime.trace.records) > 0, "未记录任何执行链信息"

    # 检查各个组件是否被记录到
    expected_components = ["planner", "tool", "evaluator", "memory"]
    recorded_layers = set()
    for record in runtime.trace.records:
        recorded_layers.add(record.layer)

    for component in expected_components:
        assert component in recorded_layers, f"{component}层未被记录"

    print("✅ 所有核心组件执行都已记录")
    print()

    # 保存Trace结果
    print("💾 5. 保存Trace结果")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"trace-{timestamp}.html"
    runtime.trace.save(filename)
    print(f"✅ 执行链可视化已保存到: {filename}")
    print()

    # 打印执行统计
    print("📈 6. 执行统计")
    print("=" * 60)
    print(f"任务: {test_task}")
    print(f"总步骤: {len(results)}")
    print(f"总记录数: {len(runtime.trace.records)}")
    print(f"任务状态: {runtime.state.value}")
    print()

    failed_steps = sum(1 for res in results if "失败" in res.observation)
    succeeded_steps = sum(1 for res in results if "成功" in res.observation)
    replans = sum(1 for res in results if "重规划" in res.observation)

    print(f"✅ 成功: {succeeded_steps}")
    print(f"❌ 失败: {failed_steps}")
    print(f"🔄 重规划: {replans}")
    print()

    # 打印各个组件的执行次数
    component_counts = {}
    for record in runtime.trace.records:
        component = record.component
        if component not in component_counts:
            component_counts[component] = 0
        component_counts[component] += 1

    print("组件执行次数:")
    for component, count in component_counts.items():
        print(f"  {component}: {count}次")
    print()

    print("🎉 Runtime Trace System 测试通过！")
    print("📋 下一步操作：在浏览器中打开生成的HTML文件查看可视化结果")
    print("=" * 80)


if __name__ == "__main__":
    test_trace_system()
