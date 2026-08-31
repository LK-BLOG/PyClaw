# CLAUDE.md

## 项目概述

**PyClaw** 是本地优先的AI助手框架，支持桌面/Web/CLI三端运行，版本0.6.4.4.2。数据完全本地化，不上传云端，具有插件系统，支持PPT生成、视频剪辑、长期记忆等功能。

**核心特性**：
- 本地优先：所有数据存储在本地，不上传云端
- 三端支持：桌面窗口（desktop.py）、Web浏览器（webapp.py）、命令行（run.py）
- 插件系统：36 个技能工具 + 15 个内置工具，支持热加载和卸载
- 长期记忆：SQLite持久化，支持全局/会话级记忆
- 多API支持：DeepSeek、OpenAI、智谱AI、通义千问、火山引擎等
- 跨平台：Windows/Linux/macOS
- 便携模式：支持从USB运行

## 核心架构

### 架构层次

```
入口层: run.py (智能启动器→webapp.py) / webapp.py (Web) / desktop.py (桌面) / pyclaw.cli:main (命令行)
    ↓
网关层: gateway.py (会话管理、技能加载、工具注册)
    ↓
代理层: agent.py (LLM交互、工具调用循环)
    ↓
工具层: tools.py (文件/命令/网络等内置工具)
    ↓
技能层: skills/ (插件化功能扩展)
```

### 核心数据流

```
Channel.on_message(msg)
    ↓
Gateway._handle_message(msg)
    ↓
SessionManager.add_message(session_id, msg)
    ↓
Agent.chat(history) → LLM API (httpx)
    ↓
┌─ tool_calls → Agent.execute_tool() → 循环
└─ content → AgentResponse
    ↓
SessionManager.add_message(assistant_msg)
    ↓
Channel.send_message(response)
```

### 关键类职责

| 类 | 文件 | 职责 |
|---|---|---|
| `Gateway` | gateway.py | 网关协调器，管理Channel/Agent/Session三者交互 |
| `Agent` | agent.py | LLM交互核心，Tool Loop、上下文压缩、SubAgent调度 |
| `SessionManager` | session.py | 会话持久化，JSON原子写入，消息历史管理 |
| `MemoryManager` | memory.py | SQLite记忆存储，自动注入System Prompt |
| `SkillManager` | skill.py | 双轨Skill发现（声明式SKILL.md + 编程式__init__.py） |
| `SubAgentManager` | agent.py | 子代理工厂，支持5种预置+动态临时子代理 |

## 项目结构

```
PyClaw-for-Win/
├── docs/CLAUDE.md      # 本文档
├── pyclaw/             # 核心代码
│   ├── __init__.py     # 包入口，导出核心类
│   ├── gateway.py      # 网关层：生命周期、Channel路由、工具注册
│   ├── agent.py        # 代理层：LLM交互、Tool Loop、上下文压缩、SubAgent
│   ├── runner.py       # AgentRunner：唯一一份 LLM+工具 循环，向外 yield 事件
│   ├── cancel.py       # RunRegistry：按 session_id 注册/停止任务（仅 WebUI 使用，CLI 已走纯同步循环）
│   ├── session.py      # 会话层：JSON持久化、原子写入、消息历史
│   ├── memory.py       # 记忆层：SQLite存储、全局/会话记忆、Prompt注入
│   ├── pyclaw_types.py # 类型定义：Message、Tool、Channel Protocol
│   ├── types.py        # 兼容层：重导出pyclaw_types
│   ├── tools.py        # 内置工具：Exec/FileRead/ListDir/Time/WebSearch/WebFetch
│   ├── memory_tools.py # 记忆工具：Add/List/Search/Delete Memory
│   ├── skill_tools.py  # Skill工具：List/Install/Uninstall Skill
│   ├── subagent_tools.py # 子代理工具：DelegateTo/DelegateTmp
│   ├── skill.py        # Skill系统：双轨发现（声明式+编程式）
│   ├── cli.py          # CLI入口：命令行界面
│   ├── channels.py     # 通道实现（CLIChannel + WebChatChannel）
│   └── agents/         # 5种预置子代理配置（app/browser/exec/file/search）
├── tests/              # 测试文件（pytest）
│   ├── conftest.py     # 共享fixture
│   ├── test_agent.py   # Agent功能测试
│   ├── test_memory.py  # 记忆系统测试
│   ├── test_session.py # 会话管理测试
│   ├── test_tools.py   # 工具测试
│   └── test_types.py   # 类型定义测试
├── skills/             # 插件系统（36个技能工具 + 15个内置工具）
│   ├── bilibili/       # B站完整功能
│   ├── desktop_path/   # Linux桌面路径
│   ├── fuck_agent/     # 暴躁按钮
│   ├── lk_cut/         # 视频剪辑工具集
│   ├── ppt/            # PPT制作
│   ├── system_info/    # 系统信息
│   ├── weather/        # 天气查询
│   ├── web_creator/    # 网页设计工程师（仅SKILL.md，声明式）
│   └── workspace/      # 工作空间管理
├── workspace/          # 工作区
├── pyclaw_data/        # 数据存储
├── wiki/               # 文档站点
├── desktop.py          # 桌面窗口入口
├── webapp.py           # Web应用入口
├── run.py              # 智能启动器（→ webapp.py）
├── run_pyclaw_wine.py  # Wine 兼容启动器
├── pyclaw.json         # 主配置文件
├── pyclaw.json.example # 配置示例
├── API.txt             # API Key 持久化文件
├── requirements.txt    # 依赖列表
├── pyproject.toml      # 包元数据
├── SKILLS.md           # 技能开发文档
├── README.md           # 英文文档
├── README_CN.md        # 中文文档
├── README_JP.md        # 日文文档
├── 配置说明.md         # 配置说明
├── index.html          # WebUI 单页应用
├── sw.js               # Service Worker
├── logo.svg            # 站点 logo
├── icon.ico            # 应用图标
├── pyclaw.desktop      # Linux 桌面快捷方式
├── set_fixed_ipv6.sh   # 固定 IPv6 工具
├── 启动.bat            # Windows桌面启动脚本
├── 启动.sh             # Linux/Mac桌面启动脚本
├── start.bat           # Windows Web启动脚本
├── start.sh            # Linux/Mac启动脚本（三选一）
├── 清理.bat            # Windows清理脚本
├── 清理.sh             # Linux/Mac清理脚本
├── install.ps1         # Windows安装脚本
├── install.sh          # Linux/Mac安装脚本
└── .gitignore          # Git忽略文件
```

