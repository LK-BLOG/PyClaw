"""
pyclaw/cancel.py — RunRegistry

按 session_id 索引的运行中任务注册表，用于支持：
- 硬停止：调 stop(session_id) -> 立刻设 stop_event
- 软插话：把消息 add_message 进 session，runner 每轮重新 get_history 自然读到

为什么 registry 里要存 asyncio.Task 引用：Web 那边 process_chat
被 create_task 启动，必要时可以 task.cancel() 兜底。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional
from collections import deque


@dataclass
class _Slot:
    task: asyncio.Task
    stop: asyncio.Event = field(default_factory=asyncio.Event)
    interject: Deque[str] = field(default_factory=deque)


class RunRegistry:
    def __init__(self) -> None:
        self._slots: Dict[str, _Slot] = {}

    def start(self, session_id: str, task: asyncio.Task) -> None:
        """注册一个运行中的任务。如果已有同 session 的任务在跑，先停掉旧的。"""
        old = self._slots.get(session_id)
        if old is not None:
            old.stop.set()
        self._slots[session_id] = _Slot(task=task)

    def stop(self, session_id: str) -> bool:
        """设置 stop_event。返回 True 表示真的有在跑的任务。"""
        slot = self._slots.get(session_id)
        if slot is None:
            return False
        slot.stop.set()
        return True

    def interject(self, session_id: str, text: str) -> bool:
        """记录一条插话文本（实际生效靠 add_message，这里只用于通知）。"""
        slot = self._slots.get(session_id)
        if slot is None:
            return False
        slot.interject.append(text)
        return True

    def is_running(self, session_id: str) -> bool:
        slot = self._slots.get(session_id)
        if slot is None:
            return False
        return not slot.task.done()

    def get_stop_event(self, session_id: str) -> Optional[asyncio.Event]:
        """给 runner 用 —— 拿到对应会话的 stop_event 传进去。"""
        slot = self._slots.get(session_id)
        return slot.stop if slot is not None else None

    def finish(self, session_id: str) -> None:
        """runner 跑完（或异常退出）时清理。"""
        self._slots.pop(session_id, None)


# 模块级单例
registry = RunRegistry()
