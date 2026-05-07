"""
Agent 运行时 - 负责与LLM交互
"""
import json
from typing import List, Dict, Any, Optional
import httpx
from .types import Message, AgentResponse, ToolCall, Tool, MessageRole


class Agent:
    """AI代理运行时"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "glm-4-flash"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.tools: Dict[str, Tool] = {}
        self.system_prompt = "你是一个有用的AI助手。"
    
    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.definition.name] = tool
    
    def _build_messages(self, history: List[Message]) -> List[Dict[str, Any]]:
        """构建发送给LLM的消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for msg in history:
            if msg.role == MessageRole.TOOL:
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        return messages
    
    def _build_tools_definition(self) -> List[Dict[str, Any]]:
        """构建工具定义"""
        if not self.tools:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.definition.name,
                    "description": tool.definition.description,
                    "parameters": tool.definition.parameters
                }
            }
            for tool in self.tools.values()
        ]
    
    async def chat(self, history: List[Message]) -> AgentResponse:
        """与LLM对话"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": self._build_messages(history),
        }
        
        tools_def = self._build_tools_definition()
        if tools_def:
            payload["tools"] = tools_def
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return self._parse_response(data)
    
    def _parse_response(self, data: Dict[str, Any]) -> AgentResponse:
        """解析LLM响应"""
        choice = data["choices"][0]
        message = choice["message"]
        
        content = message.get("content", "")
        tool_calls = []
        
        if "tool_calls" in message and message["tool_calls"]:
            for tc in message["tool_calls"]:
                try:
                    params = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, KeyError):
                    params = {}
                
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=tc["function"]["name"],
                    parameters=params
                ))
        
        return AgentResponse(content=content, tool_calls=tool_calls)
    
    async def execute_tool(self, tool_call: ToolCall) -> Optional[str]:
        """执行工具调用"""
        if tool_call.name not in self.tools:
            return f"错误: 找不到工具 {tool_call.name}"
        
        tool = self.tools[tool_call.name]
        result = await tool.execute(tool_call.parameters)
        
        if result.success:
            return result.content
        return f"工具执行失败: {result.error}"
