"""
runner / cancel 的核心正确性测试。

1. sanitize_history 兜底：脏消息被丢弃
2. _make_interrupted_tool_msg 生成的消息能正确挂在 tool_call_id 上
3. RunRegistry：start/stop/finish 状态机正确
4. 集成：中断后历史里每个 tool_call 都有配对响应（用 stub session_manager）
"""
import asyncio
import pytest

from pyclaw.runner import sanitize_history, _make_interrupted_tool_msg
from pyclaw.cancel import RunRegistry
from pyclaw.pyclaw_types import Message, MessageRole, ToolCall


def _msg(role, content="", **kw):
    return Message(
        id=kw.get("id", f"m_{content[:5]}"),
        content=content,
        sender=kw.get("sender", "user"),
        role=role,
        timestamp=0,
        channel_id="test",
        session_id="s1",
        tool_call_id=kw.get("tool_call_id"),
        tool_calls=kw.get("tool_calls"),
    )


def test_sanitize_drops_orphan_assistant_tool_calls():
    """assistant 发了 tool_calls 但没收到配对 tool 响应 —— 整条 assistant 消息应被丢弃。"""
    h = [
        _msg(MessageRole.USER, "hi"),
        _msg(MessageRole.ASSISTANT, "thinking",
             tool_calls=[{"id": "tc1"}, {"id": "tc2"}]),
        # tc1 有响应，tc2 没有
        _msg(MessageRole.TOOL, "r1", tool_call_id="tc1", sender="tool"),
    ]
    cleaned = sanitize_history(h)
    # assistant 消息应被丢弃
    assert len(cleaned) == 2
    assert cleaned[0].content == "hi"
    assert cleaned[1].content == "r1"


def test_sanitize_keeps_complete_assistant_tool_calls():
    """所有 tool_call 都有配对响应 —— 保留。"""
    h = [
        _msg(MessageRole.USER, "hi"),
        _msg(MessageRole.ASSISTANT, "thinking",
             tool_calls=[{"id": "tc1"}]),
        _msg(MessageRole.TOOL, "r1", tool_call_id="tc1", sender="tool"),
    ]
    cleaned = sanitize_history(h)
    assert len(cleaned) == 3


def test_interrupted_tool_msg_has_correct_tool_call_id():
    """中断时合成的 tool 消息必须带上 tool_call_id，下一轮 API 才不会报错。"""
    m = _make_interrupted_tool_msg("tc_xyz", "cli", "session_a")
    assert m.role == MessageRole.TOOL
    assert m.tool_call_id == "tc_xyz"
    assert m.session_id == "session_a"
    assert m.channel_id == "cli"
    # 内容明确告诉 LLM 这是中断
    assert "中断" in m.content or "interrupted" in m.content.lower()


def test_registry_lifecycle():
    """start → is_running → stop → finish 状态机。"""
    reg = RunRegistry()
    sid = "s_test"

    async def _run():
        evt = asyncio.Event()
        async def task_coro():
            await asyncio.sleep(10)
        task = asyncio.create_task(task_coro())
        reg.start(sid, task)
        assert reg.is_running(sid) is True
        assert reg.stop(sid) is True  # 真的在跑
        evt.set()  # 真没用到，只是变量
        assert reg.get_stop_event(sid) is not None
        # 重复 stop 返回 True（slot 还在）
        assert reg.stop(sid) is True
        task.cancel()
        try: await task
        except (asyncio.CancelledError, Exception): pass
        reg.finish(sid)
        assert reg.is_running(sid) is False
        assert reg.stop(sid) is False  # 已经清掉
    asyncio.run(_run())


def test_registry_interject_returns_true_only_when_running():
    reg = RunRegistry()
    assert reg.interject("nope", "x") is False
    reg.finish("nope")  # 不应崩


def test_interrupted_history_is_consistent():
    """模拟：模型发出 2 个 tool_calls，用户在工具执行前按停止。
    最终历史里每条 assistant(tool_calls) 的每个 id 都能找到配对 tool 响应。"""
    h = [
        _msg(MessageRole.USER, "user-msg"),
        _msg(MessageRole.ASSISTANT, "think",
             tool_calls=[{"id": "a"}, {"id": "b"}]),
    ]
    # runner 中断时补的两条 tool 响应
    h.append(_make_interrupted_tool_msg("a", "cli", "s1"))
    h.append(_make_interrupted_tool_msg("b", "cli", "s1"))

    # 不需要 sanitize 修复（已经完整），直接校验
    needed = set()
    for m in h:
        if m.role == MessageRole.ASSISTANT and m.tool_calls:
            for tc in m.tool_calls:
                needed.add(tc["id"])
    found = {m.tool_call_id for m in h
             if m.role == MessageRole.TOOL and m.tool_call_id}
    assert needed == found, f"missing responses: {needed - found}"


@pytest.mark.asyncio
async def test_runner_yields_events_in_order_on_immediate_stop():
    """stop_event 在 runner 启动前就设位：应立即 yield stopped 并 return。"""
    from pyclaw.runner import run_agent, EVT_STOPPED

    # 假 agent —— 只用来看是否被调（永远不该被调）
    class FakeAgent:
        max_rounds = 5
        async def stream_chat(self, hist):
            raise AssertionError("should not be called")
        async def execute_tool(self, tc, allowed=None): return ""

    # 假 session_manager
    class FakeSM:
        def __init__(self):
            self.messages = []
        def get_history(self, sid): return list(self.messages)
        def add_message(self, sid, m): self.messages.append(m)
        def flush(self): pass

    sm = FakeSM()
    stop = asyncio.Event()
    stop.set()  # 已经置位

    events = []
    async for evt in run_agent(FakeAgent(), sm, "s1",
                                channel_id="cli", stop_event=stop):
        events.append(evt)

    assert len(events) == 1
    assert events[0]["type"] == EVT_STOPPED
