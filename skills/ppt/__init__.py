"""
📊 PPT制作技能 for PyClaw
快速创建专业的演示文稿，支持文本、图片、图表等内容添加
"""
import os
import tempfile
from dataclasses import dataclass
from typing import Dict, Any

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


@dataclass
class CreatePPTXTool:
    """创建新的PPT文件"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_pptx",
            description="创建新的PPT文件，支持自定义标题、副标题和模板样式",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "PPT标题（第一页）",
                        "default": "新演示文稿"
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "PPT副标题（第一页）",
                        "default": "PyClaw 智能创建"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出PPT文件路径，可选（默认自动生成）"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        title = params.get("title", "新演示文稿").strip()
        subtitle = params.get("subtitle", "PyClaw 智能创建").strip()
        output_path = params.get("output", "").strip()
        
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            from pptx import Presentation
            from pptx.util import Inches
            
            # 创建新的PPT
            prs = Presentation()
            
            # 添加标题幻灯片
            title_slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(title_slide_layout)
            slide.shapes.title.text = title
            slide.placeholders[1].text = subtitle
            
            # 自动生成输出路径
            if not output_path:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"presentation_{timestamp}.pptx"
            
            # 保存PPT
            prs.save(output_path)
            
            result = f"""✅ PPT 创建成功！

📄 文件名称: {os.path.basename(output_path)}
📍 文件位置: {os.path.abspath(output_path)}

🎯 内容:
- 标题: {title}
- 副标题: {subtitle}
"""
            
            return ToolResult(success=True, content=result)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"创建PPT失败: {str(e)}")


@dataclass
class AddSlideTool:
    """向PPT添加新幻灯片"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="add_slide",
            description="向已有的PPT文件添加新的幻灯片，支持标题、内容、图片等",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入PPT文件路径"
                    },
                    "title": {
                        "type": "string",
                        "description": "幻灯片标题",
                        "default": "新幻灯片"
                    },
                    "content": {
                        "type": "string",
                        "description": "幻灯片内容（文本）"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "图片路径（可选）"
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_path = params.get("input", "").strip()
        title = params.get("title", "新幻灯片").strip()
        content = params.get("content", "").strip()
        image_path = params.get("image_path", "").strip()
        
        if not os.path.exists(input_path):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_path}")
        
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            from pptx import Presentation
            from pptx.util import Inches
            
            # 打开PPT
            prs = Presentation(input_path)
            
            # 添加幻灯片
            title_and_content_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(title_and_content_layout)
            slide.shapes.title.text = title
            
            if content:
                slide.placeholders[1].text = content
            
            if image_path and os.path.exists(image_path):
                left = Inches(1)
                top = Inches(1)
                slide.shapes.add_picture(image_path, left, top, width=Inches(6))
            
            # 保存PPT
            prs.save(input_path)
            
            result = f"""✅ 幻灯片添加成功！

📄 文件名称: {os.path.basename(input_path)}
📍 文件位置: {os.path.abspath(input_path)}

🎯 幻灯片内容:
- 标题: {title}
- 内容: {content if content else '无文本内容'}
- 图片: {'已添加' if image_path and os.path.exists(image_path) else '无图片'}
"""
            
            return ToolResult(success=True, content=result)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"添加幻灯片失败: {str(e)}")


@dataclass
class AddTextTool:
    """向幻灯片添加文本"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="add_text",
            description="向幻灯片添加文本内容",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入PPT文件路径"
                    },
                    "slide_index": {
                        "type": "integer",
                        "description": "幻灯片索引（从0开始）",
                        "default": 0
                    },
                    "text": {
                        "type": "string",
                        "description": "要添加的文本内容"
                    },
                    "x": {
                        "type": "number",
                        "description": "x坐标（英寸）",
                        "default": 1
                    },
                    "y": {
                        "type": "number",
                        "description": "y坐标（英寸）",
                        "default": 1
                    },
                    "width": {
                        "type": "number",
                        "description": "文本框宽度（英寸）",
                        "default": 6
                    },
                    "height": {
                        "type": "number",
                        "description": "文本框高度（英寸）",
                        "default": 2
                    }
                },
                "required": ["input", "text"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_path = params.get("input", "").strip()
        slide_index = params.get("slide_index", 0)
        text = params.get("text", "").strip()
        x = params.get("x", 1)
        y = params.get("y", 1)
        width = params.get("width", 6)
        height = params.get("height", 2)
        
        if not os.path.exists(input_path):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_path}")
        
        if not text:
            return ToolResult(success=False, content="", error="文本内容不能为空")
        
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            from pptx import Presentation
            from pptx.util import Inches
            
            # 打开PPT
            prs = Presentation(input_path)
            
            if slide_index < 0 or slide_index >= len(prs.slides):
                return ToolResult(success=False, content="", error=f"幻灯片索引无效，有效范围: 0 - {len(prs.slides)-1}")
            
            # 获取幻灯片
            slide = prs.slides[slide_index]
            
            # 添加文本框
            left = Inches(x)
            top = Inches(y)
            width_in = Inches(width)
            height_in = Inches(height)
            
            textbox = slide.shapes.add_textbox(left, top, width_in, height_in)
            text_frame = textbox.text_frame
            text_frame.text = text
            
            # 保存PPT
            prs.save(input_path)
            
            result = f"""✅ 文本添加成功！

