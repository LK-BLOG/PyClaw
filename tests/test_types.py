"""
测试 PyClaw 核心类型定义
- Message: 消息对象序列化和枚举
- ToolDefinition: 工具定义转字典
- ToolCall: 工具调用
- ToolResult: 工具结果
- AgentResponse: Agent 响应
"""
import time
import uuid
import json


class TestMessageRole:
    """测试消息角色枚举"""

    def test_values(self):
        from pyclaw.pyclaw_types import MessageRole
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.TOOL.value == "tool"

    def test_from_string(self):
        from pyclaw.pyclaw_types import MessageRole
        assert MessageRole("user") == MessageRole.USER
        assert MessageRole("assistant") == MessageRole.ASSISTANT
        assert MessageRole("system") == MessageRole.SYSTEM
        assert MessageRole("tool") == MessageRole.TOOL

    def test_invalid_string_raises(self):
        from pyclaw.pyclaw_types import MessageRole
        import pytest
        with pytest.raises(ValueError):
            MessageRole("invalid_role")


class TestMessage:
    """测试消息对象"""

    def test_create_basic(self):
        from pyclaw.pyclaw_types import Message, MessageRole
        msg = Message(
            id="msg_001",
            content="测试消息",
            sender="user",
            role=MessageRole.USER,
            timestamp=1000.0,
            channel_id="ch_1",
            session_id="sess_1",
        )
        assert msg.id == "msg_001"
        assert msg.content == "测试消息"
        assert msg.sender == "user"
        assert msg.role == MessageRole.USER
        assert msg.timestamp == 1000.0
        assert msg.channel_id == "ch_1"
        assert msg.session_id == "sess_1"
        # 可选字段默认值
        assert msg.tool_call_id is None
        assert msg.tool_calls is None
        assert msg.reasoning_content is None

    def test_with_tool_call_id(self):
        from pyclaw.pyclaw_types import Message, MessageRole
        msg = Message(
            id="msg_002",
            content='{"result": "ok"}',
            sender="tool",
            role=MessageRole.TOOL,
            timestamp=2000.0,
            channel_id="ch_1",
            session_id="sess_1",
            tool_call_id="call_abc123",
        )
        assert msg.tool_call_id == "call_abc123"

    def test_with_tool_calls(self):
        from pyclaw.pyclaw_types import Message, MessageRole, ToolCall
        tool_calls = [
            ToolCall(id="call_1", name="read_file", arguments={"file_path": "/tmp/a.txt"}),
            ToolCall(id="call_2", name="exec_command", arguments={"command": "ls"}),
        ]
        msg = Message(
            id="msg_003",
            content="",
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=3000.0,
            channel_id="ch_1",
            session_id="sess_1",
            tool_calls=tool_calls,
        )
        assert len(msg.tool_calls) == 2
        assert msg.tool_calls[0].name == "read_file"
        assert msg.tool_calls[1].arguments["command"] == "ls"

    def test_with_reasoning(self):
        from pyclaw.pyclaw_types import Message, MessageRole
        msg = Message(
            id="msg_004",
            content="最终答案",
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=4000.0,
            channel_id="ch_1",
            session_id="sess_1",
            reasoning_content="思考过程...",
        )
        assert msg.reasoning_content == "思考过程..."

    def test_default_timestamp(self):
        """timestamp 没有默认值，所以必须传入"""
        from pyclaw.pyclaw_types import Message, MessageRole
        msg = Message(
            id="msg_005",
            content="test",
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="ch_1",
            session_id="sess_1",
        )
        assert msg.timestamp > 0


