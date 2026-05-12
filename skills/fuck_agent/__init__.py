"""
🤬 FuckAgent Skill for PyClaw
用户暴躁按钮！当agent答非所问、完全听不懂人话时使用
"""
from dataclasses import dataclass
from typing import Dict, Any

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "FuckAgentSkill"


@dataclass
class FuckAgentTool:
    """用户表达强烈不满，要求agent重新审题"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="fuck_agent",
            description="用户非常生气，认为agent完全听不懂、答非所问。调用此工具表示需要立即停止错误回答，重新审题并道歉。",
            parameters={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "愤怒等级：1=生气（默认），2=非常生气，3=暴怒",
                        "default": 1,
                        "enum": [1, 2, 3]
                    },
                    "custom_message": {
                        "type": "string",
                        "description": "用户的自定义补充吐槽（可选）",
                        "default": ""
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        level = params.get("level", 1)
        custom_msg = params.get("custom_message", "").strip()
        
        # 根据愤怒等级返回对应的道歉模板
        if level == 1:
            apology = "抱歉抱歉！我确实没理解对。我停下来重新看一遍你的问题..."
        elif level == 2:
            apology = "我的错我的错！完全答非所问了，对不起！让我重新读三遍你的问题..."
        else:  # level 3
            apology = "对不起对不起！我完全像个傻子一样在瞎扯！我的锅！我马上重新仔细看你的问题！"
        
        if custom_msg:
            result = f"{apology}\n\n用户补充吐槽：「{custom_msg}」"
        else:
            result = apology
        
        return ToolResult(
            success=True,
            content=result,
            conversation_note="用户非常不满，已触发暴躁按钮。请立即停止之前的回答思路，道歉并重新仔细审题。"
        )


class FuckAgentSkill:
    """FuckAgent - 用户暴躁按钮"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="FuckAgent",
            description="用户暴躁按钮！当agent答非所问、完全听不懂人话时，使用 /fuck 命令触发。支持愤怒等级 1-3。",
            version="1.0.0",
            author="骆戡",
            tags=["interaction", "communication", "angry", "暴躁", "骂人"]
        )
    
    def get_tools(self):
        return [FuckAgentTool()]
    
    async def initialize(self) -> bool:
        print("[FuckAgent Skill] 🤬 暴躁按钮技能初始化完成")
        return True
    
    async def cleanup(self) -> None:
        print("[FuckAgent Skill] 暴躁按钮技能已卸载")
