"""
🖥️ Linux Chinese Desktop Path Skill for PyClaw
Resolve Linux Chinese desktop path — auto-detect "桌面" vs "Desktop"
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill config
SKILL_CLASS = "DesktopPathSkill"


@dataclass
class GetDesktopPathTool:
    """Get the correct desktop path"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_desktop_path",
            description="Detect the actual desktop path on Linux — handles Chinese '桌面' vs English 'Desktop' differences",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional: filename to place on desktop — returns full path"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        filename = params.get("filename", "").strip()
        
        try:
            chinese_desktop = Path.home() / "桌面"
            english_desktop = Path.home() / "Desktop"
            
            result = ["🖥️ Desktop Path Detection\n"]
            
            has_chinese = chinese_desktop.exists()
            has_english = english_desktop.exists()
            
            result.append(f"Chinese ~/桌面: {'✅ exists' if has_chinese else '❌ not found'}")
            result.append(f"English ~/Desktop: {'✅ exists' if has_english else '❌ not found'}")
            result.append("")
            
            # Determine primary path
            if has_chinese:
                primary_path = chinese_desktop
                result.append("📌 Primary: Chinese ~/桌面")
            elif has_english:
                primary_path = english_desktop
                result.append("📌 Primary: English ~/Desktop")
            else:
                # Neither exists — create Chinese path
                primary_path = chinese_desktop
                primary_path.mkdir(exist_ok=True)
                result.append("📌 Neither existed — created Chinese ~/桌面")
            
            result.append("")
            result.append(f"Full path: {primary_path}")
            
            if filename:
                full_path = primary_path / filename
                result.append("")
                result.append(f"📄 File: {filename}")
                result.append(f"Full path: {full_path}")
                result.append(f"Exists: {'✅' if full_path.exists() else '❌'}")
            
            return ToolResult(success=True, content="\n".join(result))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Desktop path detection failed: {str(e)}")


@dataclass
class WriteToDesktopTool:
    """Write content to a desktop file"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_to_desktop",
            description="Write content to a desktop file — auto-selects Chinese/English path",
            parameters={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename (e.g. 'output.txt')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Append mode (default false = overwrite)",
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
            return ToolResult(success=False, content="", error="Please specify a filename")
        
        try:
            # Detect desktop path
            chinese_desktop = Path.home() / "桌面"
            english_desktop = Path.home() / "Desktop"
            
            if chinese_desktop.exists():
                desktop_path = chinese_desktop
            else:
                desktop_path = english_desktop
                # Neither exists — create Chinese path
                if not desktop_path.exists():
                    desktop_path = chinese_desktop
                    desktop_path.mkdir(exist_ok=True)
            
            full_path = desktop_path / filename
            
            # Write file
            mode = "a" if append else "w"
            with open(full_path, mode, encoding="utf-8") as f:
                f.write(content)
            
            file_size = full_path.stat().st_size
            mode_desc = "appended" if append else "written"
            
            return ToolResult(
                success=True,
                content=f"✅ File successfully {mode_desc} to desktop!\n\n📄 Name: {filename}\n📂 Path: {full_path}\n📊 Size: {file_size} bytes"
            )
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Write file failed: {str(e)}")


class DesktopPathSkill:
    """
    🖥️ Linux Chinese Desktop Path Skill for PyClaw
    Auto-detect and handle Chinese "桌面" vs English "Desktop" path differences
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Desktop Path",
            description="Linux Chinese Desktop Path — auto-detect '桌面' vs 'Desktop'",
            author="骆戡",
            version="1.0.0",
            tags=["linux", "desktop", "path", "tool"],
            website="https://github.com/pyclaw/skill-desktop-path"
        )
    
    def get_tools(self):
        return [
            GetDesktopPathTool(),
            WriteToDesktopTool()
        ]
    
    async def initialize(self) -> bool:
        print("[Desktop Path Skill] Initialized")
        return True
    
    async def cleanup(self) -> None:
        print("[Desktop Path Skill] Linux Chinese Desktop Path Skill unloaded")
