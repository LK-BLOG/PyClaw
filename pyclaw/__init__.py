"""
PyClaw USB版 - 统一入口（API Freeze）

这是 PyClaw USB 的唯一对外暴露入口，所有功能必须通过此处访问。

API 规范（冻结）：
- create_runtime() - 创建运行时实例
- AgentRuntime - 运行时类（不建议直接实例化）
- registry - 全局注册中心

禁止行为：
- 直接 import core.*
- 直接 import tools.*
- 直接实例化 core 层类
- 绕过 registry 访问系统组件
"""

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