## 技术栈

### 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.9-3.12 | 运行环境 |
| httpx | - | HTTP客户端，调用LLM API |
| pytz | - | 时区处理 |
| fastapi | - | Web框架 |
| uvicorn | - | ASGI服务器 |
| websockets | - | WebSocket支持 |
| aiosqlite | - | 异步SQLite操作 |

### 可选依赖

| 依赖 | 用途 | 所需技能 |
|------|------|----------|
| bilibili-api-python | B站API | bilibili |
| psutil | 进程管理 | system_info |
| python-pptx | PPT生成 | ppt |
| ffmpeg | 视频处理 | lk_cut |
| pytest | 测试框架 | 开发 |

### 支持的API

| API提供商 | 模型示例 | 端点 |
|-----------|----------|------|
| DeepSeek | deepseek-v4-flash | https://api.deepseek.com/v1 |
| OpenAI | gpt-4 | https://api.openai.com/v1 |
| 智谱AI | glm-4 | https://open.bigmodel.cn/api/paas/v4 |
| 通义千问 | qwen-max | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 火山引擎 | - | https://ark.cn-beijing.volces.com/api/v3 |

## 关键模块详解

### 1. Gateway（网关层）

**文件**: `pyclaw/gateway.py`

Gateway是整个系统的核心协调器，管理Channel、Agent、Session三者的交互。

**主要职责**:
- 生命周期管理：初始化、启动、关闭
- Channel路由：处理来自不同Channel的消息
- 工具注册：按顺序注册内置工具、技能工具、记忆工具
- 技能加载：扫描skills目录，加载声明式和编程式技能

**初始化流程**:
```python
# Gateway.initialize() 主要步骤
1. 初始化SessionManager（JSON持久化）
2. 初始化MemoryManager（SQLite存储）
3. 初始化SkillManager（技能发现）
4. 初始化Agent（LLM交互）
5. 注册工具（内置+技能+记忆）
6. 加载技能（声明式+编程式）
```

**工具注册顺序**:
```python
# Gateway.initialize_skills() 中按顺序注册
1. 内置工具 (ExecTool, FileReadTool, ...)
2. 声明式Skill内容注入System Prompt
3. 编程式Skill.get_tools() 返回的工具
4. Skill管理工具 (List/Install/Uninstall)
5. 记忆管理工具 (Add/List/Search/Delete)
```

### 2. Agent（代理层）

**文件**: `pyclaw/agent.py`

Agent是LLM交互的核心，负责与大模型通信、执行工具调用、管理上下文。

