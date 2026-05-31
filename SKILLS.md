# 🦞 PyClaw Skill 开发手册

> 双轨制：声明式（推荐） + 编程式（高级）

---

## 快速创建 Skill

你只需要一个 **SKILL.md** 文件：

```
skills/my-tool/
└── SKILL.md       ← 纯 Markdown，LLM 自己读
```

不需要写 Python。不需要注册工具。不需要了解 Protocol。

### 格式

```markdown
---
name: my-tool
description: 一行描述（会自动注入 system prompt）
---

## Instructions

LLM 从这里读懂这个 Skill 的用途、用法、最佳实践。

## Examples

好的和坏的调用模式对比。
```

### 示例：天气 Skill

```markdown
---
name: weather
description: 查询全球天气信息
---

## Instructions

使用 `curl wttr.in/<city>` 或 `exec` 工具查询天气。

## Example

User: 北京今天天气怎么样？
Assistant: 用 `curl wttr.in/Beijing?format=3` 查一下
```

只要把文件放到 `skills/weather/SKILL.md`，PyClaw 启动时自动加载，
内容注入到 LLM 的 system prompt。不需要任何 Python 代码。

---

## 双轨制

| 方式 | 文件 | 复杂度 | 适用场景 |
|------|------|--------|----------|
| **声明式** 🆕 | `SKILL.md` | 低 | 大多数 Skill：工具组合、领域知识、工作流 |
| **编程式** | `__init__.py` + `SKILL.md` | 高 | 需要自定义 Python 执行的复杂 Skill |

优先用声明式。只有需要真实调用系统 API、复杂计算、文件操作时才用编程式。

### 声明式 （推荐）

LLM 用系统内置工具（`exec` / `read` / `write` / `listdir`）来实现 Skill 功能。
SKILL.md 只是教 LLM **什么时候**、**怎么** 用这些工具。

适合的场景：
- 系统管理（查磁盘、看进程、管理文件）
- 数据查询（查日志、读配置）
- 工作流编排（多步操作组合）
- 领域知识（代码规范、架构指南）
- 模板（PPT 布局、代码生成规则）

### 编程式（高级）

需要自定义 Python 执行逻辑时使用。参见下方「编程式 Skill」章节。

---

## 声明式 Skill 详解

### SKILL.md 规范

使用 YAML frontmatter + Markdown 正文：

```yaml
---
name: skill-name           # 必填，唯一标识
description: 一行描述       # 必填，注入 system prompt
---
```

正文用自然语言写「怎么用、什么时候用、注意事项」。

### 最佳实践

1. **描述要具体** — 不是"处理文件"，而是"将 Markdown 文件批量转成 PDF"
2. **给例子** — LLM 从例子中理解得更快
3. **说清楚什么时候不该用** — 避免 LLM 错误触发

### 示例：桌面路径

```markdown
---
name: desktop-path
description: Detect Chinese 桌面 vs English Desktop path
---

## Instructions

Use `ls ~/桌面` and `ls ~/Desktop` to check which exists.
Report the actual existing path. Create if neither exists.

## Rules

- Always check both paths
- Report the ACTUAL result, not guessed paths
```

### 示例：代码规范

```markdown
---
name: python-style
description: Python 代码风格规范
---

## Rules

- 4 spaces, no tabs
- Max line length: 100
- Use type hints for all functions
- Docstrings in Google style
```

### 如何加载

1. 在 `skills/` 下创建目录
2. 放入 `SKILL.md`
3. 重启 PyClaw

```
skills/
├── weather/
│   └── SKILL.md
├── desktop-path/
│   └── SKILL.md
└── python-style/
    └── SKILL.md
```

系统自动发现，内容注入到 system prompt。

---

## 编程式 Skill

需要自定义 Python 执行逻辑时使用。

### 结构

```
skills/my-skill/
├── __init__.py     # Python 代码
└── SKILL.md        # 文档（也加载到 system prompt）
```

### 基础模板

```python
from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult

SKILL_CLASS = "MySkill"

class MySkill:
    def __init__(self):
        self._metadata = SkillMetadata(
            name="MySkill",
            version="1.0.0",
            description="My skill description",
            author="Your Name",
            tags=["example"],
        )
    
    @property
    def metadata(self) -> SkillMetadata:
        return self._metadata
    
    def get_tools(self) -> list:
        return [MyTool()]
    
    async def initialize(self) -> bool:
        return True

class MyTool:
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="Tool description",
            parameters={"type": "object", "properties": {}},
        )
    
    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=True, content="done")
```

### 什么时候用编程式？

| 场景 | 示例 |
|------|------|
| 需要 HTTP 请求 | 查天气、调外部 API |
| 需要复杂文件操作 | 生成 PPT、处理视频 |
| 需要访问数据库 | 查询、写入 |
| 需要第三方库 | requests, pandas, pillow |

大多数场景先用声明式，不够了再升级编程式。

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Skill 不加载 | SKILL.md 文件名不对 | 确认文件名是 `SKILL.md`（大写 S） |
| LLM 不用我的 Skill | 描述不够清楚 | 加例子、说清楚什么时候该用 |
| 编程式 Skill 报错 | 循环导入 | 用 `from .xxx import` 相对导入 |
