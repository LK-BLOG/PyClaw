"""
共享子代理委派工具：delegate_to（预置） + delegate_tmp（一次性临时）
"""
from typing import Dict, Any
from .pyclaw_types import ToolDefinition, ToolResult


class DelegateToTool:
    """委派任务给预置子代理（exec/file/search/browser/app）"""

    def __init__(self, mgr):
        self.mgr = mgr

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delegate_to",
            description="委派任务给子代理执行。exec:命令 file:文件 search:搜索 browser:浏览器 app:桌面",
            parameters={
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "enum": ["exec", "file", "search", "browser", "app"], "description": "目标子代理"},
                    "task": {"type": "string", "description": "要委派的任务描述"}
                },
                "required": ["agent", "task"]
            }
        )

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        agent_name = params.get("agent", "")
        task = params.get("task", "")
        if not agent_name or not task:
            return ToolResult(success=False, content="", error="需要 agent 和 task 参数")
        result = await self.mgr.delegate(agent_name, task)
        return ToolResult(success=True, content=str(result))


class DelegateTmpTool:
    """现场创建一次性临时子代理，用完即焚不缓存，可递归"""

    def __init__(self, mgr):
        self.mgr = mgr

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delegate_tmp",
            description="现场创建一次性临时子代理并委派任务，用完即焚不缓存。name: 临时子代理名称(自定义) tools: 允许使用的工具名数组(可含 delegate_tmp 实现递归，深度上限5) task: 任务描述。tools 传空数组时创建纯推理代理。",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "临时子代理名称"},
                    "tools": {"type": "array", "items": {"type": "string"}, "description": "允许使用的工具名数组，可为空"},
                    "task": {"type": "string", "description": "要委派的任务描述"}
                },
                "required": ["name", "tools", "task"]
            }
        )

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "")
        tools = params.get("tools", []) or []
        task = params.get("task", "")
        if not name or not task:
            return ToolResult(success=False, content="", error="需要 name、tools、task 参数")
        result = await self.mgr.delegate_tmp(name, tools, task)
        return ToolResult(success=True, content=str(result))