**关键机制**:

#### Tool Loop（工具调用循环）
```python
# Agent.chat() 核心逻辑
while True:
    response = call_llm(history)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)
            history.append(result)
    else:
        return response
# 最多300轮工具调用
```

#### 上下文压缩
当对话历史超过100K字符时自动触发：
- **主动检测**：每轮对话检查字符数
- **异步版**：前10轮 + AI总结中段 + 后10轮
- **同步版**：前10轮 + 压缩摘要 + 后10轮

#### 备用模型Failover
主模型失败时自动切换备用模型：
```python
# Agent配置
failover_models = ["model1", "model2"]
# 主模型失败 → 尝试model1 → 尝试model2
```

#### DeepSeek思考模式
支持`reasoning_content`字段透传，显示模型思考过程。

#### System Prompt动态构建
model/mode切换自动重建System Prompt，包含：
- 基础角色设定
- 工具使用说明
- 技能内容注入
- 记忆上下文

### 3. SessionManager（会话层）

**文件**: `pyclaw/session.py`

负责会话的持久化和消息历史管理。

**主要功能**:
- JSON原子写入：防止并发写入导致数据损坏
- 消息历史管理：添加、查询、删除消息
- 不活跃清理：自动清理长时间不活跃的会话
- 序列化/反序列化：消息对象与JSON互转

**存储结构**:
```json
{
  "session_id": "xxx",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "...", "tool_calls": [...]}
  ],
  "created_at": "2026-08-21T10:00:00",
  "updated_at": "2026-08-21T10:05:00"
}
```

### 4. MemoryManager（记忆层）

**文件**: `pyclaw/memory.py`

基于SQLite的长期记忆系统。

**记忆类型**:
- **全局记忆**：跨会话持久化，适用于用户偏好、常用信息
- **会话记忆**：仅当前会话有效，适用于临时上下文

**主要功能**:
- 自动注入：记忆内容自动添加到System Prompt
- 重要性过滤：按重要性排序，优先注入重要记忆
- 关键词搜索：支持全文搜索记忆内容
- 标签系统：支持标签分类和筛选

**数据库结构**:
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance INTEGER DEFAULT 0,
    tags TEXT,
    session_id TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 5. SkillManager（技能系统）

**文件**: `pyclaw/skill.py`

双轨技能发现机制：声明式（SKILL.md）+ 编程式（Python类）。

**发现流程**:
```python
# Gateway启动时
1. skill_manager.discover_skills()  # 扫描skills/目录
2. skill_manager.initialize_all()   # 异步初始化每个技能
3. get_all_tools()                  # 获取所有工具定义
4. agent.register_tool()            # 注册到Agent
```

**技能分类**:
- **多媒体技能**：bilibili, lk_cut, ppt
- **系统工具技能**：system_info, desktop_path, workspace
- **信息查询技能**：weather
- **交互控制技能**：fuck_agent
- **开发设计技能**：web_creator

## 技能系统完整文档

### 1. ~~ai_prompts~~ （已删除）

> 该技能已在历史提交中删除（提交 468ddaa）。

### 2. bilibili — B站完整功能

**功能**: 发布动态、扫码登录、检查登录状态

**工具**:
- `bilibili_publish_dynamic(content)` — 发布纯文字动态
- `bilibili_publish_tunnel_dynamic(tunnel_url, tunnel_name?)` — 发布隧道链接动态
- `bilibili_qr_login()` — 扫码登录获取Cookie
- `bilibili_check_login(cookie_file?)` — 检查登录状态

**依赖**: `bilibili-api-python`

**Cookie存储**: `Cookie.txt`

**使用流程**:
```python
# 1. 首次使用需要扫码登录
bilibili_qr_login()

# 2. 检查登录状态
bilibili_check_login()

# 3. 发布动态
bilibili_publish_dynamic("Hello World!")
```

### 3. ~~canvas-video~~ （已删除）

> 该技能已在历史提交中删除（提交 468ddaa）。


### 6. lk_cut — 视频剪辑工具集

**功能**: 基于ffmpeg的13种视频处理

**工具列表**:
- `video_info(input)` — 获取视频信息
- `video_cut(input, start, duration, output?)` — 剪切片段
- `video_merge(inputs, output)` — 合并视频
- `video_speed(input, speed, output?)` — 调整速度
- `video_watermark(input, watermark, position?, output?)` — 添加水印
- `video_extract_audio(input, output?)` — 提取音频
- `video_make_gif(input, start?, duration?, fps?, output?)` — 制作GIF
- `video_transcode(input, format?, output?)` — 转码
- `video_extract_frames(input, fps?, output?)` — 提取帧
- `video_add_subtitles(input, subtitles, output?)` — 添加字幕
- `video_rotate(input, angle, output?)` — 旋转视频
- `video_crop(input, x, y, width, height, output?)` — 裁剪视频
- `video_thumbnail(input, time?, output?)` — 生成缩略图

