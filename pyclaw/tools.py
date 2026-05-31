"""
内置工具实现
"""
import os
import subprocess
import asyncio
from dataclasses import dataclass
from typing import Dict, Any
from .pyclaw_types import ToolDefinition, ToolResult


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
            return ToolResult(success=False, content="", error="File path cannot be empty")
        
        try:
            if not os.path.exists(file_path):
                return ToolResult(success=False, content="", error=f"文件不存在: {file_path}")
            
            if not os.path.isfile(file_path):
                return ToolResult(success=False, content="", error=f"路径不是文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 限制返回大小，防止太大
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncated, file too long)"
            
            return ToolResult(success=True, content=f"文件内容 ({file_path}):\n\n{content}")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Failed to read file: {str(e)}")


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
                },
                "required": ["dir_path"]
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
            return ToolResult(success=False, content="", error=f"Failed to list directory: {str(e)}")


@dataclass
class ExecTool:
    """命令执行工具 - 执行 shell 命令"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="exec_command",
            description="执行系统 shell 命令，返回输出结果。支持 Windows、Linux、macOS",
            # 自动适配系统命令风格（cmd / powershell / bash）,
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令，例如 'ls -la' 或 'python --version'"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds (default 30)",
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
            return ToolResult(success=False, content="", error="Command cannot be empty")
        
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
                output.append(f"--- STDOUT ---\n{result.stdout[:5000]}")
                if len(result.stdout) > 5000:
                    output.append("... (truncated, too long)")
            
            if result.stderr:
                output.append(f"--- STDERR ---\n{result.stderr[:3000]}")
                if len(result.stderr) > 3000:
                    output.append("... (stderr truncated, too long)")
            
            output.append(f"\nExit code: {result.returncode}")
            
            return ToolResult(success=True, content="\n".join(output))
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, content="", error=f"Command timed out ({timeout}s)")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Command execution failed: {str(e)}")


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
            return ToolResult(success=False, content="", error=f"Failed to get time: {str(e)}")


@dataclass
class WebSearchTool:
    """免费互联网搜索工具（通过 Exa MCP）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="搜索互联网获取最新信息、新闻、知识等",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量（默认5条）",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        num_results = params.get("num_results", 5)
        try:
            # 调用 mcporter 执行 Exa 搜索
            cmd = f"mcporter call 'exa.web_search_exa(query: \"{query}\", numResults: {num_results})'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Search failed: {stderr.decode()[:500]}"
                )
            
            # 解析结果
            output = stdout.decode()
            lines = output.strip().split('\n')
            results = []
            current = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Title:'):
                    if current.get('title'):
                        results.append(current)
                    current = {'title': line[6:].strip()}
                elif line.startswith('URL:'):
                    current['url'] = line[4:].strip()
                elif line.startswith('Published:'):
                    current['published'] = line[10:].strip()
                elif line.startswith('Author:'):
                    current['author'] = line[7:].strip()
                elif line.startswith('Highlights:'):
                    current['highlights'] = ''
                elif current.get('highlights') is not None and line:
                    current['highlights'] = line[:300]
            
            if current.get('title'):
                results.append(current)
            
            if not results:
                return ToolResult(
                    success=True,
                    content=f"Search '{query}' returned no results",
                    error=None
                )
            
            # 格式化输出
            text_parts = [f"## 搜索结果: {query}\n"]
            for i, r in enumerate(results[:num_results], 1):
                text_parts.append(f"**{i}. {r.get('title', '无标题')}**")
                if r.get('url'):
                    text_parts.append(f"   链接: {r['url']}")
                if r.get('published') and r['published'] != 'N/A':
                    text_parts.append(f"   时间: {r['published']}")
                if r.get('highlights'):
                    text_parts.append(f"   摘要: {r['highlights'][:200]}")
                text_parts.append("")
            
            return ToolResult(
                success=True,
                content='\n'.join(text_parts),
                error=None
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"搜索异常: {str(e)}"
            )


@dataclass
class WebFetchTool:
    """抓取网页内容工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="fetch_url",
            description="抓取并读取网页的文本内容，获取页面上的实际信息。配合 web_search 使用，搜索到相关链接后可进一步读取页面内容",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要读取的网页 URL"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "最大返回字符数，默认 3000"
                    }
                },
                "required": ["url"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        url = params.get("url", "")
        max_chars = params.get("max_chars", 3000)
        if not url:
            return ToolResult(success=False, content="", error="需要 url 参数")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PyClaw/1.0)"})
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "text/html" in content_type or "text/plain" in content_type:
                    import re
                    text = resp.text
                    # 简单提取文本（去掉 script/style 标签）
                    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'<[^>]+>', '', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if len(text) > max_chars:
                        text = text[:max_chars] + "\n\n[truncated, too long]"
                    return ToolResult(success=True, content=text, error="")
                else:
                    return ToolResult(success=True, content=f"[非HTML内容] 类型: {content_type}, 大小: {len(resp.content)} bytes", error="")
        except Exception as e:
            return ToolResult(success=False, content="", error=f"Fetch failed: {str(e)[:500]}")
