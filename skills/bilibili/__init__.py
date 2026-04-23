"""
📺 Bilibili Skill for PyClaw
发布 B站 动态、查看动态数据等功能
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

from pyclaw.skill import SkillMetadata
from pyclaw.types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "BilibiliSkill"


@dataclass
class PublishDynamicTool:
    """发布 B站 纯文字动态"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="bilibili_publish_dynamic",
            description="发布 Bilibili 纯文字动态。支持话题标签、@他人等功能",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "动态内容，支持换行和话题标签（#话题）"
                    },
                    "cookie_file": {
                        "type": "string",
                        "description": "（可选）Cookie 文件路径，默认从 Skill 目录的 Cookie.txt 读取",
                        "default": "skills/bilibili/Cookie.txt"
                    }
                },
                "required": ["content"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        content = params.get("content", "").strip()
        cookie_file = params.get("cookie_file", "skills/bilibili/Cookie.txt")
        
        if not content:
            return ToolResult(success=False, content="", error="动态内容不能为空")
        
        # 读取 Cookie
        cookie_path = Path(cookie_file)
        if not cookie_path.exists():
            # 也尝试从 U 盘根目录读取
            alt_path = Path("../Cookie.txt")
            if alt_path.exists():
                cookie_path = alt_path
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"未找到 Cookie 文件: {cookie_file}\n请在 Skill 目录放置 Cookie.txt，包含 SESSDATA、bili_jct、buvid3"
                )
        
        try:
            cookies = {}
            with open(cookie_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        cookies[key.strip()] = value.strip()
            
            SESSDATA = cookies.get('SESSDATA', '')
            BILI_JCT = cookies.get('bili_jct', '')
            BUVID3 = cookies.get('buvid3', '')
            
            if not SESSDATA or not BILI_JCT:
                return ToolResult(
                    success=False,
                    content="",
                    error="Cookie 不完整：需要 SESSDATA 和 bili_jct"
                )
            
            # 导入并调用 Bilibili API
            import asyncio
            from bilibili_api import Credential, dynamic
            from bilibili_api.dynamic import BuildDynamic
            
            cred = Credential(
                sessdata=SESSDATA,
                bili_jct=BILI_JCT,
                buvid3=BUVID3
            )
            
            builder = BuildDynamic()
            builder.add_text(content)
            
            result = await dynamic.send_dynamic(builder, cred)
            
            dynamic_id = result.get('dynamic_id', '未知')
            return ToolResult(
                success=True,
                content=f"✅ B站 动态发布成功！\n\n动态 ID: {dynamic_id}\n\n内容预览:\n{content[:200]}..." if len(content) > 200 else content
            )
            
        except ImportError:
            return ToolResult(
                success=False,
                content="",
                error="缺少依赖: 请运行 pip install bilibili-api-python"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"发布失败: {str(e)}"
            )


class BilibiliSkill:
    """
    📺 Bilibili Skill for PyClaw
    发布 B站 动态、查看数据等功能
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Bilibili",
            description="发布 Bilibili 纯文字动态，支持话题标签和自定义内容",
            author="PyClaw Team",
            version="1.0.0",
            tags=["bilibili", "social", "社交"],
            website="https://github.com/pyclaw/skill-bilibili"
        )
    
    def get_tools(self):
        return [PublishDynamicTool()]
    
    async def initialize(self) -> bool:
        print("[Bilibili Skill] B站 Skill 初始化完成")
        return True
    
    async def cleanup(self) -> None:
        print("[Bilibili Skill] B站 Skill 已卸载")