**依赖**: 需要安装 `ffmpeg`

**使用示例**:
```python
# 获取视频信息
video_info("input.mp4")

# 剪切视频（从10秒开始，持续30秒）
video_cut("input.mp4", "00:00:10", "00:00:30", "output.mp4")

# 合并多个视频
video_merge(["part1.mp4", "part2.mp4"], "merged.mp4")

# 2倍速播放
video_speed("input.mp4", 2.0, "fast.mp4")

# 添加水印
video_watermark("input.mp4", "logo.png", "top-right", "output.mp4")

# 制作GIF
video_make_gif("input.mp4", "00:00:05", "00:00:10", 15, "output.gif")
```

### 7. ppt — PPT制作

**功能**: 生成现代风格PPT，10种布局

**工具**:
- `create_modern_pptx(slides_json, output?)` — 智能PPT（推荐）
- `create_pptx(title?, subtitle?, theme?, output?)` — 基础PPT
- `create_smart_ppt(title?, sections?, theme?, output?)` — 旧版智能PPT

**布局类型**:
1. 标题页
2. 居中封面
3. 浅色内容页
4. 深色内容页
5. 双栏布局
6. 卡片布局
7. 步骤流程
8. 引用页
9. 结束页
10. 空白页

**主题选项**:
- `modern` — 现代简约
- `classic` — 经典商务
- `creative` — 创意设计
- `tech` — 科技感

**依赖**: `python-pptx`（有纯Python回退方案）

**使用示例**:
```python
# 创建基础PPT
create_pptx("项目汇报", "2026年度总结", "modern", "report.pptx")

# 创建智能PPT
sections = [
    {"title": "项目背景", "content": "项目简介..."},
    {"title": "进展汇报", "content": "已完成工作..."},
    {"title": "下一步计划", "content": "未来规划..."}
]
create_smart_ppt("项目汇报", sections, "tech", "report.pptx")
```

### 8. system_info — 系统信息

**功能**: 查看系统状态、进程管理

**工具**:
- `get_system_info()` — 操作系统、Python、磁盘信息
- `list_processes(limit?, search?)` — 列出进程（按CPU排序）
- `kill_process(pid, force?)` — 结束进程

**依赖**: `psutil`（进程管理）

**使用示例**:
```python
# 获取系统信息
system_info = get_system_info()
# 返回: OS版本、Python版本、磁盘空间、内存使用等

# 列出前10个进程
list_processes(limit=10)

# 搜索python相关进程
list_processes(search="python")

# 结束进程
kill_process(1234)  # 优雅结束
kill_process(1234, force=True)  # 强制结束
```

### 9. weather — 天气查询

**功能**: 查询全球城市天气

**工具**:
- `get_weather(city, unit?)` — 获取天气信息

**参数**:
- `city`: 城市名（中英文均可）
- `unit`: 'c'摄氏度（默认） / 'f'华氏度

**API**: wttr.in（免费）

**使用示例**:
```python
# 查询北京天气（摄氏度）
get_weather("北京")

# 查询上海天气（华氏度）
get_weather("上海", "f")

# 查询东京天气
get_weather("Tokyo")
```

**返回信息**:
- 当前温度
- 天气状况（晴/阴/雨等）
- 湿度
- 风速
- 未来几天预报

### 10. web_creator — 网页设计工程师

**功能**: 创建高质量视觉Web作品

**类型**: 文档型技能，提供设计原则和工作流程

**适用场景**:
- 落地页设计
- 仪表盘开发
- 原型设计
- 演示文稿
- 动画效果
- 数据可视化

**核心理念**:
- 追求"惊艳"而非"功能"
- 避免AI设计套路
- 注重用户体验
- 重视视觉层次

**工作流程**:
1. 需求分析：理解用户需求和目标受众
2. 设计规划：确定风格、色彩、布局
3. 原型设计：创建线框图和交互原型
4. 视觉实现：编写HTML/CSS/JavaScript
5. 优化测试：性能优化和兼容性测试

### 11. workspace — 工作空间管理

**功能**: 多目录管理、文件操作、搜索、Git状态

