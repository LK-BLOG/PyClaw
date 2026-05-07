"""
PyClaw USB版启动器
负责初始化整个系统，包括状态恢复和组件注册
"""
from pyclaw.policy.execution_policy import ExecutionPolicy
from pyclaw.core.runtime import AgentRuntime
from pyclaw.tools.file_tool import FileTool
from pyclaw.tools.write_file_tool import WriteFileTool
from pyclaw.tools.bash_tool import BashTool
from pyclaw.tools.python_tool import PythonTool
from pyclaw.tools.finish_tool import FinishTool


def bootstrap(state=None) -> AgentRuntime:
    """
    初始化整个PyClaw系统
    :param state: 之前的执行状态，用于恢复执行
    :return: 初始化后的Runtime实例
    """
    print("🚀 正在启动PyClaw USB Runtime...")

    # 1. 初始化Policy层 - 安全控制
    policy = ExecutionPolicy()
    print("✅ 安全策略层初始化完成")

    # 2. 初始化Runtime - 执行引擎
    runtime = AgentRuntime(llm_client=None, trace=True, state=state)
    print("✅ 运行时引擎初始化完成")

    # 3. 注册工具 - 沙箱化工具链
    runtime.register_tool(FileTool())
    runtime.register_tool(WriteFileTool())
    runtime.register_tool(BashTool())
    runtime.register_tool(PythonTool())
    runtime.register_tool(FinishTool())
    print("✅ 沙箱化工具链注册完成")

    # 4. 如果有状态，恢复执行上下文
    if state:
        print("📋 状态恢复完成")
        print(f"   任务: {state.get('task', 'Unknown')}")
        print(f"   当前步骤: {state.get('current_step', 0)}")
        print(f"   状态: {state.get('state', 'Unknown')}")

    print("🎉 PyClaw USB Runtime启动成功")
    return runtime
