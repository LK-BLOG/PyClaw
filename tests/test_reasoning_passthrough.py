"""
回归测试：DeepSeek thinking 模式下 reasoning_content 必须回传。

现象：第二轮起报 400 'reasoning_content in the thinking mode must be passed back'
原因：serialize_history 时普通 assistant 消息漏掉 reasoning_content 字段

覆盖：
1. 普通 assistant 消息（无 tool_calls）必须带 reasoning_content 字段
2. thinking=True 模式下，history 中所有 assistant 都要有 reasoning_content 字段
3. 老 session 没有 reasoning_content 的消息，序列化时也得有字段（哪怕是 ""）
"""
import pytest
from pyclaw.pyclaw_types import Message, MessageRole
from pyclaw.agent import Agent


def _msg(role, content, **kw):
    return Message(
        id=kw.get("id", f"m_{content[:5]}"),
        content=content,
        sender=kw.get("sender", "user" if role == MessageRole.USER else "assistant"),
        role=role,
        timestamp=0,
        channel_id="cli",
        session_id="s_test",
        tool_call_id=kw.get("tool_call_id"),
        tool_calls=kw.get("tool_calls"),
        reasoning_content=kw.get("reasoning_content"),
    )


def test_plain_assistant_serializes_reasoning_content():
    """无 tool_calls 的普通 assistant 消息也要带 reasoning_content。"""
    agent = Agent(api_key="dummy", base_url="http://x", model="m")
    h = [
        _msg(MessageRole.USER, "hi"),
        _msg(MessageRole.ASSISTANT, "hello", reasoning_content="我思考了"),
    ]
    out = agent._build_messages(h)
    assert out[2]["role"] == "assistant"
    assert "reasoning_content" in out[2]
    assert out[2]["reasoning_content"] == "我思考了"


def test_thinking_mode_pads_missing_reasoning():
    """thinking=True 时，序列化兜底：所有 assistant 都要有 reasoning_content 字段。"""
    agent = Agent(api_key="dummy", base_url="http://x", model="m")
    agent._thinking = True
    h = [
        _msg(MessageRole.USER, "hi"),
        # 老消息：没 reasoning_content
        _msg(MessageRole.ASSISTANT, "old reply"),
    ]
    out = agent._build_messages(h)
    assert out[2]["role"] == "assistant"
    assert "reasoning_content" in out[2]
    # 兜底给空串
    assert out[2]["reasoning_content"] == ""


def test_thinking_disabled_no_padding_needed():
    """thinking=False 时不强制补字段。"""
    agent = Agent(api_key="dummy", base_url="http://x", model="m")
    agent._thinking = False
    h = [
        _msg(MessageRole.USER, "hi"),
        _msg(MessageRole.ASSISTANT, "ok"),
    ]
    out = agent._build_messages(h)
    # thinking off：不强制补
    assert "reasoning_content" not in out[2] or out[2].get("reasoning_content") is None