**工具**:
- `workspace_add(name, path)` — 添加工作空间
- `workspace_list()` — 列出所有工作空间
- `workspace_remove(name)` — 删除工作空间
- `workspace_list_files(workspace_name?, path?)` — 浏览文件
- `workspace_read_file(workspace_name, file_path)` — 读取文件
- `workspace_search(keyword, workspace_name?, path?)` — 搜索文件
- `workspace_git_status(workspace_name)` — Git状态
- `workspace_set_key(new_key, confirm_key)` — 设置访问密钥
- `workspace_read_external(full_path, access_key, limit?)` — 读取外部文件（需密钥授权）

**权限控制**:
- 默认1MB文件大小限制
- 密钥授权后可访问1GB+外部路径
- 访问密钥用于安全控制

**使用示例**:
```python
# 添加工作空间
workspace_add("project", "/path/to/project")

# 列出所有工作空间
workspace_list()

# 浏览工作空间文件
workspace_list_files("project")

# 读取文件
workspace_read_file("project", "README.md")

# 搜索文件
workspace_search("main", "project")

# 查看Git状态
workspace_git_status("project")

# 设置访问密钥
workspace_set_key("my_secret_key", "my_secret_key")
```

## 配置体系详解

### 三层配置

#### 1. pyclaw.json — 主配置文件

```json
{
  "API_KEY": "your_api_key",
  "MODEL": "deepseek-v4-flash",
  "ENDPOINT": "https://api.deepseek.com/v1",
  "LANGUAGE": "zh",
  "CONTEXT_SIZE": 1000000,
  "PORT": 2469,
  "ALLOW_EXTERNAL": false,
  "SUB_AGENTS_ENABLED": true,
  "FAIL_OVER_MODELS": [],
  "THEME": "dark"
}
```

**配置项说明**:
- `API_KEY`: API密钥（必填）
- `MODEL`: 模型名称（默认deepseek-v4-flash）
- `ENDPOINT`: API端点地址
- `LANGUAGE`: 界面语言（zh/en/ja）
- `CONTEXT_SIZE`: 上下文窗口大小
- `PORT`: 服务端口（默认2469）
- `ALLOW_EXTERNAL`: 是否允许局域网访问
- `SUB_AGENTS_ENABLED`: 是否启用子代理
- `FAIL_OVER_MODELS`: 备用模型列表
- `THEME`: 界面主题（dark/light）

#### 2. 环境变量（极少使用，仅覆盖路径类）

`.env` **已废弃**。绝大多数配置写在 `pyclaw.json` 即可。
下面这些环境变量仍然有效，但只是「覆盖某条具体配置」：

```bash
# 配置文件路径覆盖（默认就是仓库根目录的 pyclaw.json）
PYCLAW_CONFIG=/path/to/another-pyclaw.json

# 局域网开关（与 pyclaw.json 的 ALLOW_EXTERNAL 等效）
PYCLAW_ALLOW_EXTERNAL=1

# 工作区路径盐值
PYCLAW_WORKSPACE_KEY=some-entropy

# 主题色微调
PYCLAW_BLUE=...
PYCLAW_ART=...
PYCLAW_YELLOW=...
```

> **注意**：`PYCLAW_API_KEY` / `PYCLAW_BASE_URL` / `PYCLAW_MODEL` 之类的「API 字段」
> **没有任何代码读取**。API 配置只能写在 `pyclaw.json`。

#### 3. pyproject.toml — 包元数据

```toml
[project]
name = "pyclaw"
version = "0.6.4.4.2"
description = "Local-first AI assistant framework"
requires-python = ">=3.9"

[project.scripts]
pyclaw = "pyclaw.cli:main"
```

### 配置优先级

```
PYCLAW_CONFIG 指定的配置路径 > pyclaw.json > 默认值
```

> **配置只从 `pyclaw.json` 读取，`.env` 已废弃。**
> 代码层面的依据：`webapp.py` 明确注释「配置统一从 pyclaw.json 读取，不读取 .env」，
> 全仓库无任何 dotenv 加载代码。`pyclaw.json.example` 是唯一推荐的配置起点。

### 配置热更新

Agent支持运行时重新配置：
```python
Agent.reconfigure(
    api_key="new_key",
    base_url="new_url",
    model="new_model",
    mode="new_mode",
    thinking=True,
    reasoning_effort="high",
    failover_models=["model1", "model2"]
)
# model/mode变化自动触发 _build_system_prompt(force=True)
```

## 安装与部署

### 快速安装（推荐）

#### Linux/macOS
```bash
curl -fsSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh | bash
```

