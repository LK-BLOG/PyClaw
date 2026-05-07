# PyClaw USB v1.1 API Freeze Layer

## 🎯 目标

实现 PyClaw USB 的 API 冻结层，确保系统架构稳定，消除模块边界和导入体系混乱问题，使系统进入工业级稳定状态。

## 🏗️ 架构变更

### 1. 统一系统入口

**文件**：`pyclaw/__init__.py`

```python
from .runtime import AgentRuntime
from .registry import Registry

# 🧠 全局单例注册中心
registry = Registry()

def create_runtime(state=None):
    """
    USB Agent 唯一启动入口（冻结 API）
    
    参数：
        state: 可选的状态数据，用于恢复运行时
    
    返回：
        AgentRuntime 实例
    """
    return AgentRuntime(state=state, registry=registry)

__all__ = [
    "create_runtime",
    "AgentRuntime",
    "registry"
]
```

### 2. 全局注册中心

**文件**：`pyclaw/registry.py`

```python
class Registry:
    """
    系统组件注册表（单例模式）
    
    管理：
    - 工具（Tools）
    - 规划器（Planners）
    - 评估器（Evaluators）
    """
    def __init__(self):
        self.tools = {}
        self.planners = {}
        self.evaluators = {}
        
    def register_tool(self, name, tool):
        self.tools[name] = tool
        
    def get_tool(self, name):
        return self.tools.get(name)
        
    # 其他管理方法...
```

### 3. Runtime 封装

**文件**：`pyclaw/runtime.py`

```python
from .core.runtime import AgentRuntime as _Runtime

class AgentRuntime:
    """
    PyClaw USB 运行时（API Freeze）
    
    这是系统的唯一对外运行时接口，所有任务执行必须通过此接口。
    """
    
    def __init__(self, state=None, registry=None):
        self._runtime = _Runtime(state=state)
        self.registry = registry
        self._initialize_components()
        
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
        return self._runtime.export_state()
```

### 4. 组件初始化

**在 runtime.py 中**：

```python
def _initialize_components(self):
    from .core.intent_parser import IntentParser
    from .core.planner import Planner
    from .core.evaluator import Evaluator
    
    self._intent_parser = IntentParser()
    self._planner = Planner(self._intent_parser)
    self._evaluator = Evaluator()
    
    self._register_core_tools()
    
def _register_core_tools(self):
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
```

## 🎯 使用规范

### 禁止行为

❌ 直接导入内部模块
```python
# 禁止
from core.runtime import AgentRuntime
from pyclaw.tools import write_file_tool
```

❌ 直接实例化 core 层类
```python
# 禁止
runtime = pyclaw.core.runtime.AgentRuntime()
```

❌ 绕过 registry 访问系统组件
```python
# 禁止
tool = FileTool()
```

### 正确用法

✅ 通过统一入口创建运行时
```python
from pyclaw import create_runtime

runtime = create_runtime()
results = runtime.run("你的任务")
```

✅ 访问注册中心
```python
from pyclaw import registry

# 访问工具
tool = registry.get_tool("write_file")

# 访问规划器
planner = registry.get_planner("default")
```

## 📊 测试结果

### 1. API Freeze 架构测试

✅ 导入路径规范验证
✅ 运行时创建成功
✅ 内部组件初始化成功
✅ 任务执行流程正常
✅ 文件操作功能正常

### 2. 执行契约验证测试

✅ 计划验证成功
✅ 无效计划验证失败（预期行为）
✅ 工具执行契约验证成功
✅ 实际执行过程中的契约验证通过

### 3. 简单功能测试

✅ 系统正常运行
✅ 任务解析正确
✅ 文件操作正常
✅ 多种任务类型测试通过

## 🎉 结果

PyClaw USB 已成功升级到 v1.1 API Freeze 版本：

### 阶段跃迁

v0.7.2 → 能跑但结构不稳  
v1.0 → API Freeze（当前）  
v1.1 → 系统稳定  

### 改进效果

✅ 入口唯一  
✅ 模块隔离  
✅ 可替换组件  
✅ 测试稳定  
✅ USB可迁移  

### 下一步建议

系统现已进入稳定状态，可以继续开发：
- Plugin化 Tool System（USB v1.2）
- 外部能力扩展
- 系统优化和功能增强
