"""
🖥️ System Info Skill for PyClaw
查看系统信息、CPU/内存/磁盘使用、进程等
"""
import os
import sys
import platform
import shutil
from dataclasses import dataclass
from typing import Dict, Any

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "SystemInfoSkill"


@dataclass
class SystemInfoTool:
    """获取系统基本信息"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_system_info",
            description="获取当前系统的基本信息：操作系统、Python版本、CPU、内存、磁盘等",
            parameters={
                "type": "object",
                "properties": {}
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            lines = ["🖥️ 系统信息\n"]
            
            # 操作系统
            lines.append(f"📦 系统: {platform.system()} {platform.release()}")
            lines.append(f"  版本: {platform.version()}")
            lines.append(f"  架构: {platform.machine()}")
            lines.append(f"  处理器: {platform.processor() or '未知'}")
            lines.append("")
            
            # Python
            lines.append(f"🐍 Python: {sys.version.split()[0]}")
            lines.append(f"  路径: {sys.executable}")
            lines.append("")
            
            # 磁盘
            disk = shutil.disk_usage(".")
            lines.append(f"💾 当前磁盘:")
            lines.append(f"  总计: {disk.total // (1024**3)} GB")
            lines.append(f"  已用: {disk.used // (1024**3)} GB ({100*disk.used/disk.total:.1f}%)")
            lines.append(f"  可用: {disk.free // (1024**3)} GB")
            lines.append("")
            
            # PyClaw
            lines.append(f"🦞 PyClaw 工作目录: {os.getcwd()}")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取系统信息失败: {str(e)}")


@dataclass
class ProcessListTool:
    """列出系统进程"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_processes",
            description="列出当前运行的进程，支持按名称搜索和数量限制",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "显示进程数量限制，默认 20",
                        "default": 20
                    },
                    "search": {
                        "type": "string",
                        "description": "按名称搜索进程，可选"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        limit = params.get("limit", 20)
        search = params.get("search", "").lower()
        
        try:
            import psutil
            
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if search and search not in info['name'].lower():
                        continue
                    
                    procs.append(info)
                except:
                    pass
            
            # 按 CPU 使用率排序
            procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            lines = [f"📊 进程列表 (显示前 {min(limit, len(procs))} 个)\n"]
            lines.append(f"{'PID':>6} | {'CPU%':>5} | {'MEM%':>5} | 进程名称")
            lines.append("-" * 50)
            
            for p in procs[:limit]:
                lines.append(
                    f"{p['pid']:>6} | {p.get('cpu_percent', 0):>5.1f} | "
                    f"{p.get('memory_percent', 0):>5.1f} | {p['name']}"
                )
            
            lines.append(f"\n总计: {len(procs)} 个进程")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except ImportError:
            return ToolResult(
                success=False,
                content="",
                error="需要 psutil 库：pip install psutil"
            )
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取进程列表失败: {str(e)}")


@dataclass
class KillProcessTool:
    """结束指定进程"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="kill_process",
            description="结束指定 PID 的进程",
            parameters={
                "type": "object",
                "properties": {
                    "pid": {
                        "type": "integer",
                        "description": "要结束的进程 PID"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "是否强制结束（kill -9），默认 false",
                        "default": False
                    }
                },
                "required": ["pid"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        pid = params.get("pid")
        force = params.get("force", False)
        
        try:
            import psutil
            
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            if force:
                proc.kill()
            else:
                proc.terminate()
            
            return ToolResult(
                success=True,
                content=f"✅ 已结束进程: PID={pid}, 名称={proc_name}"
            )
            
        except psutil.NoSuchProcess:
            return ToolResult(
                success=False,
                content="",
                error=f"不存在 PID 为 {pid} 的进程"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"结束进程失败: {str(e)}"
            )


class SystemInfoSkill:
    """
    🖥️ System Info Skill for PyClaw
    查看系统信息、进程、资源使用情况
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="System Info",
            description="查看系统信息、CPU/内存/磁盘使用、进程管理等",
            author="PyClaw Team",
            version="1.0.0",
            tags=["system", "tools", "系统", "工具"],
            website="https://github.com/pyclaw/skill-system-info"
        )
    
    def get_tools(self):
        return [
            SystemInfoTool(),
            ProcessListTool(),
            KillProcessTool()
        ]
    
    async def initialize(self) -> bool:
        print("[System Info Skill] 系统信息 Skill 初始化完成")
        return True
    
    async def cleanup(self) -> None:
        print("[System Info Skill] 系统信息 Skill 已卸载")