#### Windows
```powershell
# 下载安装脚本
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1" -OutFile "install.ps1"

# 运行安装
.\install.ps1
```

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/LK-BLOG/PyClaw.git
cd PyClaw

# 2. 安装依赖
pip install -e .

# 3. 配置向导
pyclaw setup

# 4. 启动
pyclaw start
```

### 安装脚本功能

#### install.ps1（Windows）
- Python检测（优先便携版 → 系统python → python3）
- 依赖下载和安装
- CLI安装
- 配置向导
- 桌面快捷方式创建
- Skill管理

#### install.sh（Linux/macOS）
- 支持curl/git两种下载方式
- 自动检测Python版本
- 依赖安装
- 配置向导
- 权限设置

### 启动方式

#### 命令行启动
```bash
# 交互式启动（选择模式）
pyclaw start

# 直接启动Web模式
pyclaw start --web

# 直接启动桌面模式
pyclaw start --desktop

# 一句话问答
pyclaw chat "你好"

# 交互式对话
pyclaw shell
```

#### 脚本启动

**Windows**:
- `启动.bat` — 桌面窗口模式（调用desktop.py）
- `start.bat` — Web浏览器模式（调用webapp.py）

**Linux/macOS**:
- `启动.sh` — 桌面窗口模式
- `start.sh` — 三选一菜单（Desktop/Browser/后台服务）

**所有启动脚本特点**:
1. 自动清除代理设置（DeepSeek API国内直连）
2. 自动检测Python路径
3. 便携模式支持

### 便携模式

支持从USB运行，无需安装：
1. 将整个文件夹拷贝到USB
2. 运行启动脚本
3. 所有配置和数据保存在文件夹内

### 局域网访问

默认仅监听127.0.0.1，如需局域网访问：
```json
{
  "ALLOW_EXTERNAL": true,
  "ACCESS_TOKEN": "your_access_token"
}
```

## 开发指南

### 开发环境设置

```bash
# 1. 克隆仓库
git clone https://github.com/LK-BLOG/PyClaw.git
cd PyClaw

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安装开发依赖
pip install -e .
pip install pytest pytest-asyncio

# 4. 运行测试
pytest
```

### 测试指南

#### 测试结构

```
tests/
├── conftest.py      # 共享fixture：临时会话文件、临时数据库、示例消息/工具
├── test_agent.py    # Agent功能测试（10个类，~50个用例）
├── test_memory.py   # 记忆系统测试（7个类，~30个用例）
├── test_session.py  # 会话管理测试（5个类，~25个用例）
├── test_tools.py    # 工具测试（5个类，~20个用例）
└── test_types.py    # 类型定义测试（6个类，~15个用例）
```

#### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_agent.py -v

# 运行特定测试类
pytest tests/test_agent.py::TestAgentChat -v

# 运行特定测试方法
pytest tests/test_agent.py::TestAgentChat::test_basic_chat -v

# 生成测试报告
pytest --html=report.html
```

#### 测试特点

- **纯单元测试**：不调用真实API
- **pytest fixtures**：使用临时目录和数据库隔离
- **覆盖较全**：但**没有集成测试和E2E测试**

### 代码规范

#### Python代码风格
- 遵循PEP 8
- 使用类型注解
- 异步优先（async/await）
- 文档字符串（Google风格）

#### 命名规范
- 类名：PascalCase
- 函数/方法：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有成员：_前缀

### 调试技巧

#### 日志查看
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看特定模块日志
logger = logging.getLogger("pyclaw.gateway")
logger.setLevel(logging.DEBUG)
```

#### 常见问题排查

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   netstat -ano | findstr :2469
   # 结束进程
   taskkill /PID <进程ID> /F
   ```

2. **API连接失败**
   - 检查网络连接
   - 验证API_KEY是否正确
   - 确认ENDPOINT地址

3. **技能加载失败**
   - 检查skills目录权限
   - 验证__init__.py格式
   - 查看错误日志

## 故障排除

### 常见问题

#### 1. 安装问题

**问题**: pip安装失败
**解决**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用镜像源
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**问题**: 依赖冲突
**解决**:
```bash
# 创建新的虚拟环境
python -m venv venv_new
source venv_new/bin/activate
pip install -e .
```

#### 2. 启动问题

**问题**: 端口被占用
**解决**:
```bash
# 修改端口
# 编辑 pyclaw.json
{
  "PORT": 2470
}
```

**问题**: Python版本不兼容
**解决**:
```bash
# 检查Python版本
python --version
# 需要Python 3.9-3.12
```

#### 3. API问题