class TestToolDefinition:
    """测试工具定义"""

    def test_create(self, sample_tool_definition):
        assert sample_tool_definition.name == "test_tool"
        assert sample_tool_definition.description == "测试工具"
        assert "input" in sample_tool_definition.parameters["properties"]

    def test_to_dict(self, sample_tool_definition):
        d = sample_tool_definition.to_dict()
        assert d["type"] == "function"
        assert d["function"]["name"] == "test_tool"
        assert d["function"]["description"] == "测试工具"
        assert d["function"]["parameters"]["type"] == "object"
        assert "input" in d["function"]["parameters"]["properties"]

    def test_to_dict_json_serializable(self, sample_tool_definition):
        """to_dict 结果应可 JSON 序列化"""
        d = sample_tool_definition.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_multiple_properties(self):
        from pyclaw.pyclaw_types import ToolDefinition
        td = ToolDefinition(
            name="multi_tool",
            description="多种参数",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "count": {"type": "integer"},
                    "enabled": {"type": "boolean"},
                },
                "required": ["name"]
            }
        )
        d = td.to_dict()
        props = d["function"]["parameters"]["properties"]
        assert set(props.keys()) == {"name", "count", "enabled"}


class TestToolCall:
    """测试工具调用"""

    def test_create(self, sample_tool_call_data):
        assert sample_tool_call_data.name == "read_file"
        assert sample_tool_call_data.arguments["file_path"] == "/tmp/test.txt"
        assert sample_tool_call_data.id.startswith("call_")

    def test_with_json_arguments(self):
        from pyclaw.pyclaw_types import ToolCall
        tc = ToolCall(
            id="call_xyz",
            name="exec_command",
            arguments={"command": "ls -la", "timeout": 30}
        )
        assert tc.arguments["command"] == "ls -la"
        assert tc.arguments["timeout"] == 30

    def test_empty_arguments(self):
        from pyclaw.pyclaw_types import ToolCall
        tc = ToolCall(
            id="call_empty",
            name="get_current_time",
            arguments={}
        )
        assert tc.arguments == {}


class TestToolResult:
    """测试工具结果"""

    def test_success_result(self):
        from pyclaw.pyclaw_types import ToolResult
        result = ToolResult(success=True, content="操作成功")
        assert result.success is True
        assert result.content == "操作成功"
        assert result.error is None
        assert result.conversation_note is None

    def test_failure_result(self):
        from pyclaw.pyclaw_types import ToolResult
        result = ToolResult(success=False, content="", error="文件不存在")
        assert result.success is False
        assert result.error == "文件不存在"

    def test_with_conversation_note(self):
        from pyclaw.pyclaw_types import ToolResult
        result = ToolResult(
            success=True,
            content="已读取",
            conversation_note="注意：文件中有敏感信息"
        )
        assert result.conversation_note == "注意：文件中有敏感信息"


class TestAgentResponse:
    """测试 Agent 响应"""

    def test_success(self):
        from pyclaw.pyclaw_types import AgentResponse
        resp = AgentResponse(
            success=True,
            content="你好",
            prompt_tokens=100,
            completion_tokens=50,
        )
        assert resp.success is True
        assert resp.content == "你好"
        assert resp.prompt_tokens == 100
        assert resp.completion_tokens == 50
        assert resp.error is None
        assert resp.tool_calls == []
        assert resp.reasoning_content is None

    def test_failure(self):
        from pyclaw.pyclaw_types import AgentResponse
        resp = AgentResponse(
            success=False,
            content="",
            error="API 请求失败: 401",
        )
        assert resp.success is False
        assert resp.error == "API 请求失败: 401"

    def test_with_tool_calls(self):
        from pyclaw.pyclaw_types import AgentResponse, ToolCall
        resp = AgentResponse(
            success=True,
            content="",
            tool_calls=[
                ToolCall(id="call_1", name="read_file", arguments={"file_path": "/tmp/x.txt"}),
            ],
        )
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "read_file"

    def test_with_reasoning(self):
        from pyclaw.pyclaw_types import AgentResponse
        resp = AgentResponse(
            success=True,
            content="最终答案",
            reasoning_content="推理过程...",
        )
        assert resp.reasoning_content == "推理过程..."
