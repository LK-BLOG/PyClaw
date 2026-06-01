"""
测试记忆系统 (MemoryManager)
- 全局记忆增删查
- 会话级记忆
- 记忆搜索
- 系统提示词附加
- 缓存机制
"""
import os
import pytest


class TestMemoryManagerBasics:
    """测试记忆管理器基本操作"""

    def test_add_global_memory(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mem_id = mgr.add_global_memory("test_key", "测试值")
        assert mem_id > 0

    def test_get_global_memory(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("user_name", "骆戡")
        value = mgr.get_global_memory("user_name")
        assert value == "骆戡"

    def test_get_nonexistent_memory(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        value = mgr.get_global_memory("不存在")
        assert value is None

    def test_update_existing_memory(self, temp_memory_db):
        """更新已存在的记忆（相同 key）"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("key1", "旧值")
        mgr.add_global_memory("key1", "新值")
        value = mgr.get_global_memory("key1")
        assert value == "新值"

    def test_list_global_memories(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("k1", "v1", importance=5)
        mgr.add_global_memory("k2", "v2", importance=3)
        mgr.add_global_memory("k3", "v3", importance=7)

        memories = mgr.list_global_memories()
        assert len(memories) == 3

    def test_list_ordered_by_importance(self, temp_memory_db):
        """记忆应按重要性降序排列"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("low", "不重要", importance=1)
        mgr.add_global_memory("high", "很重要", importance=10)
        mgr.add_global_memory("mid", "中等", importance=5)

        memories = mgr.list_global_memories()
        assert memories[0].key == "high"
        assert memories[1].key == "mid"
        assert memories[2].key == "low"


class TestMemoryWithImportance:
    """测试重要性过滤"""

    def test_min_importance_filter(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("secret", "秘密信息", importance=1)
        mgr.add_global_memory("important", "重要信息", importance=8)

        filtered = mgr.list_global_memories(min_importance=5)
        assert len(filtered) == 1
        assert filtered[0].key == "important"

    def test_include_all(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("a", "A", importance=1)
        mgr.add_global_memory("b", "B", importance=2)

        all_mem = mgr.list_global_memories(min_importance=0)
        assert len(all_mem) == 2


class TestSessionMemory:
    """测试会话级记忆"""

    def test_add_session_memory(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mem_id = mgr.add_session_memory("sess_1", "session_key", "会话值")
        assert mem_id > 0

    def test_global_and_session_separate(self, temp_memory_db):
        """全局记忆和会话记忆应互不干扰"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("shared_key", "全局")
        mgr.add_session_memory("sess_1", "shared_key", "会话")

        globals_list = mgr.list_global_memories()
        assert len(globals_list) == 1
        assert globals_list[0].value == "全局"


class TestMemorySearch:
    """测试记忆搜索"""

    def test_search_by_keyword(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("favorite_color", "蓝色")
        mgr.add_global_memory("favorite_food", "火锅")
        mgr.add_global_memory("phone_number", "13800138000")

        results = mgr.search_memories("favorite")
        assert len(results) == 2

    def test_search_by_value(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("hobby", "打篮球")
        mgr.add_global_memory("sport", "游泳")

        results = mgr.search_memories("篮球")
        assert len(results) == 1
        assert results[0].key == "hobby"

    def test_search_no_results(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("a", "b")
        results = mgr.search_memories("不存在的内容")
        assert len(results) == 0

    def test_search_limit(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        for i in range(20):
            mgr.add_global_memory(f"key_{i}", f"value_{i}")

        results = mgr.search_memories("key", limit=5)
        assert len(results) == 5


class TestMemoryDeletion:
    """测试记忆删除"""

    def test_delete_existing(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mem_id = mgr.add_global_memory("delete_me", "将被删除")
        assert mgr.delete_memory(mem_id) is True
        assert mgr.get_global_memory("delete_me") is None

    def test_delete_nonexistent(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        assert mgr.delete_memory(99999) is False


class TestSystemPromptAddition:
    """测试系统提示词附加内容"""

    def test_empty_prompt_addition(self, temp_memory_db):
        """没有记忆时返回空字符串"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        addition = mgr.get_system_prompt_addition()
        assert addition == ""

    def test_prompt_addition_content(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("user_name", "小戡", importance=5)
        mgr.add_global_memory("birthday", "2017-02-15", importance=3)

        addition = mgr.get_system_prompt_addition()
        assert "小戡" in addition
        assert "2017-02-15" in addition
        assert "全局长期记忆" in addition
        assert "共 2 条" in addition or "2" in addition

    def test_prompt_addition_cache(self, temp_memory_db):
        """缓存机制：无变化时应返回缓存内容"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("test", "value")
        addition1 = mgr.get_system_prompt_addition()
        addition2 = mgr.get_system_prompt_addition()
        assert addition1 == addition2

    def test_prompt_cache_invalidation(self, temp_memory_db):
        """添加记忆后缓存应失效"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        addition1 = mgr.get_system_prompt_addition()
        assert addition1 == ""  # 没有记忆时

        mgr.add_global_memory("new", "新记忆")
        addition2 = mgr.get_system_prompt_addition()
        assert "新记忆" in addition2

    def test_min_importance_in_prompt(self, temp_memory_db):
        """低于重要性阈值的记忆不应出现在系统提示词中"""
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("secret", "秘密", importance=1)  # 低于默认3
        mgr.add_global_memory("normal", "普通", importance=5)

        addition = mgr.get_system_prompt_addition()
        assert "秘密" not in addition  # 重要性太低
        assert "普通" in addition


class TestMemoryTags:
    """测试记忆标签"""

    def test_add_memory_with_tags(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mem_id = mgr.add_global_memory("tagged", "带标签", importance=5, tags=["personal", "important"])
        assert mem_id > 0

    def test_tags_stored_and_loaded(self, temp_memory_db):
        from pyclaw.memory import MemoryManager, Memory
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("tagged", "带标签", importance=5, tags=["a", "b", "c"])
        memories = mgr.list_global_memories()
        assert len(memories) == 1
        assert memories[0].tags == ["a", "b", "c"]

    def test_default_tags_empty(self, temp_memory_db):
        from pyclaw.memory import MemoryManager
        mgr = MemoryManager(temp_memory_db)

        mgr.add_global_memory("no_tags", "无标签")
        memories = mgr.list_global_memories()
        assert memories[0].tags == []