**问题**: API调用失败
**检查**:
1. API_KEY是否正确
2. ENDPOINT地址是否正确
3. 网络连接是否正常
4. API额度是否充足

**问题**: 模型响应慢
**解决**:
- 使用更快的模型（如deepseek-v4-flash）
- 减小CONTEXT_SIZE
- 检查网络延迟

#### 4. 技能问题

**问题**: 技能加载失败
**检查**:
1. 技能目录结构是否正确
2. __init__.py是否导出SKILL_CLASS
3. 依赖是否安装

**问题**: 工具调用失败
**检查**:
1. 工具参数是否正确
2. 工具依赖是否满足
3. 查看错误日志

### 错误代码

| 错误代码 | 含义 | 解决方案 |
|----------|------|----------|
| E001 | API密钥无效 | 检查pyclaw.json中的API_KEY |
| E002 | 网络连接失败 | 检查网络连接和防火墙设置 |
| E003 | 端口被占用 | 修改PORT配置或结束占用进程 |
| E004 | 技能加载失败 | 检查技能目录和依赖 |
| E005 | 内存不足 | 减小CONTEXT_SIZE或重启服务 |

### 日志文件

- **主日志**: `pyclaw_data/pyclaw.log`
- **错误日志**: `pyclaw_data/error.log`
- **访问日志**: `pyclaw_data/access.log`

## 高级功能

### 多Agent系统

#### 子代理类型
1. **ExecAgent** — 执行命令
2. **FileAgent** — 文件操作
3. **SearchAgent** — 搜索信息
4. **BrowserAgent** — 浏览器操作
5. **AppAgent** — 应用操作
6. **临时子代理** — 动态创建

#### 子代理配置
```json
{
  "SUB_AGENTS_ENABLED": true,
  "SUB_AGENT_DEPTH": 3,
  "SUB_AGENT_TIMEOUT": 300
}
```

### 上下文压缩

#### 触发条件
- 对话历史超过100K字符
- 手动触发

#### 压缩策略
1. **保留前10轮对话**
2. **AI总结中间部分**
3. **保留后10轮对话**
4. **生成压缩摘要**

### 备用模型Failover

#### 配置
```json
{
  "MODEL": "deepseek-v4-flash",
  "FAIL_OVER_MODELS": ["gpt-4", "glm-4"]
}
```

#### 行为主模型失败 → 尝试备用模型1 → 尝试备用模型2

### DeepSeek思考模式

支持`reasoning_content`字段透传，显示模型思考过程。

### 长期记忆

#### 记忆类型
- **全局记忆**：跨会话持久化
- **会话记忆**：仅当前会话有效

#### 记忆操作
- 添加记忆
- 搜索记忆
- 删除记忆
- 导出记忆

### 插件热加载

支持运行时加载/卸载技能：
```python
# 安装技能
install_skill("skill_name")

# 卸载技能
uninstall_skill("skill_name")

# 重新加载技能
reload_skill("skill_name")
```

## API参考

### REST API

#### 启动服务
```bash
pyclaw start --web
# 服务运行在 http://localhost:2469
```

#### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/chat` | POST | 发送消息 |
| `/api/sessions` | GET | 获取会话列表 |
| `/api/sessions/{id}` | GET | 获取会话详情 |
| `/api/tools` | GET | 获取工具列表 |
| `/api/skills` | GET | 获取技能列表 |
| `/api/health` | GET | 健康检查 |

#### WebSocket API

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:2469/ws');

// 发送消息
ws.send(JSON.stringify({
  type: 'chat',
  content: 'Hello',
  session_id: 'xxx'
}));

// 接收消息
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Python API

#### Gateway API
```python
from pyclaw.gateway import Gateway

# 创建网关
gateway = Gateway(config)

# 初始化
await gateway.initialize()

# 处理消息
response = await gateway.handle_message(message)

# 关闭
await gateway.close()
```

#### Agent API
```python
from pyclaw.agent import Agent

# 创建代理
agent = Agent(config)

# 聊天
response = await agent.chat(history)

# 注册工具
agent.register_tool(tool)

# 重新配置
agent.reconfigure(api_key="new_key")
```

## 性能优化

### 配置优化

```json
{
  "CONTEXT_SIZE": 100000,
  "MAX_TOOL_CALLS": 50,
  "TIMEOUT": 30,
  "CACHE_ENABLED": true
}
```

### 缓存策略

1. **响应缓存**：缓存LLM响应
2. **工具缓存**：缓存工具执行结果
3. **技能缓存**：缓存技能加载结果

### 并发优化

1. **异步IO**：使用asyncio
2. **连接池**：HTTP连接复用
3. **任务队列**：异步任务处理

