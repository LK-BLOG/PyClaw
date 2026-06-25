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

# 可选 YAML 支持
try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str
    description: str
    author: str
    version: str
    tags: List[str] = None
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
        self._declarative_skills: Dict[str, Dict] = {}  # 声明式 Skill（来自 SKILL.md）
        
        # 确保目录存在
        self.skill_dir.mkdir(exist_ok=True)
        if not (self.skill_dir / "__init__.py").exists():
            (self.skill_dir / "__init__.py").write_text("")
    
    def discover_skills(self) -> List[str]:
        """发现并加载所有 Skill
        
        双轨发现策略：
        1. 先扫 SKILL.md — 纯声明式 Skill，不需要 Python 代码
        2. 回退到现有 __init__.py 加载（向后兼容）
        """
        loaded = []
        
        for item in self.skill_dir.iterdir():
            if not item.is_dir():
                continue
            
            skill_name = item.name
            md_path = item / "SKILL.md"
            init_path = item / "__init__.py"
            
            if md_path.exists():
                if init_path.exists():
                    # Both exist: prefer __init__.py (programmatic), also load SKILL.md
                    try:
                        if self._load_skill(skill_name):
                            loaded.append(skill_name)
                    except Exception as e:
                        print(f"[ERROR] Failed to load Skill '{skill_name}': {e}")
                    # Also load SKILL.md for additional context
                    self.load_skill_from_markdown(item)
                else:
                    # Pure declarative skill
                    try:
                        if self.load_skill_from_markdown(item):
                            loaded.append(skill_name)
                            print(f"[OK] Declarative Skill loaded: {skill_name}")
                    except Exception as e:
                        print(f"[ERROR] Failed to load declarative Skill '{skill_name}': {e}")
            elif init_path.exists():
                # Legacy: __init__.py only
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
            
            print(f"[OK] Skill loaded: {metadata.name} v{metadata.version} by {metadata.author}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load Skill '{skill_name}': {e}")
            return False
    
    def get_all_tools(self) -> List[Any]:
        """获取所有 Skill 提供的所有工具"""
        all_tools = []
        for skill in self.skills.values():
            try:
                tools = skill.get_tools()
                all_tools.extend(tools)
            except Exception as e:
                print(f"[ERROR] Failed to get Skill tools: {e}")
        return all_tools
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 Skill 的信息"""
        # 先查编程式
        if skill_name in self.skill_metadata:
            meta = self.skill_metadata[skill_name]
            return {
                "name": meta.name,
                "description": meta.description,
                "author": meta.author,
                "version": meta.version,
                "tags": meta.tags,
                "website": meta.website,
                "type": "programmatic"
            }
        # 再查声明式
        decl = self._declarative_skills.get(skill_name)
        if decl:
            return {
                "name": decl["name"],
                "description": decl["description"],
                "author": "",
                "version": "1.0.0",
                "tags": [],
                "website": None,
                "type": "declarative"
            }
        return None

    def load_skill_from_markdown(self, skill_dir: Path) -> bool:
        """从 SKILL.md 加载声明式 Skill"""
        md_path = skill_dir / "SKILL.md"
        if not md_path.exists():
            return False

        content = md_path.read_text(encoding="utf-8")

        # Parse YAML frontmatter (between --- markers)
        name = skill_dir.name
        description = ""
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                if yaml is not None:
                    meta = yaml.safe_load(parts[1])
                    name = meta.get("name", name)
                    description = meta.get("description", "")
                else:
                    # Fallback: simple line parser
                    for line in parts[1].strip().split("\n"):
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                body = parts[2]

        # Combine frontmatter description + body as the skill content
        skill_content = body.strip()
        if description:
            skill_content = f"{description}\n\n{skill_content}"

        # 创建声明式 Skill
        self._declarative_skills[name] = {
            "name": name,
            "description": description or name,
            "content": skill_content,
        }
        return True

    def get_declarative_skills_content(self, max_chars_per_skill: int = 600) -> str:
        """返回所有声明式 Skill 的内容（截断到 max_chars_per_skill），用于注入 system prompt"""
        if not self._declarative_skills:
            return ""

        parts = []
        for skill_name, info in self._declarative_skills.items():
            content = info["content"]
            if len(content) > max_chars_per_skill:
                content = content[:max_chars_per_skill] + "\n...(truncated)"
            parts.append(f"## Skill: {skill_name}")
            parts.append(content)
        return "\n\n".join(parts)
    
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
