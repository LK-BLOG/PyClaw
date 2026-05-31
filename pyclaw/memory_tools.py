"""
🧠 Memory management tools
Allow AI to add, query, and delete long-term memories
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from .pyclaw_types import ToolDefinition, ToolResult
from .memory import memory_manager


@dataclass
class AddGlobalMemoryTool:
    """Add global memory"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="add_global_memory",
            description="Add a global long-term memory visible to all sessions. Use this to remember user preferences, common settings, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Memory key (short descriptive name)"
                    },
                    "value": {
                        "type": "string",
                        "description": "Memory content"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance score (1-10, default 5). Higher = more priority display",
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
                error="Please provide both key and value for the memory"
            )
        
        try:
            memory_id = memory_manager.add_global_memory(key, value, importance)
            return ToolResult(
                success=True,
                content=f"✅ Global memory added!\n\nMemory ID: {memory_id}\nKey: {key}\nValue: {value}\nImportance: {importance}/10\n\nThis memory will be visible in all future sessions!"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to add memory: {str(e)}"
            )


@dataclass
class ListGlobalMemoriesTool:
    """List all global memories"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_global_memories",
            description="List all saved global long-term memories, sorted by importance",
            parameters={
                "type": "object",
                "properties": {
                    "min_importance": {
                        "type": "integer",
                        "description": "Minimum importance score (default 0 = all)",
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
                    content="📭 No global memories saved. Use add_global_memory to add one."
                )
            
            lines = ["🧠 Global memories\n"]
            for i, mem in enumerate(memories, 1):
                time_str = datetime.fromtimestamp(mem.updated_at).strftime('%Y-%m-%d %H:%M')
                lines.append(f"{i}. [ID:{mem.id}] {mem.key}")
                lines.append(f"   Value: {mem.value}")
                lines.append(f"   Importance: {'⭐' * mem.importance} ({mem.importance}/10)")
                lines.append(f"   Updated: {time_str}")
                lines.append("")
            
            lines.append(f"Total: {len(memories)} memories")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to list memories: {str(e)}"
            )


@dataclass
class SearchMemoryTool:
    """Search memories"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_memory",
            description="Search all memories (global and session) by keyword",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 10)",
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
                error="Please provide a search keyword"
            )
        
        try:
            memories = memory_manager.search_memories(keyword, limit)
            
            if not memories:
                return ToolResult(
                    success=True,
                    content=f"🔍 No memories found matching '{keyword}'"
                )
            
            lines = [f"🔍 Search results: '{keyword}'\n"]
            for i, mem in enumerate(memories, 1):
                mem_type = "🌐 Global" if mem.memory_type == "global" else "💬 Session"
                lines.append(f"{i}. [{mem_type}] {mem.key}")
                lines.append(f"   {mem.value}")
                lines.append("")
            
            lines.append(f"Found {len(memories)} matching memories")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Search failed: {str(e)}"
            )


@dataclass
class DeleteMemoryTool:
    """Delete memory"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="delete_memory",
            description="Delete a memory by its ID",
            parameters={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "ID of the memory to delete"
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
                    content=f"🗑️ Memory ID {memory_id} deleted successfully!"
                )
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Delete failed: no memory found with ID {memory_id}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Delete failed: {str(e)}"
            )
