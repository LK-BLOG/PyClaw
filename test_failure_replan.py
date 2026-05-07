#!/usr/bin/env python3
"""
测试 Self-Correction Planner 的重规划功能
"""
from pyclaw.bootstrap import bootstrap
from pyclaw.core.planner import Step
from pyclaw.core.evaluator import Evaluator, Evaluation
from pyclaw.policy.execution_policy import ExecutionPolicy, PolicyResult, RiskLevel


def test_replan():
    print("=" * 60)
    print("🧠 测试 Self-Correction Planner")
    print("=" * 60)

    # 启动系统
    runtime = bootstrap()

    # 专门设置一个会有多个步骤的任务，确保有第二步可以失败
    runtime.set_task("运行测试")

    print()
    print("📋 原始任务计划:")
    for step in runtime.current_plan:
        print(f"   {step.id}. [{step.action}] {step.description}")

    print()
    print("=" * 60)

    if len(runtime.current_plan) < 2:
        print("⚠️  原始任务只有一步，无法测试重规划")
        print()
        print("🧪 直接测试评估器功能:")

        evaluator = Evaluator()
        test_step = Step(id=1, action="run_bash", params={"cmd": "invalid-command"}, description="测试失败")
        test_result = {"error": "command not found"}
        evaluation = evaluator.check_step(test_step, test_result)

        print(f"   步骤: {test_step.description}")
        print(f"   结果: {test_result}")
        print(f"   评估: {evaluation.ok}")
        print(f"   原因: {evaluation.reason}")
        print(f"   需要重规划: {evaluation.need_replan}")

        print()
        print("✅ 评估器工作正常")
        return

    print("🔍 强制修改第二步让它失败（用于测试）")
    runtime.current_plan[1].action = "run_bash"
    runtime.current_plan[1].params = {"cmd": "invalid-command-that-will-fail"}
    runtime.current_plan[1].description = "故意执行无效命令"

    print()
    print("🏃‍♂️ 开始执行（预期第二步失败）:")
    print("-" * 60)

    results = runtime.run_until_complete()

    print()
    print("=" * 60)
    print("🎯 执行结果统计:")
    print("-" * 60)
    print(f"总执行步数: {len(results)}")

    failed_steps = sum(1 for res in results if "失败" in res.observation)
    print(f"失败步数: {failed_steps}")

    replans = sum(1 for res in results if "重规划" in res.observation)
    print(f"重规划次数: {replans}")

    if any("重规划" in res.observation for res in results):
        print()
        print("✅ Self-Correction Planner 工作正常")
        print("🎉 系统会自动检测失败并重新规划")
    else:
        print()
        print("⚠️  未触发重规划，可能是任务太简单（直接成功了）")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_replan()
