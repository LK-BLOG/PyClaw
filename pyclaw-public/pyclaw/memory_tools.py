"""
🧠 记忆管理工具
让 AI 可以添加、查询、删除长期记忆
"""
from dataclasses import dataclass
from typing import Dict, Any
from .pyclaw_types import ToolDefinition, ToolResult
from .memory import memory_manager


@dataclass
class AddGlobalMemoryTool:
    """添加全局记忆"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="add_global_memory",
            description="添加一条全局长期记忆，所有会话都会看到。例如记住用户的偏好、常用设置等",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "记忆的键名（简短描述性名称）"
                    },
                    "value": {
                        "type": "string",
                        "description": "记忆的具体内容"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "重要性评分（1-10，默认 5），分数越高越优先显示",
                        "default": 5
                    }
                },
                "required": ["key", "value"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        key = params.get("key", "").strip()
        value = params.get("value", "").strip()
        importance = params.get("importance", 5)
        
        if not key or not value:
            return ToolResult(
                success=False,
                content="",
                error="请同时提供记忆的键名(key)和内容(value)"
            )
        
        try:
            memory_id = memory_manager.add_global_memory(key, value, importance)
            return ToolResult(
                success=True,
                content=f"✅ 全局记忆已添加！\n\n记忆 ID: {memory_id}\n键名: {key}\n内容: {value}\n重要性: {importance}/10\n\n所有未来的会话都会看到这条记忆！"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"添加记忆失败: {str(e)}"
            )


@dataclass
class ListGlobalMemoriesTool:
    """列出所有全局记忆"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_global_memories",
            description="列出所有已保存的全局长期记忆，按重要性排序",
            parameters={
                "type": "object",
                "properties": {
                    "min_importance": {
                        "type": "integer",
                        "description": "最低重要性分数（默认 0 = 全部）",
                        "default": 0
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        min_importance = params.get("min_importance", 0)
        
        try:
            memories = memory_manager.list_global_memories(min_importance)
            
            if not memories:
                return ToolResult(
                    success=True,
                    content="📭 当前没有保存任何全局记忆。你可以使用 add_global_memory 工具添加新的记忆。"
                )
            
            lines = ["🧠 全局长期记忆列表\n"]
            for i, mem in enumerate(memories, 1):
                time_str = datetime.fromtimestamp(mem.updated_at).strftime('%Y-%m-%d %H:%M')
                lines.append(f"{i}. [ID:{mem.id}] {mem.key}")
                lines.append(f"   内容: {mem.value}")
                lines.append(f"   重要性: {'⭐' * mem.importance} ({mem.importance}/10)")
                lines.append(f"   更新时间: {time_str}")
                lines.append("")
            
            lines.append(f"总计: {len(memories)} 条记忆")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"获取记忆列表失败: {str(e)}"
            )


@dataclass
class SearchMemoryTool:
    """搜索记忆"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_memory",
            description="搜索所有记忆（全局和会话），按关键词匹配",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制（默认 10）",
                        "default": 10
                    }
                },
                "required": ["keyword"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        keyword = params.get("keyword", "").strip()
        limit = params.get("limit", 10)
        
        if not keyword:
            return ToolResult(
                success=False,
                content="",
                error="请提供搜索关键词"
            )
        
        try:
            memories = memory_manager.search_memories(keyword, limit)
            
            if not memories:
                return ToolResult(
                    success=True,
                    content=f"🔍 没有找到包含 '{keyword}' 的记忆"
                )
            
            lines = [f"🔍 搜索结果: '{keyword}'\n"]
            for i, mem in enumerate(memories, 1):
                mem_type = "🌐 全局" if mem.memory_type == "global" else "💬 会话"
                lines.append(f"{i}. [{mem_type}] {mem.key}")
                lines.append(f"   {mem.value}")
                lines.append("")
            
            lines.append(f"找到 {len(memories)} 条相关记忆")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"搜索失败: {str(e)}"
            )


@dataclass
class DeleteMemoryTool:
    """删除记忆"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delete_memory",
            description="删除指定 ID 的记忆",
            parameters={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "要删除的记忆 ID"
                    }
                },
                "required": ["memory_id"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        memory_id = params.get("memory_id")
        
        try:
            if memory_manager.delete_memory(memory_id):
                return ToolResult(
                    success=True,
                    content=f"🗑️ 记忆 ID {memory_id} 已成功删除！"
                )
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"删除失败：没有找到 ID 为 {memory_id} 的记忆"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"删除失败: {str(e)}"
            )


from datetime import datetime
