"""
🖥️ Linux Chinese Desktop Path Skill for PyClaw
解决 Linux 中文桌面路径问题：自动检测是 "桌面" 还是 "Desktop"
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "DesktopPathSkill"


@dataclass
class GetDesktopPathTool:
    """获取正确的桌面路径"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_desktop_path",
            description="检测系统的实际桌面路径，自动处理中文 '桌面' 和英文 'Desktop' 的差异",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "（可选）要放在桌面的文件名，返回完整路径"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        filename = params.get("filename", "").strip()
        
        try:
            chinese_desktop = Path.home() / "桌面"
            english_desktop = Path.home() / "Desktop"
            
            result = ["🖥️ 桌面路径检测结果\n"]
            
            has_chinese = chinese_desktop.exists()
            has_english = english_desktop.exists()
            
            result.append(f"中文路径 ~/桌面: {'✅ 存在' if has_chinese else '❌ 不存在'}")
            result.append(f"英文路径 ~/Desktop: {'✅ 存在' if has_english else '❌ 不存在'}")
            result.append("")
            
            # 确定优先使用的路径
            if has_chinese:
                primary_path = chinese_desktop
                result.append("📌 优先使用: 中文路径 ~/桌面")
            elif has_english:
                primary_path = english_desktop
                result.append("📌 优先使用: 英文路径 ~/Desktop")
            else:
                # 都不存在，尝试创建中文路径
                primary_path = chinese_desktop
                primary_path.mkdir(exist_ok=True)
                result.append("📌 两个路径都不存在，已创建中文路径 ~/桌面")
            
            result.append("")
            result.append(f"完整路径: {primary_path}")
            
            if filename:
                full_path = primary_path / filename
                result.append("")
                result.append(f"📄 目标文件: {filename}")
                result.append(f"完整文件路径: {full_path}")
                result.append(f"文件已存在: {'✅' if full_path.exists() else '❌'}")
            
            return ToolResult(success=True, content="\n".join(result))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"检测桌面路径失败: {str(e)}")


@dataclass
class WriteToDesktopTool:
    """将内容写入桌面文件"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_to_desktop",
            description="将内容写入桌面的文件，自动选择正确的中文/英文桌面路径",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "文件名（例如 'output.txt'）"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文件内容"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "是否追加模式（默认 false = 覆盖）",
                        "default": False
                    }
                },
                "required": ["filename", "content"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        filename = params.get("filename", "").strip()
        content = params.get("content", "")
        append = params.get("append", False)
        
        if not filename:
            return ToolResult(success=False, content="", error="请指定文件名")
        
        try:
            # 检测桌面路径
            chinese_desktop = Path.home() / "桌面"
            english_desktop = Path.home() / "Desktop"
            
            if chinese_desktop.exists():
                desktop_path = chinese_desktop
            else:
                desktop_path = english_desktop
                # 如果都不存在，创建中文路径
                if not desktop_path.exists():
                    desktop_path = chinese_desktop
                    desktop_path.mkdir(exist_ok=True)
            
            full_path = desktop_path / filename
            
            # 写入文件
            mode = "a" if append else "w"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            file_size = full_path.stat().st_size
            mode_desc = "追加" if append else "写入"
            
            return ToolResult(
                success=True,
                content=f"✅ 文件已成功{mode_desc}到桌面！\n\n📄 文件名: {filename}\n📂 完整路径: {full_path}\n📊 文件大小: {file_size} 字节"
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"写入文件失败: {str(e)}")


class DesktopPathSkill:
    """
    🖥️ Linux 中文桌面路径 Skill for PyClaw
    自动检测和处理中文 "桌面" 与英文 "Desktop" 路径差异
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Desktop Path",
            description="Linux 中文桌面路径处理：自动检测是 '桌面' 还是 'Desktop'",
            author="骆戡",
            version="1.0.0",
            tags=["linux", "desktop", "路径", "工具"],
            website="https://github.com/pyclaw/skill-desktop-path"
        )
    
    def get_tools(self):
        return [
            GetDesktopPathTool(),
            WriteToDesktopTool()
        ]
    
    async def initialize(self) -> bool:
        print("[Desktop Path Skill] Linux 中文桌面路径 Skill 初始化完成")
        return True
    
    async def cleanup(self) -> None:
        print("[Desktop Path Skill] Linux 中文桌面路径 Skill 已卸载")
