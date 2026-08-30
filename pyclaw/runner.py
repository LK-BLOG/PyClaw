"""
pyclaw/runner.py — 唯一一份「一轮 LLM + 工具执行」循环实现

四个调用方（webapp.process_chat / gateway.chat_text /
gateway._handle_message / SubAgent.execute）都消费这里的事件流。

历史补齐原则：被中断时，给已发出但未执行的 tool_call 补一条
"[已被用户中断]" 的 tool 消息，绝不删 assistant 消息 —— 否则下一轮
API 校验会因为 tool_calls 没有配对响应而报错。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections import deque
from typing import Any, AsyncGenerator, Deque, Dict, List, Optional, Set

from .pyclaw_types import Message, MessageRole, ToolCall


# ──────────────────────────────────────────────────────────────────
# 历史一致性
# ──────────────────────────────────────────────────────────────────
def sanitize_history(history: List[Message]) -> List[Message]:
    """清理脏历史：删除发出 tool_calls 但没有配对 tool 响应的 assistant 消息。

    正常使用流程下不应有脏消息（中断时会补齐），这段作为兜底，CLI 也共享。
    """
    cleaned: List[Message] = []
    i = 0
    while i < len(history):
        m = history[i]
        if m.role == MessageRole.ASSISTANT and m.tool_calls:
            needed = {
                tc.id if hasattr(tc, "id") else tc.get("id")
                for tc in m.tool_calls
            }
            found = set()
            for j in range(i + 1, len(history)):
                nxt = history[j]
                if nxt.role == MessageRole.TOOL and nxt.tool_call_id in needed:
                    found.add(nxt.tool_call_id)
            if found == needed:
                cleaned.append(m)
            # else 跳过 —— 脏消息丢弃（兜底，正常不应该到这里）
        else:
            cleaned.append(m)
        i += 1
    return cleaned


# ──────────────────────────────────────────────────────────────────
# 事件类型常量
# ──────────────────────────────────────────────────────────────────
EVT_THINKING = "thinking"
EVT_REASONING = "reasoning"
EVT_STREAM = "stream"
EVT_TOOL_CALL = "tool_call"
EVT_TOOL_RESULT = "tool_result"
EVT_AGENT_BUBBLE = "agent_bubble"
EVT_FINAL = "final"
EVT_STOPPED = "stopped"
EVT_ERROR = "error"


# ──────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────
def _new_msg_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _normalize_tool_calls(tcs: Any) -> List[Dict[str, Any]]:
    """把 LLM 返回的 tool_calls 列表统一成 [{id,name,arguments}, ...]"""
    out: List[Dict[str, Any]] = []
    for tc in tcs:
        if isinstance(tc, ToolCall):
            out.append({
                "id": tc.id,
                "name": tc.name,
                "arguments": tc.arguments or {},
            })
        elif isinstance(tc, dict):
            out.append({
                "id": tc.get("id"),
                "name": tc.get("name") or (tc.get("function") or {}).get("name", ""),
                "arguments": tc.get("arguments")
                if "arguments" in tc
                else (json.loads((tc.get("function") or {}).get("arguments") or "{}")
                      if (tc.get("function") or {}).get("arguments") else {}),
            })
    return out


def _make_interrupted_tool_msg(tool_call_id: str, channel_id: str,
                               session_id: str) -> Message:
    """给已发出但被中断的 tool_call 补一条合成的 tool 响应消息。"""
    return Message(
        id=_new_msg_id("tool"),
        content="[已被用户中断]",
        sender="tool",
        role=MessageRole.TOOL,
        timestamp=0,
        channel_id=channel_id,
        session_id=session_id,
        tool_call_id=tool_call_id,
    )


# ──────────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────────
async def run_agent(
    agent,
    session_manager,
    session_id: str,
    *,
    channel_id: str = "cli",
    stream: bool = True,
    stop_event: Optional[asyncio.Event] = None,
    interject_queue: Optional[Deque[Message]] = None,
    allowed_tools: Optional[Set[str]] = None,
    initial_message: Optional[Message] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """异步生成器：消费方按事件渲染。

    Args:
        agent: Agent 实例（提供 stream_chat / chat / execute_tool）
        session_manager: SessionManager（提供 get_history / add_message / flush）
        session_id: 会话 ID
        channel_id: 写入 Message.channel_id 用的标签
        stream: True=用 stream_chat（Web/CLI 都要 True 才能边打边渲）
        stop_event: 设置后本 runner 下一检查点会优雅退出
        interject_queue: 不使用 —— 软插话直接走 add_message 即可
        allowed_tools: 限制可用工具（SubAgent 用）
        initial_message: 已经写好历史里的新 user 消息（gateway.chat_text 走这里）
    """
    if initial_message is not None:
        session_manager.add_message(session_id, initial_message)
        session_manager.flush()

    max_rounds = getattr(agent, "max_rounds", 300)

    # 把 stream_chat / chat 二选一
    if stream and hasattr(agent, "stream_chat"):
        chat = lambda hist: agent.stream_chat(hist)  # noqa: E731
    else:
        async def _chat(hist):
            r = await agent.chat(hist)
            yield r
        chat = _chat

    for round_idx in range(max_rounds):
        # 取消检查点 1：每轮开头
        if stop_event is not None and stop_event.is_set():
            yield {"type": EVT_STOPPED, "reason": "user_requested", "partial": ""}
            return

        history = sanitize_history(session_manager.get_history(session_id))

        yield {"type": EVT_THINKING, "round": round_idx + 1}

        full_content = ""
        full_reasoning = ""
        tool_calls_payload: List[Dict[str, Any]] = []
        final_response = None
        err_msg: Optional[str] = None

        try:
            async for chunk in chat(history):
                # 取消检查点 2：每个 chunk 后 —— 唯一能做到「打断正在输出的文字」的位置
                if stop_event is not None and stop_event.is_set():
                    break

                if not chunk.success:
                    err_msg = chunk.error or "unknown error"
                    break

                if chunk.reasoning_content:
                    full_reasoning += chunk.reasoning_content
                    if not chunk.content:
                        # reasoning-only chunk：单独派发 EVT_REASONING 给前端
                        yield {"type": EVT_REASONING, "delta": chunk.reasoning_content}

                if chunk.content:
                    if not chunk.tool_calls:
                        full_content += chunk.content
                    yield {"type": EVT_STREAM, "delta": chunk.content}

                if chunk.tool_calls:
                    tool_calls_payload = _normalize_tool_calls(chunk.tool_calls)
                    final_response = chunk
                    break
        except asyncio.CancelledError:
            # 上层 cancel（比如 SubAgent 父层停止）
            yield {"type": EVT_STOPPED, "reason": "cancelled", "partial": full_content}
            return
        except Exception as e:
            yield {"type": EVT_ERROR, "message": f"LLM call failed: {e}"}
            return

        if stop_event is not None and stop_event.is_set():
            # 中断点：保存已流出的部分 + 给已发出 tool_calls 补响应
            if full_content:
                assistant_msg = Message(
                    id=_new_msg_id("assist"),
                    content=full_content,
                    sender="assistant",
                    role=MessageRole.ASSISTANT,
                    timestamp=0,
                    channel_id=channel_id,
                    session_id=session_id,
                    reasoning_content=full_reasoning or None,
                )
                session_manager.add_message(session_id, assistant_msg)
            for tc in tool_calls_payload:
                session_manager.add_message(
                    session_id,
                    _make_interrupted_tool_msg(tc["id"], channel_id, session_id),
                )
            session_manager.flush()
            yield {"type": EVT_STOPPED, "reason": "user_requested",
                   "partial": full_content}
            return

        if err_msg:
            yield {"type": EVT_ERROR, "message": err_msg}
            return

        if not tool_calls_payload:
            # 正常结束
            if full_content:
                assistant_msg = Message(
                    id=_new_msg_id("assist"),
                    content=full_content,
                    sender="assistant",
                    role=MessageRole.ASSISTANT,
                    timestamp=0,
                    channel_id=channel_id,
                    session_id=session_id,
                    reasoning_content=full_reasoning or None,
                )
                session_manager.add_message(session_id, assistant_msg)
                session_manager.flush()
            yield {"type": EVT_FINAL, "content": full_content}
            return

        # 有 tool_calls：保存 assistant 消息（含 tool_calls + reasoning）
        assistant_msg = Message(
            id=_new_msg_id("assist"),
            content=full_content,
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=0,
            channel_id=channel_id,
            session_id=session_id,
            tool_calls=[
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls_payload
            ],
            reasoning_content=full_reasoning or None,
        )
        session_manager.add_message(session_id, assistant_msg)

        # 取消检查点 3：工具执行之前
        if stop_event is not None and stop_event.is_set():
            for tc in tool_calls_payload:
                session_manager.add_message(
                    session_id,
                    _make_interrupted_tool_msg(tc["id"], channel_id, session_id),
                )
            session_manager.flush()
            yield {"type": EVT_STOPPED, "reason": "user_requested",
                   "partial": full_content}
            return

        # 并发执行所有工具
        tasks = [agent.execute_tool(_to_tc(tc), allowed_tools)
                 for tc in tool_calls_payload]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 派发事件 + 落盘
        for tc, result in zip(tool_calls_payload, results):
            if isinstance(result, Exception):
                result_str = f"Tool exception: {result}"
            else:
                result_str = str(result) if result else ""

            # delegate_to / delegate_tmp：作为子代理气泡单独派发
            if tc["name"] in ("delegate_to", "delegate_tmp"):
                args = tc["arguments"] or {}
                bubble_name = args.get("agent") or args.get("name") or "subagent"
                yield {
                    "type": EVT_AGENT_BUBBLE,
                    "agent": bubble_name,
                    "content": result_str,
                }
            else:
                yield {
                    "type": EVT_TOOL_CALL,
                    "name": tc["name"],
                    "id": tc["id"],
                    "arguments": tc["arguments"],
                }
                yield {
                    "type": EVT_TOOL_RESULT,
                    "id": tc["id"],
                    "name": tc["name"],
                    "content": result_str,
                }

            # 所有工具结果都必须落盘（包括 delegate）
            session_manager.add_message(
                session_id,
                Message(
                    id=_new_msg_id("tool"),
                    content=result_str,
                    sender="tool",
                    role=MessageRole.TOOL,
                    timestamp=0,
                    channel_id=channel_id,
                    session_id=session_id,
                    tool_call_id=tc["id"],
                ),
            )

        session_manager.flush()


def _to_tc(d: Dict[str, Any]) -> ToolCall:
    return ToolCall(id=d["id"], name=d["name"], arguments=d.get("arguments") or {})
