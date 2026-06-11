# CHANGELOG

## [Unreleased]

### 🎨 CLI 重设计
- 全新的 Claude Code 风格界面：启动清屏 + 终端高度填充
- ASCII art PYCLAW 大字（蓝+黄双色，终端真彩色）
- 信息栏: 版本 · 模型 · 供应商 · 语言 · 时区 · 会话数
- 多会话选择器：启动时列出历史会话，支持 `/sessions` `/session <id>` `/new` 命令
- 全命令双语适配 (zh-CN / en-US)
- Rich 库渲染 Markdown 响应（表格/代码块/标题）
- `--help` 和 epilog 适配双语
- 配置显示自动对齐（dots padding）

### 🐛 Fixes
- session.py: tool_calls 序列化兼容三种格式（ToolCall / OpenAI API dict / ToolCall dict）
- Gateway 初始化静默化：Skill 加载信息不再污染终端
- `pyclaw setup`: PORT 读成 int 导致 `c()` 拼接错误
- `pyclaw setup`: ASCII 控制码写入配置（`\u001b[<35;35;16M`）
- API.txt 旧文件残留清理
- 启动参数目录配置外移到 workspace/ 根目录（防公开仓库泄露 Key）

### 📚 文档
- 文档整理到 `docs/` 目录
- 删除过期的 ROADMAP.md
- Python 版本要求 3.8 → 3.9（匹配 pyproject.toml）
- CHANGELOG 恢复实质更新

### 🧪 W3: 测试体系搭建
- 新增 `tests/` 测试目录，134 个测试用例覆盖 5 个模块
- **test_types.py**: Message/ToolDefinition/ToolCall/ToolResult/AgentResponse 序列化测试
- **test_tools.py**: FileRead/ListDir/Exec/Time 工具定义和执行测试
- **test_session.py**: 会话 CRUD、消息管理、文件持久化（原子写入/损坏降级）、清理
- **test_memory.py**: 全局/会话记忆、重要性过滤、搜索、删除、缓存、标签
- **test_agent.py**: 初始化、属性、reconfigure、消息构建、SubAgent/SubAgentManager
- 添加 pytest 到 requirements.txt
- 顺势修了 session.py 中 ToolCall 序列化和 reasoning_content 丢失的 Bug

### 🐛 Fixes
- Session history contamination — restored sessions now exclude assistant messages (avoid hallucination carry-over)
- Tool output labels fully English (STDOUT/STDERR/Exit code) — no more Chinese labels confusing the LLM
- Tool results appended with hard "BELIEVE THIS DATA" instruction to reduce hallucination

### ♻️ Refactored
- System prompt rewritten from 33 AI tools' best practices (Cursor/Claude Code/Windsurf/CodeBuddy/v0):
  - Tool best practices: only call when necessary, explain why, call immediately
  - No preamble/postamble in responses
  - Minimize verbosity, expand only for complex tasks
  - Never create files unless needed, prefer editing

### ✨ Features
- New Skill: `ai_prompts` — query 108 prompts from 33 AI tool brands
  - `list_ai_tools(filter)` — list / filter brands
  - `get_ai_prompt(brand, file)` — read any prompt
  - `search_ai_prompts(keyword)` — full-text search

---

## [0.6.2] — 2026-05-30

### 🌐 i18n
- agent.py: bilingual system prompts (talk + coding modes), dynamic OS detection
- cli.py: shell mode bilingual (welcome, prompts, bye, errors)
- skill.py: loading/error messages → English
- 8 skill files: init logs → English
- tools.py: 9 error messages → English
- skill_tools.py: all tool descriptions → English
- memory_tools.py: all tool descriptions → English
- webapp.py: reads LANGUAGE from API.txt
- install.sh: saves LANGUAGE choice to API.txt

### 🐛 Fixes
- Docker hallucination: system prompt now says "NOT inside a container"
- Hardcoded OS → dynamic platform.system() detection
- System prompt: "Tool results override your training knowledge — BELIEVE THE TOOL"

---

## [0.6.1] — 2026-05-15

### ✨ Features
- LK-Cut video editing Skill
- Bilibili upload Skill v2
- Weather Skill
- Multi-agent system (SubAgent/SubAgentManager)

### 🐛 Fixes
- Gateway integration fixes
- Skill discovery edge cases
