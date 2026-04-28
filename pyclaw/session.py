"""
会话管理器
"""
import time
import uuid
from typing import Optional, List
from .pyclaw_types import Session, Message


class SessionManager:
    """会话管理器 - 负责创建、管理和销毁会话"""
    
    def __init__(self):
        self._sessions: dict[str, Session] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """创建新会话"""
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        now = time.time()
        session = Session(
            id=session_id,
            created_at=now,
            last_active_at=now
        )
        self._sessions[session_id] = session
        return session
    
    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """获取会话，不存在则创建"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_active_at = time.time()
            return session
        return self.create_session(session_id)
    
    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def add_message(self, session_id: str, message: Message) -> None:
        """添加消息到会话"""
        session = self.get_or_create(session_id)
        session.messages.append(message)
        session.last_active_at = time.time()
    
    def get_history(self, session_id: str) -> List[Message]:
        """获取会话历史"""
        session = self.get(session_id)
        return session.messages.copy() if session else []
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_inactive(self, max_age_seconds: int = 3600) -> int:
        """清理不活跃的会话"""
        now = time.time()
        to_delete = []
        
        for session_id, session in self._sessions.items():
            if now - session.last_active_at > max_age_seconds:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self._sessions[session_id]
        
        return len(to_delete)
    
    def list_sessions(self) -> List[str]:
        """获取所有会话ID"""
        return list(self._sessions.keys())
