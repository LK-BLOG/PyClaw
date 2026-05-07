#!/usr/bin/env python3
"""
PyClaw USB版运行入口
支持状态保存和恢复，确保可移植性
"""
import os
import sys
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.memory.state_store import StateStore
from pyclaw.bootstrap import bootstrap
from pyclaw.core.runtime import RuntimeState


def main():
    print("=" * 50)
    print("🐉 PyClaw USB v1.0.0 - Portable AI Runtime")
    print("=" * 50)

    # 初始化状态存储
    state_store = StateStore()

    # 尝试加载之前的状态
    previous_state = state_store.load()

    if previous_state:
        print(f"🔄 检测到之前的状态，任务ID: {previous_state.get('task_id', 'unknown')}")
        print(f"📋 当前步骤: {previous_state.get('current_step', 0)}")

        # 询问是否要恢复
        choice = input("是否要恢复执行? (y/n, 默认n): ").strip().lower()
        if choice == "y" or choice == "yes":
            print("⏯️  正在恢复执行...")
            runtime = bootstrap(state=previous_state)
            # 直接启动运行循环
            run_runtime(runtime, state_store)
            return
        else:
            state_store.clear()
            print("🧹 已清除之前的状态")

    # 启动新会话
    runtime = bootstrap()

    print()
    print("🆕 新会话启动")

    # 获取任务
    while True:
        task_input = input("请输入任务: ").strip()

        if task_input.lower() in ["exit", "quit", "q"]:
            print("👋 退出程序")
            break

        if len(task_input) > 0:
            break
        else:
            print("⚠️  任务不能为空，请重新输入")

    print(f"\n📋 任务: {task_input}")
    print("-" * 50)

    # 设置任务并开始执行
    runtime.set_task(task_input)

    # 启动运行循环
    run_runtime(runtime, state_store)


def run_runtime(runtime, state_store):
    """
    运行Runtime循环，负责状态管理和任务执行
    """
    try:
        while runtime.state not in [RuntimeState.FINISHED, RuntimeState.WAITING_CONFIRM, RuntimeState.ERROR]:
            result = runtime.step()
            print(f"\n📍 Step {result.step}")
            print(f"   状态: {runtime.state.value}")
            print(f"   观察: {result.observation}")

            if result.intent:
                print(f"   意图: {result.intent}")
            if result.tool_result:
                print(f"   结果: {result.tool_result}")

            # 保存状态（每次步后都保存，确保可恢复）
            state_store.save(runtime.export_state())

            # 检查是否需要暂停
            if check_pause():
                break

        if runtime.state == RuntimeState.WAITING_CONFIRM:
            print("\n⏸️  需要用户确认，请手动继续")
            print(f"   待确认意图: {runtime.pending_intent}")
            choice = input("是否继续执行? (y/n, 默认n): ").strip().lower()

            if choice == "y" or choice == "yes":
                result = runtime.confirm(yes=True)
                print(f"✅ 确认后执行结果: {result}")
                run_runtime(runtime, state_store)

        elif runtime.state == RuntimeState.FINISHED:
            print("\n🎉 任务完成!")
            state_store.clear()

        elif runtime.state == RuntimeState.ERROR:
            print("\n❌ 执行过程中出错")

    except KeyboardInterrupt:
        print("\n⏸️  用户中断，正在保存状态...")
        state_store.save(runtime.export_state())
        print("✅ 状态已保存")

    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
        import traceback
        print("🔍 详细错误信息:")
        print(traceback.format_exc())
        # 尝试保存最后状态
        try:
            state_store.save(runtime.export_state())
            print("✅ 状态已保存")
        except:
            pass


def check_pause() -> bool:
    """
    检查是否需要暂停执行
    """
    import sys
    import select

    # 检查是否有输入（1秒超时）
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

    if rlist:
        char = sys.stdin.read(1)
        if char.lower() in ['p', 'q']:
            print("\n⏸️  暂停请求已收到")
            return True

    return False


if __name__ == "__main__":
    main()
