"""
PyClaw USB 会话管理器

负责管理多个会话实例，每个会话有独立的运行时状态和上下文。
支持通过会话ID进行会话的创建、获取、删除和状态管理。
"""

import uuid
from typing import Dict, Any, Optional
from pyclaw import create_runtime


class SessionManager:
    """PyClaw USB 会话管理器"""

    def __init__(self):
        self._sessions: Dict[str, Any] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        创建一个新的会话

        参数：
            session_id: 可选的会话ID，不提供则自动生成

        返回：
            会话ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            raise ValueError(f"会话ID {session_id} 已存在")

        runtime = create_runtime()
        self._sessions[session_id] = runtime
        return session_id

    def get_session(self, session_id: str) -> Any:
        """
        获取指定ID的会话

        参数：
            session_id: 会话ID

        返回：
            会话对象

        抛出：
            KeyError: 会话不存在
        """
        if session_id not in self._sessions:
            raise KeyError(f"会话ID {session_id} 不存在")
        return self._sessions[session_id]

    def delete_session(self, session_id: str) -> None:
        """
        删除指定ID的会话

        参数：
            session_id: 会话ID

        抛出：
            KeyError: 会话不存在
        """
        if session_id not in self._sessions:
            raise KeyError(f"会话ID {session_id} 不存在")
        del self._sessions[session_id]

    def list_sessions(self) -> list:
        """
        获取所有会话的ID列表

        返回：
            会话ID列表
        """
        return list(self._sessions.keys())

    def get_session_count(self) -> int:
        """
        获取会话数量

        返回：
            会话数量
        """
        return len(self._sessions)

    def clear_all_sessions(self) -> None:
        """
        清除所有会话
        """
        self._sessions.clear()


# 全局会话管理器实例
_global_session_manager = None


def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器实例（单例模式）

    返回：
        全局会话管理器实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
