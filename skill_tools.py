"""
Skill 管理工具
让 AI 可以列出、安装、管理 Skill
"""
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
from .types import ToolDefinition, ToolResult
from .skill import skill_manager


@dataclass
class ListSkillsTool:
    """列出所有已安装的 Skill"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_skills",
            description="列出所有已安装和已加载的 PyClaw Skill 插件",
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
                    content="当前没有已安装的 Skill。可以使用 install_skill 安装新的 Skill。"
                )
            
            result = ["已安装的 Skill 列表:\n"]
            for i, skill in enumerate(skills, 1):
                tags = ", ".join(skill.get('tags', []))
                result.append(f"{i}. {skill['name']} v{skill['version']}")
                result.append(f"   作者: {skill['author']}")
                result.append(f"   描述: {skill['description']}")
                if tags:
                    result.append(f"   标签: {tags}")
                result.append("")
            
            result.append(f"总计: {len(skills)} 个 Skill")
            return ToolResult(success=True, content="\n".join(result))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取 Skill 列表失败: {str(e)}")


@dataclass
class InstallSkillTool:
    """安装新的 Skill（从本地目录或 Git 仓库）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="install_skill",
            description="安装新的 PyClaw Skill 插件。支持从本地目录复制或从 Git 仓库克隆",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Skill 来源：本地目录路径或 Git 仓库 URL"
                    },
                    "name": {
                        "type": "string",
                        "description": "（可选）指定安装后的 Skill 目录名称"
                    }
                },
                "required": ["source"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        source = params.get("source", "").strip()
        name = params.get("name", "").strip()
        
        if not source:
            return ToolResult(success=False, content="", error="请指定 Skill 来源")
        
        skill_dir = Path("skills")
        skill_dir.mkdir(exist_ok=True)
        
        try:
            # 判断是 Git 还是本地目录
            if source.startswith("http://") or source.startswith("git@") or source.endswith(".git"):
                # Git 仓库
                if not name:
                    # 从 URL 提取名称
                    name = source.split("/")[-1].replace(".git", "")
                
                target_dir = skill_dir / name
                
                if target_dir.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Skill '{name}' 已存在。如果需要更新请先卸载。"
                    )
                
                print(f"[Skill] 正在克隆 Git 仓库: {source}")
                result = subprocess.run(
                    ["git", "clone", source, str(target_dir)],
                    capture_output=True, text=True, timeout=60
                )
                
                if result.returncode != 0:
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Git 克隆失败: {result.stderr}"
                    )
                
            else:
                # 本地目录
                source_path = Path(source)
                if not source_path.exists():
                    return ToolResult(success=False, content="", error=f"目录不存在: {source}")
                
                if not (source_path / "__init__.py").exists():
                    return ToolResult(success=False, content="", error=f"不是有效的 Skill 目录: 缺少 __init__.py")
                
                if not name:
                    name = source_path.name
                
                target_dir = skill_dir / name
                
                if target_dir.exists():
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Skill '{name}' 已存在。如果需要更新请先卸载。"
                    )
                
                # 复制目录
                import shutil
                shutil.copytree(source_path, target_dir)
            
            # 尝试加载新安装的 Skill
            if skill_manager._load_skill(name):
                skill = skill_manager.skills.get(name)
                if skill:
                    await skill.initialize()
                
                return ToolResult(
                    success=True,
                    content=f"✅ Skill '{name}' 安装成功并已加载！"
                )
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Skill 文件复制成功，但加载失败。请检查 Skill 代码格式。"
                )
                
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, content="", error="安装超时（60秒）")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"安装失败: {str(e)}")


@dataclass
class UninstallSkillTool:
    """卸载已安装的 Skill"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="uninstall_skill",
            description="卸载指定的 PyClaw Skill 插件",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要卸载的 Skill 名称"
                    }
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "").strip()
        
        if not name:
            return ToolResult(success=False, content="", error="请指定要卸载的 Skill 名称")
        
        if name not in skill_manager.skills:
            return ToolResult(success=False, content="", error=f"未找到 Skill: {name}")
        
        try:
            # 先清理
            skill = skill_manager.skills[name]
            await skill.cleanup()
            
            # 删除目录
            import shutil
            skill_dir = Path("skills") / name
            shutil.rmtree(skill_dir)
            
            # 从管理器移除
            del skill_manager.skills[name]
            del skill_manager.skill_metadata[name]
            
            return ToolResult(success=True, content=f"✅ Skill '{name}' 已成功卸载")
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"卸载失败: {str(e)}")
