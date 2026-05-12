---
name: ppt
description: PPT制作技能 - 快速创建和编辑专业演示文稿，支持文本、图片、图表等内容添加
---

# 📊 PPT制作技能

PyClaw的PPT制作技能提供了专业的PowerPoint演示文稿创建和编辑功能，支持快速生成美观的演示文稿。

## 🎯 主要功能

### 1. 创建新PPT
- 快速创建带有标题页的演示文稿
- 支持自定义标题和副标题
- 自动保存到当前目录

### 2. 编辑幻灯片
- 向现有PPT添加新幻灯片
- 支持文本内容和图片添加
- 提供多种幻灯片布局选项

### 3. 内容添加
- 添加文本内容
- 添加图片（支持常见图片格式）
- 支持自定义位置和尺寸

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
    "output": "自动生成的文件路径"
  }
}
```

### add_slide - 向PPT添加新幻灯片
```json
{
  "name": "add_slide",
  "description": "向已有的PPT文件添加新的幻灯片，支持标题、内容、图片等",
  "parameters": {
    "input": "输入PPT文件路径",
    "title": "新幻灯片",
    "content": "幻灯片内容",
    "image_path": "图片路径"
  }
}
```

### add_text - 向幻灯片添加文本
```json
{
  "name": "add_text",
  "description": "向幻灯片添加文本内容",
  "parameters": {
    "input": "输入PPT文件路径",
    "slide_index": 0,
    "text": "要添加的文本",
    "x": 1,
    "y": 1,
    "width": 6,
    "height": 2
  }
}
```

### add_image - 向幻灯片添加图片
```json
{
  "name": "add_image",
  "description": "向幻灯片添加图片",
  "parameters": {
    "input": "输入PPT文件路径",
    "slide_index": 0,
    "image_path": "图片文件路径",
    "x": 1,
    "y": 1,
    "width": "自动大小"
  }
}
```

## 🔧 使用方法

### 快速开始
```python
# 创建新PPT
ppt = PPTSkill()
result = await ppt.create_pptx(title="项目报告", subtitle="2024年Q1")
print(result)

# 添加幻灯片
await ppt.add_slide(input="presentation_20240101_100000.pptx", 
                    title="市场分析", 
                    content="市场份额持续增长...")
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

### v1.0.0（2024-05-12）
- 首次发布
- 支持PPT创建和基本编辑
- 添加文本和图片功能
