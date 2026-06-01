"""
测试会话管理器 (SessionManager)
- 创建/获取/删除会话
- 添加/读取消息
- 序列化与反序列化
- 文件持久化
- 不活跃会话清理
"""
import os
import time
import pytest


class TestSessionManagerBasics:
    """测试 SessionManager 基本功能"""

    def test_create_session(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        session = mgr.create_session()
        assert session.id is not None
        assert len(session.messages) == 0
        assert session.created_at > 0
        assert session.last_active_at > 0

    def test_create_session_with_id(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        session = mgr.create_session("my_session")
        assert session.id == "my_session"

    def test_get_existing_session(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        mgr.create_session("sess_1")
        session = mgr.get("sess_1")
        assert session is not None
        assert session.id == "sess_1"

    def test_get_nonexistent_session(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        session = mgr.get("does_not_exist")
        assert session is None

    def test_get_or_create_existing(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        created = mgr.create_session("sess_1")
        fetched = mgr.get_or_create("sess_1")
        assert fetched.id == created.id

    def test_get_or_create_new(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        session = mgr.get_or_create("new_sess")
        assert session.id == "new_sess"

    def test_delete_session(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        mgr.create_session("delete_me")
        assert mgr.delete_session("delete_me") is True
        assert mgr.get("delete_me") is None

    def test_delete_nonexistent(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        assert mgr.delete_session("ghost") is False

    def test_list_sessions(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        mgr.create_session("a")
        mgr.create_session("b")
        mgr.create_session("c")
        sessions = mgr.list_sessions()
        assert len(sessions) == 3
        assert set(sessions) == {"a", "b", "c"}

    def test_duplicate_create_returns_existing(self):
        """重复调用 create_session 应返回已有会话，不覆盖"""
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        s1 = mgr.create_session("dup")
        s2 = mgr.create_session("dup")
        assert s1.id == s2.id
        # 确认是同一个对象
        assert mgr.get("dup") is s1


class TestSessionMessages:
    """测试消息管理"""

    def test_add_message(self):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr = SessionManager()
        mgr.create_session("sess_msg")

        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="测试消息",
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="ch",
            session_id="sess_msg",
        )
        mgr.add_message("sess_msg", msg)
        history = mgr.get_history("sess_msg")
        assert len(history) == 1
        assert history[0].content == "测试消息"

    def test_add_message_auto_creates_session(self):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr = SessionManager()
        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="自动创建",
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="ch",
            session_id="auto_sess",
        )
        mgr.add_message("auto_sess", msg)
        session = mgr.get("auto_sess")
        assert session is not None
        assert len(session.messages) == 1

    def test_multiple_messages(self):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr = SessionManager()
        for i in range(5):
            msg = Message(
                id=f"msg_{i}",
                content=f"消息{i}",
                sender="user",
                role=MessageRole.USER,
                timestamp=time.time() + i,
                channel_id="ch",
                session_id="sess_multi",
            )
            mgr.add_message("sess_multi", msg)

        history = mgr.get_history("sess_multi")
        assert len(history) == 5
        assert history[0].content == "消息0"
        assert history[4].content == "消息4"

    def test_get_history_returns_copy(self):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr = SessionManager()
        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="test",
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="ch",
            session_id="sess",
        )
        mgr.add_message("sess", msg)
        history = mgr.get_history("sess")
        history.append("mutated")  # 修改副本不应影响原数据
        assert len(mgr.get_history("sess")) == 1

    def test_tool_message(self):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr = SessionManager()
        tool_msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content='{"result": "ok"}',
            sender="tool",
            role=MessageRole.TOOL,
            timestamp=time.time(),
            channel_id="ch",
            session_id="sess_tool",
            tool_call_id="call_abc",
        )
        mgr.add_message("sess_tool", tool_msg)
        history = mgr.get_history("sess_tool")
        assert history[0].tool_call_id == "call_abc"


class TestSessionSerialization:
    """测试序列化与反序列化"""

    def test_serialize_deserialize_roundtrip(self, temp_session_file):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole, ToolCall

        # 创建带数据的会话
        mgr1 = SessionManager(temp_session_file)
        mgr1.create_session("sess_1")

        # 添加普通消息
        msg1 = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="用户消息",
            sender="user",
            role=MessageRole.USER,
            timestamp=1000.0,
            channel_id="ch",
            session_id="sess_1",
        )
        mgr1.add_message("sess_1", msg1)

        # 添加工具调用消息
        tool_calls = [
            ToolCall(id="call_1", name="read_file", arguments={"file_path": "/tmp/x.txt"})
        ]
        msg2 = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="",
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=2000.0,
            channel_id="ch",
            session_id="sess_1",
            tool_calls=tool_calls,
        )
        mgr1.add_message("sess_1", msg2)

        # 添加工具结果
        msg3 = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="文件内容",
            sender="tool",
            role=MessageRole.TOOL,
            timestamp=3000.0,
            channel_id="ch",
            session_id="sess_1",
            tool_call_id="call_1",
        )
        mgr1.add_message("sess_1", msg3)

        # 强制写入
        mgr1.flush()

        # 重新加载
        mgr2 = SessionManager(temp_session_file)
        session = mgr2.get("sess_1")
        assert session is not None
        assert session.id == "sess_1"
        assert len(session.messages) == 3

        # 验证内容
        assert session.messages[0].content == "用户消息"
        assert session.messages[0].role.value == "user"

        assert session.messages[1].content == ""
        assert session.messages[1].role.value == "assistant"
        assert len(session.messages[1].tool_calls) == 1
        assert session.messages[1].tool_calls[0].name == "read_file"

        assert session.messages[2].content == "文件内容"
        assert session.messages[2].role.value == "tool"
        assert session.messages[2].tool_call_id == "call_1"

    def test_persist_version_in_file(self, temp_session_file):
        import json
        from pyclaw.session import SessionManager
        mgr = SessionManager(temp_session_file)
        mgr.create_session("v_test")
        mgr.flush()

        with open(temp_session_file, "r") as f:
            data = json.load(f)
        assert data["version"] == 1

    def test_load_empty_file(self, temp_session_file):
        """不存在的文件应正常加载为空"""
        from pyclaw.session import SessionManager
        mgr = SessionManager(temp_session_file)
        # 文件还不存在，应正常初始化
        assert mgr.list_sessions() == []

    def test_corrupted_file(self, temp_session_file):
        """损坏的文件应优雅降级"""
        from pyclaw.session import SessionManager
        # 写非法 JSON
        with open(temp_session_file, "w") as f:
            f.write("这不是 JSON{")
        mgr = SessionManager(temp_session_file)
        # 应该能创建新会话
        mgr.create_session("after_corruption")
        assert mgr.get("after_corruption") is not None

    def test_atomic_write(self, temp_session_file):
        """原子写入不应留下临时文件"""
        from pyclaw.session import SessionManager
        mgr = SessionManager(temp_session_file)
        mgr.create_session("atomic_test")
        mgr.flush()
        # 临时文件应已被清理
        tmp_path = temp_session_file + ".tmp"
        assert not os.path.exists(tmp_path)

    def test_serialize_message_with_reasoning(self, temp_session_file):
        import time
        import uuid
        from pyclaw.session import SessionManager
        from pyclaw.pyclaw_types import Message, MessageRole

        mgr1 = SessionManager(temp_session_file)
        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            content="答案",
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=time.time(),
            channel_id="ch",
            session_id="sess_reason",
            reasoning_content="思考过程",
        )
        mgr1.add_message("sess_reason", msg)
        mgr1.flush()

        mgr2 = SessionManager(temp_session_file)
        session = mgr2.get("sess_reason")
        assert session.messages[0].reasoning_content == "思考过程"


class TestSessionCleanup:
    """测试不活跃会话清理"""

    def test_cleanup_inactive(self):
        import time
        from pyclaw.session import SessionManager

        mgr = SessionManager()
        mgr.create_session("active")
        mgr.create_session("stale_1")
        mgr.create_session("stale_2")

        # 模拟 stale 会话很早以前活跃
        import time as t
        mgr.get("stale_1").last_active_at = t.time() - 10000
        mgr.get("stale_2").last_active_at = t.time() - 10000

        deleted = mgr.cleanup_inactive(max_age_seconds=3600)
        assert deleted == 2
        assert mgr.get("active") is not None
        assert mgr.get("stale_1") is None
        assert mgr.get("stale_2") is None

    def test_cleanup_all(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        mgr.create_session("a")
        mgr.create_session("b")
        # last_active_at = time.time() (刚刚创建)
        deleted = mgr.cleanup_inactive(max_age_seconds=0)
        assert deleted == 2

    def test_no_stale_sessions(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        mgr.create_session("a")
        mgr.create_session("b")
        deleted = mgr.cleanup_inactive(max_age_seconds=86400)
        assert deleted == 0


class TestSessionEdgeCases:
    """边界情况"""

    def test_storage_path_as_file(self, temp_session_file):
        """测试直接传文件路径"""
        from pyclaw.session import SessionManager
        mgr = SessionManager(temp_session_file)
        mgr.create_session("path_test")
        mgr.flush()
        assert os.path.exists(temp_session_file)

    def test_storage_path_as_directory(self):
        """测试传目录路径"""
        import tempfile
        import shutil
        tmpdir = tempfile.mkdtemp()
        try:
            from pyclaw.session import SessionManager
            mgr = SessionManager(tmpdir)
            mgr.create_session("dir_test")
            mgr.flush()
            expected = os.path.join(tmpdir, "pyclaw_sessions.json")
            assert os.path.exists(expected)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_empty_history_for_nonexistent_session(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        history = mgr.get_history("ghost")
        assert history == []

    def test_last_active_at_updated_on_get_or_create(self):
        from pyclaw.session import SessionManager
        mgr = SessionManager()
        s1 = mgr.create_session("sess_active")
        old_time = s1.last_active_at
        import time
        time.sleep(0.01)
        mgr.get_or_create("sess_active")
        assert mgr.get("sess_active").last_active_at > old_time
