---
name: ppt
description: PPT制作技能 v3.0 — 模板引擎 · 10套布局 · 纯Python运行时
---

# 📊 PPT制作技能 v3.0

纯 Python 运行时（python-pptx），零 Node.js 依赖。模板预生成，直接使用。

## 🎯 10套布局

| # | 类型 | 风格 | 字段 |
|---|------|------|------|
| 1 | `title` / `title_dark` | 深色封面 | title, subtitle |
| 2 | `title_center` | 深色居中封面 | title, subtitle |
| 3 | `content_light` / `content` | 浅色内容 | title, content |
| 4 | `content_dark` | 深色内容 | title, content |
| 5 | `two_column` / `two_column_light` | 浅色双栏 | title, content, content2 |
| 6 | `two_column_dark` | 深色双栏 | title, content, content2 |
| 7 | `features_dark` / `features` | 深色列表 | title, content |
| 8 | `process_light` / `process` | 浅色步骤 | title, content |
| 9 | `quote_dark` / `quote` | 深色引用 | title(引用), subtitle(作者) |
| 10 | `end` / `end_dark` | 深色结束 | title(默认Thanks), subtitle |

## 🛠️ 工具

### create_modern_pptx — 推荐
```json
{
  "slides": "[{\"type\":\"title\",\"title\":\"标题\",\"subtitle\":\"副标题\"},{\"type\":\"content_dark\",\"title\":\"内容\",\"content\":[\"项目1\",\"项目2\"]},{\"type\":\"end\",\"title\":\"谢谢\"}]",
  "output": ""
}
```

### create_pptx — 基础PPT
### create_smart_ppt — 智能PPT

## 📦 依赖

仅需 `python-pptx`：`pip install python-pptx`

## 🔄 版本

### v3.0.0 (2026-05-23)
- 🚀 模板引擎：10套精美布局
- 🎨 深色/浅色双风格
- 📐 双栏对比、引用金句、步骤流程
- 🐍 纯Python，零Node.js
