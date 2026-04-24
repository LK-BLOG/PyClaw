"""
🧠 PyClaw 长期记忆系统
使用 SQLite 轻量存储，支持全局记忆和会话级记忆
"""
import sqlite3
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Memory:
    """记忆条目"""
    id: int
    memory_type: str  # 'global' 或 'session'
    session_id: Optional[str]
    key: str
    value: str
    importance: int  # 1-10，重要性评分
    created_at: float
    updated_at: float
    tags: List[str]


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, db_path: str = "pyclaw_memory.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                session_id TEXT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                importance INTEGER DEFAULT 5,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                tags TEXT DEFAULT '[]'
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON memories(key)")
        
        conn.commit()
        conn.close()
    
    def add_global_memory(self, key: str, value: str, importance: int = 5, tags: List[str] = None) -> int:
        """添加全局记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        now = time.time()
        tags_json = json.dumps(tags or [])
        
        # 检查是否已存在，存在则更新
        cursor.execute("SELECT id FROM memories WHERE memory_type = 'global' AND key = ?", (key,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE memories SET value = ?, importance = ?, tags = ?, updated_at = ?
                WHERE id = ?
            """, (value, importance, tags_json, now, existing[0]))
            memory_id = existing[0]
        else:
            cursor.execute("""
                INSERT INTO memories (memory_type, session_id, key, value, importance, created_at, updated_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('global', None, key, value, importance, now, now, tags_json))
            memory_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return memory_id
    
    def add_session_memory(self, session_id: str, key: str, value: str, importance: int = 5, tags: List[str] = None) -> int:
        """添加会话记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        now = time.time()
        tags_json = json.dumps(tags or [])
        
        cursor.execute("""
            INSERT INTO memories (memory_type, session_id, key, value, importance, created_at, updated_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('session', session_id, key, value, importance, now, now, tags_json))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return memory_id
    
    def get_global_memory(self, key: str) -> Optional[str]:
        """获取全局记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM memories WHERE memory_type = 'global' AND key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def list_global_memories(self, min_importance: int = 0) -> List[Memory]:
        """列出所有全局记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, memory_type, session_id, key, value, importance, created_at, updated_at, tags
            FROM memories WHERE memory_type = 'global' AND importance >= ?
            ORDER BY importance DESC, updated_at DESC
        """, (min_importance,))
        
        memories = []
        for row in cursor.fetchall():
            memories.append(Memory(
                id=row[0],
                memory_type=row[1],
                session_id=row[2],
                key=row[3],
                value=row[4],
                importance=row[5],
                created_at=row[6],
                updated_at=row[7],
                tags=json.loads(row[8])
            ))
        
        conn.close()
        return memories
    
    def search_memories(self, keyword: str, limit: int = 10) -> List[Memory]:
        """搜索记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        search_pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT id, memory_type, session_id, key, value, importance, created_at, updated_at, tags
            FROM memories 
            WHERE key LIKE ? OR value LIKE ?
            ORDER BY importance DESC, updated_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, limit))
        
        memories = []
        for row in cursor.fetchall():
            memories.append(Memory(
                id=row[0],
                memory_type=row[1],
                session_id=row[2],
                key=row[3],
                value=row[4],
                importance=row[5],
                created_at=row[6],
                updated_at=row[7],
                tags=json.loads(row[8])
            ))
        
        conn.close()
        return memories
    
    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def get_system_prompt_addition(self) -> str:
        """获取要追加到系统提示词的全局记忆"""
        memories = self.list_global_memories(min_importance=3)
        
        if not memories:
            return ""
        
        lines = ["\n\n## 🧠 全局长期记忆\n"]
        for mem in memories:
            lines.append(f"- **{mem.key}**: {mem.value}")
        
        lines.append(f"\n(共 {len(memories)} 条记忆)")
        return "\n".join(lines)


# 全局记忆管理器实例
memory_manager = MemoryManager()
