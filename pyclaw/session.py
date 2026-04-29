"""
会话管理器 - 支持文件持久化，可指定存储路径
"""
import os
import json
import time
import uuid
from typing import Optional, List
from .pyclaw_types import Session, Message, MessageRole


class SessionManager:
    """会话管理器 - 负责创建、管理和销毁会话，支持文件持久化"""

    PERSIST_VERSION = 1

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化会话管理器

        Args:
            storage_path: 持久化文件路径（目录或文件皆可）。
                          若为目录，自动在目录下创建 pyclaw_sessions.json。
                          若为 None，则纯内存模式不持久化。
                          示例: "/home/claw/pyclaw_data/sessions.json" 或 "/home/claw/pyclaw_data/"
        """
        self._sessions: dict[str, Session] = {}
        self._storage_path = None
        self._dirty = False

        if storage_path:
            self._init_storage(storage_path)
            self._load()

    def _init_storage(self, path: str):
        """初始化存储文件路径"""
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, "pyclaw_sessions.json")

        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        self._storage_path = path

    def _serialize_message(self, msg: Message) -> dict:
        """序列化消息"""
        d = {
            "id": msg.id,
            "content": msg.content,
            "sender": msg.sender,
            "role": msg.role.value if isinstance(msg.role, MessageRole) else msg.role,
            "timestamp": msg.timestamp,
            "channel_id": msg.channel_id,
            "session_id": msg.session_id,
        }
        if msg.tool_call_id:
            d["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls:
            d["tool_calls"] = msg.tool_calls
        return d

    def _deserialize_message(self, d: dict) -> Message:
        """反序列化消息"""
        role = d.get("role")
        if isinstance(role, str):
            try:
                role = MessageRole(role)
            except ValueError:
                role = MessageRole.USER

        return Message(
            id=d.get("id", f"msg_{uuid.uuid4().hex[:8]}"),
            content=d.get("content", ""),
            sender=d.get("sender", ""),
            role=role,
            timestamp=d.get("timestamp", time.time()),
            channel_id=d.get("channel_id", ""),
            session_id=d.get("session_id", ""),
            tool_call_id=d.get("tool_call_id"),
            tool_calls=d.get("tool_calls"),
        )

    def _serialize_session(self, session: Session) -> dict:
        """序列化会话"""
        return {
            "id": session.id,
            "created_at": session.created_at,
            "last_active_at": session.last_active_at,
            "messages": [self._serialize_message(m) for m in session.messages],
            "metadata": session.metadata,
        }

    def _deserialize_session(self, d: dict) -> Session:
        """反序列化会话"""
        return Session(
            id=d.get("id", f"session_{uuid.uuid4().hex[:8]}"),
            created_at=d.get("created_at", time.time()),
            last_active_at=d.get("last_active_at", time.time()),
            messages=[self._deserialize_message(m) for m in d.get("messages", [])],
            metadata=d.get("metadata", {}),
        )

    def _load(self):
        """从文件加载会话"""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            sessions_data = data.get("sessions", {})
            for sid, sdata in sessions_data.items():
                self._sessions[sid] = self._deserialize_session(sdata)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 会话持久化文件读取失败，将使用空会话: {e}")

    def _save(self):
        """将会话保存到文件"""
        if not self._storage_path:
            return

        try:
            data = {
                "version": self.PERSIST_VERSION,
                "sessions": {
                    sid: self._serialize_session(s)
                    for sid, s in self._sessions.items()
                },
            }
            # 原子写入：先写临时文件再重命名，防止写了一半断电/红温
            tmp_path = self._storage_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._storage_path)
            self._dirty = False
        except (IOError, OSError) as e:
            print(f"⚠️ 会话持久化写入失败（U盘可能过热了）: {e}")

    def flush(self):
        """强制写入磁盘"""
        if self._dirty:
            self._save()

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """创建新会话"""
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        now = time.time()
        session = Session(
            id=session_id,
            created_at=now,
            last_active_at=now,
        )
        self._sessions[session_id] = session
        self._dirty = True
        return session

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """获取会话，不存在则创建"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_active_at = time.time()
            self._dirty = True
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
        self._dirty = True

    def get_history(self, session_id: str) -> List[Message]:
        """获取会话历史"""
        session = self.get(session_id)
        return session.messages.copy() if session else []

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._dirty = True
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

        if to_delete:
            self._dirty = True

        return len(to_delete)

    def list_sessions(self) -> List[str]:
        """获取所有会话ID"""
        return list(self._sessions.keys())
