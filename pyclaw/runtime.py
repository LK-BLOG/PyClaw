"""
PyClaw USB 运行时封装（API Freeze）

这是 PyClaw 的唯一运行时入口，负责：
1. 封装内部核心运行时
2. 提供统一的对外接口
3. 管理系统状态
4. 执行任务

禁止直接访问内部 core/runtime.py。
"""

from .core.runtime import AgentRuntime as _Runtime, RuntimeState
from .core.planner import Step


class AgentRuntime:
    """
    PyClaw USB 运行时（API Freeze）
    
    这是系统的唯一对外运行时接口，所有任务执行必须通过此接口。
    """
    
    def __init__(self, state=None, registry=None):
        """
        初始化运行时
        
        参数：
            state: 可选的状态数据，用于恢复运行时
            registry: 注册中心实例
        """
        self._runtime = _Runtime(state=state)
        self.registry = registry
        
        # 内部组件引用
        self._intent_parser = None
        self._planner = None
        self._evaluator = None
        
        # 初始化系统组件
        self._initialize_components()
        
    def _initialize_components(self):
        """初始化内部组件"""
        from .core.intent_parser import IntentParser
        from .core.planner import Planner
        from .core.evaluator import Evaluator
        
        self._intent_parser = IntentParser()
        self._planner = Planner(self._intent_parser)
        self._evaluator = Evaluator()
        
        # 注册核心工具
        self._register_core_tools()
        
    def _register_core_tools(self):
        """注册核心工具"""
        from .tools.write_file_tool import WriteFileTool
        from .tools.file_tool import FileTool
        from .tools.bash_tool import BashTool
        from .tools.python_tool import PythonTool
        from .tools.finish_tool import FinishTool
        
        self._runtime.register_tool(WriteFileTool())
        self._runtime.register_tool(FileTool())
        self._runtime.register_tool(BashTool())
        self._runtime.register_tool(PythonTool())
        self._runtime.register_tool(FinishTool())
        
    def run(self, task: str):
        """
        唯一执行入口（冻结 API）
        
        参数：
            task: 自然语言任务描述
            
        返回：
            任务执行结果
        """
        self._runtime.set_task(task)
        return self._runtime.run_until_complete()
        
    def export_state(self):
        """导出系统状态"""
        return self._runtime.export_state()
        
    def import_state(self, state):
        """导入系统状态（用于恢复运行）"""
        try:
            # 状态验证
            if not isinstance(state, dict):
                raise TypeError("状态必须是字典类型")
                
            required_fields = ["task_id", "export_timestamp", "task", "current_step"]
            for field in required_fields:
                if field not in state:
                    raise ValueError(f"状态缺失必填字段: {field}")
            
            # 恢复任务
            self._runtime.set_task(state["task"])
            
            # 恢复内部状态
            if "plan" in state and state["plan"]:
                self._runtime.current_plan = []
                for step_data in state["plan"]:
                    step = Step(
                        id=step_data.get("id", 0),
                        action=step_data.get("action", "finish_task"),
                        params=step_data.get("params", {}),
                        description=step_data.get("description", "")
                    )
                    self._runtime.current_plan.append(step)
            
            if "plan_index" in state:
                self._runtime.plan_index = state["plan_index"]
                
            if "replan_count" in state:
                self._runtime.replan_count = state["replan_count"]
            
            if "current_step" in state:
                self._runtime.step_count = state["current_step"]
            
            # 恢复记忆
            if "memory" in state and state["memory"]:
                self._runtime.short_term.clear()
                for key, value in state["memory"].items():
                    self._runtime.short_term.add(key, value)
            
            # 恢复任务状态
            if "state" in state:
                # 这里需要将字符串状态转换为 RuntimeState 枚举
                # 为了简单，我们直接使用状态字符串
                state_map = {
                    "idle": RuntimeState.IDLE,
                    "thinking": RuntimeState.THINKING,
                    "executing": RuntimeState.EXECUTING,
                    "waiting_confirm": RuntimeState.WAITING_CONFIRM,
                    "finished": RuntimeState.FINISHED,
                    "error": RuntimeState.ERROR
                }
                
                if state["state"] in state_map:
                    self._runtime.state = state_map[state["state"]]
            
            print(f"✅ 状态恢复成功 (任务ID: {state['task_id']})")
            return True
            
        except Exception as e:
            print(f"❌ 状态恢复失败: {e}")
            import traceback
            print(f"堆栈信息: {traceback.format_exc()}")
            return False
        
    @property
    def state(self):
        """获取当前运行时状态"""
        return self._runtime.state
        
    @property
    def step_count(self):
        """获取已执行的步骤数"""
        return self._runtime.step_count
        
    def __repr__(self):
        return f"PyClaw USB Runtime<state={self.state.value}, steps={self.step_count}>"
