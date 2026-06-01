"""
PyClaw 测试共享夹具
"""
import os
import sys
import tempfile
import uuid
from datetime import datetime

import pytest

# 确保 pyclaw 包在测试路径中
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))


# ── 基础夹具 ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_message_data():
    """提供一份标准消息数据"""
    import time
    from pyclaw.pyclaw_types import Message, MessageRole
    return Message(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        content="你好",
        sender="user",
        role=MessageRole.USER,
        timestamp=time.time(),
        channel_id="test_channel",
        session_id="test_session",
    )


@pytest.fixture
def sample_tool_call_data():
    """提供一份工具调用数据"""
    from pyclaw.pyclaw_types import ToolCall
    return ToolCall(
        id=f"call_{uuid.uuid4().hex[:8]}",
        name="read_file",
        arguments={"file_path": "/tmp/test.txt"}
    )


@pytest.fixture
def sample_tool_definition():
    """提供一份工具定义"""
    from pyclaw.pyclaw_types import ToolDefinition
    return ToolDefinition(
        name="test_tool",
        description="测试工具",
        parameters={
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "输入"}
            },
            "required": ["input"]
        }
    )


@pytest.fixture
def temp_session_file():
    """创建临时会话文件路径，测试结束后清理"""
    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, "test_sessions.json")
    yield filepath
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_memory_db():
    """创建临时记忆数据库路径"""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_memory.db")
    yield db_path
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
