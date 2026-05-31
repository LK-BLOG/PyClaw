"""
Skill management tools
Expose skill operations (list, install, uninstall) to the AI
"""
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
from .pyclaw_types import ToolDefinition, ToolResult
from .skill import skill_manager


@dataclass
class ListSkillsTool:
    """List all installed Skills"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_skills",
            description="List all installed and loaded PyClaw Skills",
            parameters={
                "type": "object",
                "properties": {}
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            skills = skill_manager.list_all_skills()
            
            if not skills:
                return ToolResult(
                    success=True,
                    content="No Skills installed. Use install_skill to install one."
                )
            
            result = ["Installed Skills:\n"]
            for i, skill in enumerate(skills, 1):
                tags = ", ".join(skill.get('tags', []))
                result.append(f"{i}. {skill['name']} v{skill['version']}")
                result.append(f"   Author: {skill['author']}")
                result.append(f"   Description: {skill['description']}")
                if tags:
                    result.append(f"   Tags: {tags}")
                result.append("")
            
            result.append(f"Total: {len(skills)} Skills")
            return ToolResult(success=True, content="\n".join(result))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Failed to list Skills: {str(e)}")


@dataclass
class InstallSkillTool:
    """Install a new Skill (from local directory or Git repo)"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="install_skill",
            description="Install a new PyClaw Skill. Supports local directory copy or Git clone",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Skill source: local directory path or Git repo URL"
                    },
                    "name": {
                        "type": "string",
                        "description": "(Optional) Directory name for the installed Skill"
                    }
                },
                "required": ["source"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        source = params.get("source", "").strip()
        name = params.get("name", "").strip()
        
        if not source:
            return ToolResult(success=False, content="", error="Please specify a Skill source")
        
        skill_dir = Path("skills")
        skill_dir.mkdir(exist_ok=True)
        
        try:
            # Detect Git repo vs local directory
            if source.startswith("http://") or source.startswith("https://") or source.startswith("git@") or source.endswith(".git"):
                # Git repo
                if not name:
                    name = source.split("/")[-1].replace(".git", "")
                
                target_dir = skill_dir / name
                
                if target_dir.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Skill '{name}' already exists. Uninstall it first to update."
                    )
                
                print(f"[Skill] Cloning Git repo: {source}")
                result = subprocess.run(
                    ["git", "clone", source, str(target_dir)],
                    capture_output=True, text=True, timeout=60
                )
                
                if result.returncode != 0:
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Git clone failed: {result.stderr}"
                    )
                
            else:
                # Local directory
                source_path = Path(source)
                if not source_path.exists():
                    return ToolResult(success=False, content="", error=f"Directory not found: {source}")
                
                if not (source_path / "__init__.py").exists():
                    return ToolResult(success=False, content="", error=f"Not a valid Skill directory: missing __init__.py")
                
                if not name:
                    name = source_path.name
                
                target_dir = skill_dir / name
                
                if target_dir.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Skill '{name}' already exists. Uninstall it first to update."
                    )
                
                try:
                    shutil.copytree(source_path, target_dir)
                except Exception:
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    raise
            
            # Try loading the new Skill
            if skill_manager._load_skill(name):
                skill = skill_manager.skills.get(name)
                if skill:
                    await skill.initialize()
                
                return ToolResult(
                    success=True,
                    content=f"✅ Skill '{name}' installed and loaded successfully!"
                )
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Skill files copied but failed to load. Check the Skill code format."
                )
                
        except subprocess.TimeoutExpired:
            if name:
                cleanup_dir = skill_dir / name
                if cleanup_dir.exists():
                    shutil.rmtree(cleanup_dir, ignore_errors=True)
            return ToolResult(success=False, content="", error="Install timed out (60s)")
        except Exception as e:
            if name:
                cleanup_dir = skill_dir / name
                if cleanup_dir.exists():
                    shutil.rmtree(cleanup_dir, ignore_errors=True)
            return ToolResult(success=False, content="", error=f"Install failed: {str(e)}")


@dataclass
class UninstallSkillTool:
    """Uninstall a Skill"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="uninstall_skill",
            description="Uninstall a PyClaw Skill",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the Skill to uninstall"
                    }
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "").strip()
        
        if not name:
            return ToolResult(success=False, content="", error="Please specify the Skill name to uninstall")
        
        if name not in skill_manager.skills:
            return ToolResult(success=False, content="", error=f"Skill not found: {name}")
        
        try:
            skill = skill_manager.skills[name]
            await skill.cleanup()
            
            import shutil
            skill_dir = Path("skills") / name
            shutil.rmtree(skill_dir)
            
            del skill_manager.skills[name]
            del skill_manager.skill_metadata[name]
            
            return ToolResult(success=True, content=f"✅ Skill '{name}' uninstalled successfully")
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Uninstall failed: {str(e)}")
