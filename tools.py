"""
内置工具实现
"""
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Any
from .types import ToolDefinition, ToolResult


@dataclass
class FileReadTool:
    """文件读取工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="读取本地文件内容，支持相对路径和绝对路径",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件路径，例如 './test.py' 或 '/home/user/file.txt'"
                    }
                },
                "required": ["file_path"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        file_path = params.get("file_path", "")
        if not file_path:
            return ToolResult(success=False, content="", error="文件路径不能为空")
        
        try:
            if not os.path.exists(file_path):
                return ToolResult(success=False, content="", error=f"文件不存在: {file_path}")
            
            if not os.path.isfile(file_path):
                return ToolResult(success=False, content="", error=f"路径不是文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 限制返回大小，防止太大
            if len(content) > 10000:
                content = content[:10000] + "\n... (文件过长，已截断)"
            
            return ToolResult(success=True, content=f"文件内容 ({file_path}):\n\n{content}")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"读取文件失败: {str(e)}")


@dataclass
class ListDirTool:
    """列出目录内容工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_directory",
            description="列出指定目录下的文件和子目录",
            parameters={
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "目录路径，默认为当前目录",
                        "default": "."
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        dir_path = params.get("dir_path", ".")
        
        try:
            if not os.path.exists(dir_path):
                return ToolResult(success=False, content="", error=f"目录不存在: {dir_path}")
            
            if not os.path.isdir(dir_path):
                return ToolResult(success=False, content="", error=f"不是目录: {dir_path}")
            
            items = os.listdir(dir_path)
            items.sort()
            
            result = []
            for item in items:
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    result.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    result.append(f"📄 {item} ({size} bytes)")
            
            content = f"目录内容 ({dir_path}):\n\n" + "\n".join(result)
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=f"列出目录失败: {str(e)}")


@dataclass
class ExecTool:
    """命令执行工具 - 执行 shell 命令"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="exec_command",
            description="执行系统 shell 命令，返回输出结果。支持 Linux/Mac 命令",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令，例如 'ls -la' 或 'python --version'"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "命令超时时间（秒），默认 30 秒",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        command = params.get("command", "")
        timeout = params.get("timeout", 30)
        
        if not command:
            return ToolResult(success=False, content="", error="命令不能为空")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            output = []
            if result.stdout:
                output.append(f"标准输出:\n{result.stdout[:5000]}")
                if len(result.stdout) > 5000:
                    output.append("... (输出过长，已截断)")
            
            if result.stderr:
                output.append(f"标准错误:\n{result.stderr[:3000]}")
                if len(result.stderr) > 3000:
                    output.append("... (错误输出过长，已截断)")
            
            output.append(f"\n退出码: {result.returncode}")
            
            return ToolResult(success=True, content="\n".join(output))
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, content="", error=f"命令执行超时（{timeout}秒）")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"命令执行失败: {str(e)}")


@dataclass
class TimeTool:
    """获取当前时间工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_current_time",
            description="获取当前时间和日期",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区，例如 'Asia/Shanghai' 或 'UTC'",
                        "default": "Asia/Shanghai"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        from datetime import datetime
        import pytz
        
        tz_name = params.get("timezone", "Asia/Shanghai")
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            time_str = now.strftime("%Y年%m月%d日 %H:%M:%S (%Z)")
            return ToolResult(success=True, content=f"当前时间: {time_str}")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取时间失败: {str(e)}")
