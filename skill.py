"""
PyClaw Skill 插件系统
支持动态加载、安装、管理第三方 Skill
"""
import os
import json
import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Protocol


@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str
    description: str
    author: str
    version: str
    tags: List[str] = field(default_factory=list)
    website: Optional[str] = None


class Skill(Protocol):
    """Skill 接口协议"""
    
    @property
    def metadata(self) -> SkillMetadata:
        """返回 Skill 元数据"""
        ...
    
    def get_tools(self) -> List[Any]:
        """返回此 Skill 提供的所有工具"""
        ...
    
    async def initialize(self) -> bool:
        """初始化 Skill，返回是否成功"""
        return True
    
    async def cleanup(self) -> None:
        """清理资源"""
        pass


class SkillManager:
    """Skill 管理器"""
    
    def __init__(self, skill_dir: str = "skills"):
        self.skill_dir = Path(skill_dir)
        self.skills: Dict[str, Skill] = {}
        self.skill_metadata: Dict[str, SkillMetadata] = {}
        
        # 确保目录存在
        self.skill_dir.mkdir(exist_ok=True)
        if not (self.skill_dir / "__init__.py").exists():
            (self.skill_dir / "__init__.py").write_text("")
    
    def discover_skills(self) -> List[str]:
        """发现并加载所有 Skill"""
        loaded = []
        
        for item in self.skill_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                skill_name = item.name
                try:
                    if self._load_skill(skill_name):
                        loaded.append(skill_name)
                except Exception as e:
                    print(f"[ERROR] 加载 Skill '{skill_name}' 失败: {e}")
        
        return loaded
    
    def _load_skill(self, skill_name: str) -> bool:
        """加载单个 Skill"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}",
                self.skill_dir / skill_name / "__init__.py"
            )
            
            if not spec or not spec.loader:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 Skill 类
            if hasattr(module, "SKILL_CLASS"):
                skill_class = getattr(module, module.SKILL_CLASS)
            else:
                # 自动查找第一个 Skill 类
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name.endswith("Skill"):
                        skill_class = obj
                        break
                else:
                    return False
            
            skill_instance = skill_class()
            metadata = skill_instance.metadata
            
            self.skills[skill_name] = skill_instance
            self.skill_metadata[skill_name] = metadata
            
            print(f"[OK] 已加载 Skill: {metadata.name} v{metadata.version} by {metadata.author}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 加载 Skill '{skill_name}' 异常: {e}")
            return False
    
    def get_all_tools(self) -> List[Any]:
        """获取所有 Skill 提供的所有工具"""
        all_tools = []
        for skill in self.skills.values():
            try:
                tools = skill.get_tools()
                all_tools.extend(tools)
            except Exception as e:
                print(f"[ERROR] 获取 Skill 工具失败: {e}")
        return all_tools
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 Skill 的信息"""
        if skill_name not in self.skill_metadata:
            return None
        
        meta = self.skill_metadata[skill_name]
        return {
            "name": meta.name,
            "description": meta.description,
            "author": meta.author,
            "version": meta.version,
            "tags": meta.tags,
            "website": meta.website
        }
    
    def list_all_skills(self) -> List[Dict[str, Any]]:
        """列出所有已加载的 Skill"""
        return [
            self.get_skill_info(name)
            for name in self.skills.keys()
        ]
    
    async def initialize_all(self) -> int:
        """初始化所有 Skill"""
        success_count = 0
        for name, skill in self.skills.items():
            try:
                if await skill.initialize():
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] 初始化 Skill '{name}' 失败: {e}")
        return success_count


# 全局 Skill 管理器实例
skill_manager = SkillManager()