📄 文件名称: {os.path.basename(input_path)}
📍 文件位置: {os.path.abspath(input_path)}
🎯 幻灯片: 第 {slide_index+1} 页（索引 {slide_index}）

📝 添加的文本:
{text}
"""
            
            return ToolResult(success=True, content=result)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"添加文本失败: {str(e)}")


@dataclass
class AddImageTool:
    """向幻灯片添加图片"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="add_image",
            description="向幻灯片添加图片",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入PPT文件路径"
                    },
                    "slide_index": {
                        "type": "integer",
                        "description": "幻灯片索引（从0开始）",
                        "default": 0
                    },
                    "image_path": {
                        "type": "string",
                        "description": "图片文件路径"
                    },
                    "x": {
                        "type": "number",
                        "description": "x坐标（英寸）",
                        "default": 1
                    },
                    "y": {
                        "type": "number",
                        "description": "y坐标（英寸）",
                        "default": 1
                    },
                    "width": {
                        "type": "number",
                        "description": "图片宽度（英寸），默认自动大小",
                        "default": 0
                    }
                },
                "required": ["input", "image_path"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_path = params.get("input", "").strip()
        slide_index = params.get("slide_index", 0)
        image_path = params.get("image_path", "").strip()
        x = params.get("x", 1)
        y = params.get("y", 1)
        width = params.get("width", 0)
        
        if not os.path.exists(input_path):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_path}")
        
        if not image_path or not os.path.exists(image_path):
            return ToolResult(success=False, content="", error=f"图片不存在: {image_path}")
        
        if not _check_pptx_library():
            return ToolResult(success=False, content="", error="需要安装 python-pptx 库: pip install python-pptx")
        
        try:
            from pptx import Presentation
            from pptx.util import Inches
            
            # 打开PPT
            prs = Presentation(input_path)
            
            if slide_index < 0 or slide_index >= len(prs.slides):
                return ToolResult(success=False, content="", error=f"幻灯片索引无效，有效范围: 0 - {len(prs.slides)-1}")
            
            # 获取幻灯片
            slide = prs.slides[slide_index]
            
            # 添加图片
            left = Inches(x)
            top = Inches(y)
            
            if width > 0:
                # 固定宽度
                slide.shapes.add_picture(image_path, left, top, width=Inches(width))
            else:
                # 自动大小
                slide.shapes.add_picture(image_path, left, top)
            
            # 保存PPT
            prs.save(input_path)
            
            result = f"""✅ 图片添加成功！

📄 文件名称: {os.path.basename(input_path)}
📍 文件位置: {os.path.abspath(input_path)}
🎯 幻灯片: 第 {slide_index+1} 页（索引 {slide_index}）

🖼️ 图片: {os.path.basename(image_path)}
"""
            
            return ToolResult(success=True, content=result)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"添加图片失败: {str(e)}")


class PPTSkill:
    """
    📊 PPT制作技能 for PyClaw
    快速创建和编辑专业演示文稿
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="PPT制作",
            description="快速创建和编辑专业的演示文稿，支持文本、图片、形状等内容添加",
            author="PyClaw Team",
            version="1.0.0",
            tags=["ppt", "powerpoint", "presentation", "演示文稿", "制作"],
            website=""
        )
    
    def get_tools(self):
        return [
            CreatePPTXTool(),
            AddSlideTool(),
            AddTextTool(),
            AddImageTool()
        ]
    
    async def initialize(self) -> bool:
        print("[PPT制作技能] 📊 PPT制作技能初始化...")
        if _check_pptx_library():
            print("[PPT制作技能] ✅ python-pptx 库已找到，准备就绪")
        else:
            print("[PPT制作技能] ⚠️  python-pptx 库未安装，部分功能可能不可用")
            print("[PPT制作技能] 💡  安装命令: pip install python-pptx")
        print(f"[PPT制作技能] 🎯  已注册 {len(self.get_tools())} 个PPT制作工具")
        return True
    
    async def cleanup(self) -> None:
        print("[PPT制作技能] 幻灯片制作工具已卸载")
