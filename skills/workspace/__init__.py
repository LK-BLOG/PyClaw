"""
📂 Workspace Skill for PyClaw
工作空间管理 - 文件操作、目录管理、搜索、Git 状态等功能
"""
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, List
from pathlib import Path

from pyclaw.skill import SkillMetadata
from pyclaw.types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "WorkspaceSkill"

# 全局工作空间配置
WORKSPACES_CONFIG = Path.home() / ".pyclaw" / "workspaces.json"


def _load_workspaces() -> Dict[str, str]:
    """加载已保存的工作空间列表"""
    if WORKSPACES_CONFIG.exists():
        import json
        try:
            with open(WORKSPACES_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def _save_workspaces(workspaces: Dict[str, str]) -> None:
    """保存工作空间列表"""
    WORKSPACES_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(WORKSPACES_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(workspaces, f, ensure_ascii=False, indent=2)


@dataclass
class AddWorkspaceTool:
    """添加工作空间"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_add",
            description="添加一个新的工作空间目录。给目录起个名字，方便后续快速访问",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "工作空间名称（简短好记，比如：我的项目、博客、代码库）"
                    },
                    "path": {
                        "type": "string",
                        "description": "工作空间的绝对路径或相对路径"
                    }
                },
                "required": ["name", "path"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "").strip()
        path = params.get("path", "").strip()
        
        if not name or not path:
            return ToolResult(
                success=False,
                content="",
                error="工作空间名称和路径都不能为空"
            )
        
        # 解析路径
        workspace_path = Path(path).expanduser().resolve()
        
        if not workspace_path.exists():
            return ToolResult(
                success=False,
                content="",
                error=f"路径不存在: {path}"
            )
        
        if not workspace_path.is_dir():
            return ToolResult(
                success=False,
                content="",
                error=f"路径不是目录: {path}"
            )
        
        # 保存
        workspaces = _load_workspaces()
        workspaces[name] = str(workspace_path)
        _save_workspaces(workspaces)
        
        return ToolResult(
            success=True,
            content=f"✅ 工作空间「{name}」已添加！\n\n"
                    f"📂 路径: {workspace_path}\n\n"
                    f"现在可以使用 workspace_list 查看所有工作空间，"
                    f"或使用 workspace_files 浏览目录内容"
        )


@dataclass
class ListWorkspacesTool:
    """列出所有工作空间"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_list",
            description="列出所有已添加的工作空间",
            parameters={
                "type": "object",
                "properties": {}
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        workspaces = _load_workspaces()
        
        if not workspaces:
            return ToolResult(
                success=True,
                content="📂 还没有添加任何工作空间\n\n"
                        "使用 workspace_add 添加你的第一个工作空间吧！"
            )
        
        lines = ["📂 已保存的工作空间列表\n", "=" * 50, ""]
        
        for i, (name, path) in enumerate(workspaces.items(), 1):
            lines.append(f"{i}. 「{name}」")
            lines.append(f"   📁 {path}")
            lines.append("")
        
        lines.append("=" * 50)
        lines.append(f"\n共 {len(workspaces)} 个工作空间")
        lines.append("\n💡 提示: 使用 workspace_files <名称> 浏览目录内容")
        
        return ToolResult(
            success=True,
            content="\n".join(lines)
        )


@dataclass
class RemoveWorkspaceTool:
    """移除工作空间"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_remove",
            description="移除一个已保存的工作空间（不会删除实际文件，仅移除记录）",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "要移除的工作空间名称"
                    }
                },
                "required": ["name"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "").strip()
        workspaces = _load_workspaces()
        
        if name not in workspaces:
            return ToolResult(
                success=False,
                content="",
                error=f"未找到名为「{name}」的工作空间"
            )
        
        del workspaces[name]
        _save_workspaces(workspaces)
        
        return ToolResult(
            success=True,
            content=f"✅ 工作空间「{name}」已从列表中移除\n\n"
                    "⚠️ 注意：实际目录文件未被删除，仅移除了记录"
        )


@dataclass
class ListFilesTool:
    """浏览工作空间目录内容"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_files",
            description="浏览工作空间或指定目录的文件列表",
            parameters={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "（可选）工作空间名称，不填则列出所有工作空间供选择"
                    },
                    "subdir": {
                        "type": "string",
                        "description": "（可选）子目录路径，相对于工作空间根目录"
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "（可选）是否显示隐藏文件，默认 false",
                        "default": False
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        workspace_name = params.get("workspace", "").strip()
        subdir = params.get("subdir", "").strip()
        show_hidden = params.get("show_hidden", False)
        
        workspaces = _load_workspaces()
        
        # 如果没有指定工作空间，显示列表
        if not workspace_name:
            if not workspaces:
                return ToolResult(
                    success=False,
                    content="",
                    error="还没有添加任何工作空间，请先使用 workspace_add 添加"
                )
            
            lines = ["📂 请指定工作空间名称：\n"]
            for name in workspaces.keys():
                lines.append(f"  - {name}")
            lines.append("\n例如：workspace_files workspace=\"我的项目\"")
            
            return ToolResult(
                success=True,
                content="\n".join(lines)
            )
        
        if workspace_name not in workspaces:
            return ToolResult(
                success=False,
                content="",
                error=f"未找到工作空间「{workspace_name}」"
            )
        
        # 构建目标路径
        base_path = Path(workspaces[workspace_name])
        target_path = base_path
        if subdir:
            target_path = base_path / subdir
        
        target_path = target_path.resolve()
        
        # 安全检查：防止跳出工作空间
        if not str(target_path).startswith(str(base_path)):
            return ToolResult(
                success=False,
                content="",
                error="安全限制：不能访问工作空间以外的目录"
            )
        
        if not target_path.exists():
            return ToolResult(
                success=False,
                content="",
                error=f"路径不存在: {subdir or ''}"
            )
        
        if not target_path.is_dir():
            return ToolResult(
                success=False,
                content="",
                error=f"不是目录: {subdir or ''}"
            )
        
        # 列出文件
        try:
            items = sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            lines = [f"📂 工作空间「{workspace_name}」 - {target_path}"]
            lines.append("=" * 60)
            lines.append("")
            
            dir_count = 0
            file_count = 0
            
            for item in items:
                # 跳过隐藏文件
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    lines.append(f" 📁 {item.name}/")
                    dir_count += 1
                else:
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size//1024}KB"
                    else:
                        size_str = f"{size//(1024*1024)}MB"
                    
                    lines.append(f" 📄 {item.name} ({size_str})")
                    file_count += 1
            
            lines.append("")
            lines.append("=" * 60)
            lines.append(f"\n📊 统计: {dir_count} 个目录, {file_count} 个文件")
            
            if len(lines) > 100:
                return ToolResult(
                    success=True,
                    content="\n".join(lines[:100]) + "\n\n... (文件过多，已截断)"
                )
            
            return ToolResult(
                success=True,
                content="\n".join(lines)
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"读取目录失败: {str(e)}"
            )


@dataclass
class ReadFileTool:
    """读取工作空间中的文件"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_read_file",
            description="读取工作空间中的文件内容（文本文件）",
            parameters={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "工作空间名称"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "文件路径，相对于工作空间根目录"
                    },
                    "limit": {
                        "type": "number",
                        "description": "（可选）读取的最大行数，默认 100 行",
                        "default": 100
                    }
                },
                "required": ["workspace", "file_path"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        workspace_name = params.get("workspace", "").strip()
        file_path = params.get("file_path", "").strip()
        limit = params.get("limit", 100)
        
        workspaces = _load_workspaces()
        
        if workspace_name not in workspaces:
            return ToolResult(
                success=False,
                content="",
                error=f"未找到工作空间「{workspace_name}」"
            )
        
        base_path = Path(workspaces[workspace_name])
        target_file = (base_path / file_path).resolve()
        
        # 安全检查
        if not str(target_file).startswith(str(base_path)):
            return ToolResult(
                success=False,
                content="",
                error="安全限制：不能访问工作空间以外的文件"
            )
        
        if not target_file.exists():
            return ToolResult(
                success=False,
                content="",
                error=f"文件不存在: {file_path}"
            )
        
        if target_file.is_dir():
            return ToolResult(
                success=False,
                content="",
                error=f"这是一个目录，不是文件: {file_path}"
            )
        
        # 文件大小检查
        file_size = target_file.stat().st_size
        if file_size > 1024 * 1024:  # 1MB
            return ToolResult(
                success=False,
                content="",
                error=f"文件过大（{file_size//(1024*1024)}MB），为了安全不读取"
            )
        
        try:
            with open(target_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = []
                for i, line in enumerate(f, 1):
                    if i > limit:
                        lines.append(f"\n... (已截断，共 {limit} 行，文件还有更多内容)")
                        break
                    lines.append(line.rstrip())
            
            content = "\n".join(lines)
            
            return ToolResult(
                success=True,
                content=f"📄 文件: {file_path}\n"
                        f"📍 位置: {target_file}\n"
                        f"📊 大小: {file_size} 字节\n\n"
                        f"{content}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"读取文件失败: {str(e)}"
            )


@dataclass
class SearchFilesTool:
    """在工作空间中搜索文件"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_search",
            description="在工作空间中按文件名搜索文件",
            parameters={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "工作空间名称"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "搜索关键词（支持通配符，比如 *.py）"
                    }
                },
                "required": ["workspace", "pattern"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        workspace_name = params.get("workspace", "").strip()
        pattern = params.get("pattern", "").strip()
        
        workspaces = _load_workspaces()
        
        if workspace_name not in workspaces:
            return ToolResult(
                success=False,
                content="",
                error=f"未找到工作空间「{workspace_name}」"
            )
        
        base_path = Path(workspaces[workspace_name])
        
        import fnmatch
        matches = []
        
        try:
            for root, dirs, files in os.walk(base_path):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(base_path)
                        matches.append(str(rel_path))
            
            if not matches:
                return ToolResult(
                    success=True,
                    content=f"🔍 在「{workspace_name}」中搜索「{pattern}」\n\n"
                            f"未找到匹配的文件"
                )
            
            lines = [f"🔍 在「{workspace_name}」中搜索「{pattern}」", "=" * 50, ""]
            
            for i, match in enumerate(sorted(matches), 1):
                lines.append(f"{i}. {match}")
                if i >= 50:
                    lines.append(f"\n... 还有 {len(matches) - 50} 个结果，已截断")
                    break
            
            lines.append("")
            lines.append(f"共找到 {len(matches)} 个匹配文件")
            
            return ToolResult(
                success=True,
                content="\n".join(lines)
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"搜索失败: {str(e)}"
            )


@dataclass
class GitStatusTool:
    """查看工作空间的 Git 状态"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_git_status",
            description="查看工作空间的 Git 仓库状态（修改、暂存、提交记录等）",
            parameters={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "工作空间名称"
                    }
                },
                "required": ["workspace"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        workspace_name = params.get("workspace", "").strip()
        
        workspaces = _load_workspaces()
        
        if workspace_name not in workspaces:
            return ToolResult(
                success=False,
                content="",
                error=f"未找到工作空间「{workspace_name}」"
            )
        
        repo_path = Path(workspaces[workspace_name])
        
        # 检查是否是 Git 仓库
        if not (repo_path / ".git").exists():
            return ToolResult(
                success=True,
                content=f"📂 工作空间「{workspace_name}」

⚠️ 该目录不是 Git 仓库

提示: 如果需要，可以在目录中运行 git init 初始化仓库"
            )
        
        try:
            # 获取 Git 状态
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            status_output = result.stdout.strip()
            
            # 获取分支名
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            branch_name = branch_result.stdout.strip() or "未知分支"
            
            lines = [
                f"📂 工作空间「{workspace_name}」- Git 状态",
                "=" * 50,
                f"🌿 当前分支: {branch_name}",
                ""
            ]
            
            if not status_output:
                lines.append("✅ 工作区干净，没有未提交的更改")
            else:
                lines.append("📝 待处理的文件：")
                lines.append("")
                for line in status_output.split('\n')[:20]:
                    status_char = line[0] if line else ''
                    if status_char == 'M':
                        lines.append(f"  ✏️  修改: {line[2:]}")
                    elif status_char == 'A':
                        lines.append(f"  ➕  新增: {line[2:]}")
                    elif status_char == 'D':
                        lines.append(f"  ❌  删除: {line[2:]}")
                    elif status_char == '??':
                        lines.append(f"  ❓  未跟踪: {line[3:]}")
                    else:
                        lines.append(f"  {line}")
                
                if len(status_output.split('\n')) > 20:
                    lines.append("\n  ... (更多文件已截断)")
            
            return ToolResult(
                success=True,
                content="\n".join(lines)
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                content="",
                error="Git 命令执行超时"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"获取 Git 状态失败: {str(e)}"
            )


class WorkspaceSkill:
    """
    📂 Workspace Skill for PyClaw
    工作空间管理 - 多目录管理、文件操作、搜索、Git 状态
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Workspace",
            description="工作空间管理 - 添加/移除工作空间、浏览文件、读取内容、搜索文件、Git 状态查看",
            author="PyClaw Team",
            version="1.0.0",
            tags=["workspace", "file", "filesystem", "文件", "管理"],
            website="https://github.com/pyclaw/skill-workspace"
        )
    
    def get_tools(self):
        return [
            AddWorkspaceTool(),
            ListWorkspacesTool(),
            RemoveWorkspaceTool(),
            ListFilesTool(),
            ReadFileTool(),
            SearchFilesTool(),
            GitStatusTool()
        ]
    
    async def initialize(self) -> bool:
        print("[Workspace Skill] ✅ 工作空间管理 Skill 初始化完成")
        print(f"[Workspace Skill] 📦 已注册 {len(self.get_tools())} 个工具")
        return True
    
    async def cleanup(self) -> None:
        print("[Workspace Skill] 工作空间管理 Skill 已卸载")