### 内存优化

1. **流式处理**：大文件流式读取
2. **分页加载**：大数据分页
3. **垃圾回收**：及时释放资源

## 最佳实践

### 开发最佳实践

1. **代码复用**：提取公共函数
2. **错误处理**：完善异常处理
3. **日志记录**：详细记录关键操作
4. **单元测试**：保持高测试覆盖率
5. **文档注释**：编写清晰的文档

### 部署最佳实践

1. **环境隔离**：使用虚拟环境
2. **配置管理**：使用环境变量
3. **日志监控**：监控日志文件
4. **备份策略**：定期备份数据
5. **安全更新**：及时更新依赖

### 使用最佳实践

1. **合理配置**：根据硬件配置参数
2. **定期清理**：清理无用会话和记忆
3. **监控资源**：监控CPU、内存使用
4. **备份数据**：定期备份pyclaw_data
5. **安全使用**：不要泄露API_KEY

## 贡献指南

### 贡献流程

1. **Fork仓库**
2. **创建分支**：`git checkout -b feature/xxx`
3. **提交更改**：`git commit -m 'Add feature xxx'`
4. **推送分支**：`git push origin feature/xxx`
5. **创建PR**

### 代码规范

1. 不偏离项目方向
2. 添加类型注解
3. 编写文档字符串
4. 添加单元测试
5. 更新文档

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

## 许可证

GNU General Public License v3.0

## 联系方式

- **GitHub**: https://github.com/LK-BLOG/PyClaw
- **Issues**: https://github.com/LK-BLOG/PyClaw/issues
- **Email**: gunmu1145@gmail.com or pyclaw@agent.qq.com

---

## AgentRunner 与取消/插话协议

### 唯一对话循环

`pyclaw/runner.py` 是**唯一**的「LLM 调用 + 工具执行」循环实现。
四个调用方（WebUI、CLI、通道入口、子代理）**全部**通过 `run_agent(...)` 异步生成器消费事件流，
各自负责渲染。

### 事件协议

| type | 何时发出 | 携带字段 |
|---|---|---|
| `thinking` | 开始新一轮 LLM | `round` |
| `reasoning` | 推理内容增量 | `delta` |
| `stream` | 正文增量 | `delta` |
| `tool_call` | 准备执行某个工具 | `name`, `arguments`, `id` |
| `tool_result` | 工具执行完 | `id`, `name`, `content` |
| `agent_bubble` | 子代理产出 | `agent`, `content` |
| `final` | 本轮对话正常结束 | `content` |
| `stopped` | 被用户停止 | `reason`, `partial` |
| `error` | 出错 | `message` |

### 取消 / 插话

- `pyclaw/cancel.py` 的 `RunRegistry` 按 `session_id` 注册运行中的任务，
  持有 `asyncio.Event`（停止信号）+ `asyncio.Task` 引用。
- **硬停止**：`registry.stop(sid)` 设 stop_event，runner 在 3 个检查点（每轮开头、每个 chunk 后、工具执行前）优雅退出。
- **软插话**：直接把用户消息 `add_message` 进 session，runner 每轮重新 `get_history`，下一轮自然读到 —— **零成本插话**。
- **停止时历史必须一致**：给已发出但未执行的 `tool_call` 补一条 `tool` 消息（`[已被用户中断]`），**绝不**删除 assistant 消息。
  否则下一轮 API 调用会因为 tool_calls 没有配对响应而报错。

### CLI：故意只走同步循环

`pyclaw/cli.py` **不**注册到 `RunRegistry`，**不**支持 `/stop` / 软插话。

主循环是纯 `read → await _run_cli_chat(...) → print`：

- 上一轮还在 `await` 时按 Ctrl+C → 当前轮被 `asyncio.CancelledError` 打断，下一轮直接开始。
- 想插话？等上一轮跑完。
- 跑题了？Ctrl+C 整轮重发。

理由：之前的「软插话 + 并发输入 + 队列」多 task 互相踩（EOF 死循环、stop 路径走错、插话后助手把它当空气等），调试成本远高于「CLI 用户多等两秒」。

---

*基于PyClaw v0.6.4.4.2，最后更新：2026-08-30*

> 本次补丁（未发版）：
> - `pyclaw/cli.py` 主循环简化为同步 read→await→print
> - 删除 CLI 端的 `/stop`、软插话、并发输入 task 协调
> - 文档补：CLI 故意不走 RunRegistry（见上一节）
> - `pyclaw/cancel.py` 保留，仅供 WebUI 使用
