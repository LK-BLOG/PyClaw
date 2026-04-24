"""
PyClaw 类型定义
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Protocol
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """消息对象"""
    id: str
    content: str
    sender: str
    role: MessageRole
    timestamp: float
    channel_id: str
    session_id: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Any]] = None  # 保存完整的 tool_calls 用于 API 格式校验


@dataclass
class Session:
    """会话对象"""
    id: str
    created_at: float
    last_active_at: float
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 API 调用"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]  # 统一用 arguments，与 OpenAI API 一致


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    content: str
    error: Optional[str] = None


class Channel(Protocol):
    """Channel 接口协议"""
    id: str
    name: str
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def on_message(self, callback: Callable[[Message], None]) -> None: ...
    async def send_message(self, session_id: str, content: str) -> None: ...


class Tool(Protocol):
    """Tool 接口协议"""
    definition: ToolDefinition
    async def execute(self, params: Dict[str, Any]) -> ToolResult: ...


@dataclass
class AgentResponse:
    """Agent 响应"""
    success: bool
    content: str
    error: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
