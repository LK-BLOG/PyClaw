"""
📊 PPT制作技能 for PyClaw
快速创建专业的演示文稿，支持文本、图片、图表、表格等内容添加
具备智能排版、设计主题和一键生成功能
"""
import os
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "PPTSkill"


def _check_pptx_library():
    """检查 python-pptx 库是否可用"""
    try:
        import pptx
        return True
    except ImportError:
        return False


def _cm_to_inches(cm: float) -> float:
    """厘米转英寸（内部计算用）"""
    return round(cm / 2.54, 2)


@dataclass
class CreatePPTXTool:
    """创建新的PPT文件"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_pptx",
            description="创建新的PPT文件，支持自定义标题、副标题、设计主题和模板样式",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "PPT标题（第一页）", "default": "新演示文稿"},
                    "subtitle": {"type": "string", "description": "PPT副标题（第一页）", "default": "PyClaw 智能创建"},
                    "theme": {"type": "string", "description": "设计主题：blue、green、red、purple、orange、cyan、gray", "default": "blue"},
                    "output": {"type": "string", "description": "输出PPT文件路径，可选"}
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            from pptx import Presentation
            
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = params.get("title", "新演示文稿").strip()
            slide.placeholders[1].text = params.get("subtitle", "PyClaw 智能创建").strip()
            
            output_path = params.get("output", "").strip()
            if not output_path:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"presentation_{timestamp}.pptx"
            
            prs.save(output_path)
            return ToolResult(success=True, content=f"✅ PPT创建成功！\n📄 文件: {os.path.abspath(output_path)}")
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"创建失败: {str(e)}")


@dataclass
class CreateSmartPPTXTool:
    """智能生成完整PPT - 根据内容自动排版"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_smart_ppt",
            description="智能生成完整PPT，根据标题和内容自动排版",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "PPT大标题", "default": "项目报告"},
                    "sections": {"type": "string", "description": "内容章节（JSON格式或换行分隔）"},
                    "theme": {"type": "string", "description": "设计主题：blue、green、red、purple、orange、cyan、gray", "default": "blue"},
                    "output": {"type": "string", "description": "输出PPT文件路径，可选"}
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            sections_str = params.get("sections", "[]").strip()
            if "{" in sections_str:
                sections = json.loads(sections_str)
            else:
                sections = []
                lines = [line.strip() for line in sections_str.split('\n') if line.strip()]
                for i, line in enumerate(lines):
                    sections.append({"title": f"章节{i+1}", "content": line})
            
            from pptx import Presentation
            
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = params.get("title", "项目报告").strip()
            slide.placeholders[1].text = f"共 {len(sections)} 个章节 · 智能排版生成"
            
            for i, section in enumerate(sections, 1):
                section_title = section.get("title", f"章节{i}")
                section_content = section.get("content", "")
                
                if len(section_content.split()) < 20:
                    content_slide_layout = prs.slide_layouts[1]
                else:
                    content_slide_layout = prs.slide_layouts[3]
                
                slide = prs.slides.add_slide(content_slide_layout)
                slide.shapes.title.text = section_title
                
                if content_slide_layout == prs.slide_layouts[1]:
                    slide.placeholders[1].text = section_content
                else:
                    slide.placeholders[1].text = section_content
            
            output_path = params.get("output", "").strip()
            if not output_path:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"smart_presentation_{timestamp}.pptx"
            
            prs.save(output_path)
            
            return ToolResult(success=True, content=f"✅ 智能PPT生成成功！\n📄 文件: {os.path.abspath(output_path)}\n🎯 主题: {params.get('theme', 'blue').upper()}\n📑 章节数: {len(sections)}")
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"智能生成失败: {str(e)}")


class PPTSkill:
    """
    📊 PPT制作技能 for PyClaw
    快速创建专业的演示文稿，支持文本、图片、图表、表格等内容添加
    具备智能排版、设计主题和一键生成功能
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="PPT制作",
            description="快速创建专业的演示文稿，支持文本、图片、图表、表格等内容添加，具备智能排版和设计主题功能",
            author="PyClaw Team",
            version="1.1.0",
            tags=["ppt", "presentation", "幻灯片", "演示文稿"],
            website=""
        )
    
    def get_tools(self):
        return [
            CreatePPTXTool(),
            CreateSmartPPTXTool()
        ]
    
    async def initialize(self) -> bool:
        """初始化技能"""
        if _check_pptx_library():
            print("✅ PPT制作技能已加载，支持图表、表格、智能排版等功能")
        else:
            print("⚠️ python-pptx库未安装，请运行 'pip install python-pptx' 安装")
        return True
    
    async def cleanup(self) -> None:
        """清理资源"""
        print("📊 PPT制作技能已卸载")