---
name: ppt
description: PPT制作技能 - 快速创建和编辑专业演示文稿，支持智能排版、图表、表格、图片等内容添加
---

# 📊 PPT制作技能

PyClaw的PPT制作技能提供了专业的PowerPoint演示文稿创建和编辑功能，支持快速生成美观的演示文稿。

## 🎯 主要功能

### 1. 创建新PPT
- 快速创建带有标题页的演示文稿
- 支持自定义标题和副标题
- 自动保存到当前目录
- 支持多种设计主题

### 2. 智能PPT生成
- 根据内容自动排版
- 支持章节式内容输入（JSON格式或换行分隔）
- 自动选择合适的幻灯片布局
- 智能标题和内容匹配

### 3. 编辑幻灯片
- 向现有PPT添加新幻灯片
- 支持文本内容和图片添加
- 提供多种幻灯片布局选项

### 4. 内容添加
- 添加文本内容
- 添加图片（支持常见图片格式）
- 添加图表（柱状图、折线图、饼图等）
- 添加表格（支持自定义样式）

## 📦 依赖库

需要以下Python库：
- **python-pptx** - 专业的PPT操作库
- **lxml** - XML处理库

## 🛠️ 工具列表

### create_pptx - 创建新PPT文件
```json
{
  "name": "create_pptx",
  "description": "创建新的PPT文件，支持自定义标题、副标题和模板样式",
  "parameters": {
    "title": "新演示文稿",
    "subtitle": "PyClaw 智能创建",
    "theme": "blue、green、red、purple、orange、cyan、gray",
    "output": "自动生成的文件路径"
  }
}
```

### create_smart_ppt - 智能生成完整PPT
```json
{
  "name": "create_smart_ppt",
  "description": "智能生成完整PPT，根据标题和内容自动排版",
  "parameters": {
    "title": "项目报告",
    "sections": "内容章节（JSON格式或换行分隔）",
    "theme": "blue、green、red、purple、orange、cyan、gray",
    "output": "自动生成的文件路径"
  }
}
```

## 🔧 使用方法

### 快速开始
```python
# 创建智能PPT
ppt = PPTSkill()
result = await ppt.create_smart_ppt({
    "title": "产品发布计划",
    "sections": """
[
    {"title": "产品概述", "content": "介绍产品的核心功能和价值"},
    {"title": "市场分析", "content": "分析目标市场和竞争态势"},
    {"title": "功能特性", "content": "详细说明产品的主要功能"},
    {"title": "实施计划", "content": "产品开发和发布的时间安排"},
    {"title": "总结", "content": "对项目的总结和展望"}
]
""",
    "theme": "blue"
})
```

### 简单使用
```python
# 创建新PPT
ppt = PPTSkill()
result = await ppt.create_pptx({
    "title": "产品发布会",
    "subtitle": "2024年第一季度"
})
```

## 📝 高级功能

### 幻灯片布局
支持多种幻灯片布局：
- 标题幻灯片（0）
- 标题和内容（1）
- 节标题（2）
- 两列内容（3）
- 比较（4）
- 标题和图表（5）
- 标题和表格（6）
- 空白（7）
- 内容和标题（8）
- 图片标题（9）

### 图片格式支持
- PNG（推荐）
- JPEG
- BMP
- GIF
- TIFF

### 文本格式
支持基本的文本格式化：
- 字体类型
- 字体大小
- 字体颜色
- 粗体/斜体/下划线

## 🐛 故障排除

### 常见错误
1. `ImportError: No module named pptx` - 需要安装 python-pptx 库：
   ```bash
   pip install python-pptx
   ```

2. `FileNotFoundError: [Errno 2] No such file or directory` - 输入路径或图片路径不正确

3. `ValueError: invalid literal for int() with base 10: 'abc'` - 幻灯片索引需要是数字

## 📚 参考资料

- [python-pptx 官方文档](https://python-pptx.readthedocs.io/)
- [Microsoft Office Open XML](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-pptx)

## 🔄 版本更新

### v1.1.0（2026-05-13）
- **智能生成**：新增智能PPT生成功能，支持根据章节内容自动排版
- **图表支持**：添加图表（柱状图、折线图、饼图等）功能
- **表格支持**：添加表格功能，支持自定义行列数和样式
- **设计主题**：支持7种设计主题（blue、green、red、purple、orange、cyan、gray）
- **智能布局**：自动根据内容长度选择合适的幻灯片布局
- **内容解析**：支持JSON格式和换行分隔的章节内容
- **单位优化**：使用厘米作为位置和尺寸单位，更符合用户习惯

### v1.0.0（2024-05-12）
- 首次发布
- 支持PPT创建和基本编辑
- 添加文本和图片功能