# 🦞 PyClaw

轻量级 Python AI 助手框架 — **桌面版 + Web 版**

> **全平台**：Windows ✅ Linux ✅ macOS ✅  
> **零配置**：下载即用，自动装依赖  
> **U盘便携**：项目仅 ~10MB，比一张照片还小 ✅  
> **低功耗**：后台占用 ~50MB 内存，1 秒内启动  
> **老电脑友好**：10 年前设备也能流畅运行

---

## ✨ 特性

### 📏 极致轻量
- 📁 体积仅 ~10MB（含 Python 依赖）
- 💻 10 年前老电脑流畅运行
- 🧮 后台仅占用 ~50MB 内存
- ⚡ 1 秒内启动完成
- 🐍 兼容 Python 3.8–3.12

### 🖥️ 双模式启动

| 模式 | 说明 | 命令 |
|------|------|------|
| 🪟 **桌面版** | 原生窗口，无浏览器标签栏 | `python desktop.py` |
| 🌐 **Web 版** | 浏览器访问 | `python run.py` |

桌面版使用 pywebview + Edge WebView2 渲染，localStorage 持久化，关闭不丢会话。

### 🎨 界面

- 深色/浅色 **双主题** — 点击 🌙 切换
- 中/英 **双语** — 点击 🌐 切换
- 🤖 **AI 自动命名会话** — 首条消息自动生成标题
- 📋 **代码一键复制**
- 📱 **响应式布局** — 桌面到移动端自适应
- 🧠 **深度思考模式** — 可折叠推理过程显示

### 🔧 内置工具

| 工具 | 功能 |
|------|------|
| 📁 ListDir | 浏览目录内容 |
| 📄 FileRead | 读取文件内容 |
| 💻 Exec | 执行系统命令 |
| ⏰ Time | 查询当前时间 |
| 🤖 delegate_to | 委派任务给子代理（exec/file/search/browser/app） |

### 🧩 Skill 插件系统

| 插件 | 功能 |
|------|------|
| 🌤️ Weather | 全球城市天气查询 |
| 📺 Bilibili | B站动态发布（4工具） |
| 🖥️ System Info | 系统信息与进程管理 |
| 📂 Desktop Path | Linux 中文桌面路径 |
| ✂️ LK-Cut | 视频剪辑工具集（13工具） |
| 📊 PPT | **纯 Python 生成 PPTX**（10种布局） |
| 🧠 Memory | 长期记忆管理 |
| 🔧 Skill Manager | 插件安装/卸载/管理 |

**预装 8 个插件，合计 36+ 工具**

### 🤖 多 Agent 协作架构

支持 **1+5 子代理架构**，主 Agent 可通过 `delegate_to` 委派任务：

| 子代理 | 工具权限 | 用途 |
|--------|---------|------|
| ⚡ **Exec** | `exec_command` | 执行系统命令 |
| 📁 **File** | `read_file`, `list_directory`, `write_file` | 文件读写操作 |
| 🔍 **Search** | `web_search`, `fetch_url` | 联网搜索与网页抓取 |
| 🌐 **Browser** | `web_search`, `fetch_url` | 浏览器自动化（开发中） |
| 🖥️ **App** | `exec_command` | 桌面应用操作 |

**架构模式可切换：**
- **基础** — 仅主 Agent，无子代理
- **标准** — 1+2（Main + Exec + File）
- **完整** — 1+5（Main + 全部 5 个子代理）

在设置面板 → 🤖 Agent 架构 中一键切换。用户可通过对话创建/自定义子代理，无需写代码。

---

## 🚀 快速开始

### 一键启动

```bash
# Windows
双击 启动.bat

# Linux/macOS
./start.sh
```

首次启动自动：
1. 检测 Python 3
2. `pip install` 所有依赖
3. 启动服务 → 自动打开桌面窗口或浏览器

### 手动启动

```bash
# 桌面版（推荐）
python desktop.py

# 浏览器版
python run.py

# 开放局域网访问
python run.py --allow-external
# 或
python desktop.py --allow-external
```

---

## 📋 配置

所有配置在 **Web 界面设置面板** 中完成，自动保存到 localStorage。

### 支持的服务商

| 服务商 | 默认模型 | Base URL |
|--------|---------|----------|
| **DeepSeek** | `deepseek-v4-flash` | `https://api.deepseek.com/v1` |
| **火山引擎** | `ark-code-latest` | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| **其他** | 手动输入 | 任意兼容 API |

### 模型自动过滤

切换供应商时自动显示对应模型列表，避免选错模型导致 API 报错。

---

## 🧠 长期记忆

对 AI 说 "记住..." 即可永久保存信息：

> 记住我叫小戡，喜欢简洁回答  
> 记住我常用桌面路径是中文

所有记忆保存在 `pyclaw_memory.db`，跟 U 盘一起带走。

---

## 🧩 四大编程准则

Coding 模式下 AI 遵循的原则：

1. 🧠 **编码前思考** — 不假设、不隐藏困惑、主动权衡
2. ✂️ **简洁优先** — 最少代码、避免过度设计
3. 🎯 **精准修改** — 只改必须改的、匹配现有风格
4. 🔄 **目标驱动** — 定义成功标准、循环验证

---

## 📊 PPT 生成

纯 Python 生成 PPTX，支持 10 种布局：

| 类型 | 说明 |
|------|------|
| `title` | 深色封面 |
| `title_center` | 居中封面 |
| `content_light` | 浅色内容页 |
| `content_dark` | 深色内容页 |
| `two_column` | 双栏对比 |
| `two_column_dark` | 深色双栏 |
| `features` | 功能列表 |
| `process` | 步骤流程 |
| `quote` | 引用/金句 |
| `end` | 结束页 |

---

## 🔌 开发 Skill

`skills/` 目录下每个子目录是一个插件：

```
skills/your_skill/
├── __init__.py     # 插件代码
└── SKILL.md        # 插件文档
```

参考 `skills/ppt/` 或 `skills/weather/` 的示例。

---

## 📁 项目结构

```
pyclaw/
├── desktop.py              # 桌面版启动器
├── run.py                  # Web 版启动器
├── webapp.py               # FastAPI 后端
├── index.html              # 前端界面（单文件）
├── pyclaw/
│   ├── agent.py            # AI Agent 核心
│   ├── gateway.py          # 消息路由
│   ├── tools.py            # 内置工具
│   ├── skill.py            # 插件系统
│   ├── memory.py           # 长期记忆
│   └── ...
├── skills/
│   ├── ppt/                # PPT 生成插件
│   ├── weather/            # 天气插件
│   ├── bilibili/           # B站插件
│   ├── lk_cut/             # 视频剪辑
│   └── ...
├── 启动.bat                # Windows 启动
├── start.sh                # Linux/macOS 启动
└── README.md
```

---

## 🎯 技术栈

| 组件 | 选型 |
|------|------|
| **后端** | FastAPI + Uvicorn + WebSocket |
| **前端** | 单文件 HTML/CSS/JS，零构建 |
| **桌面** | pywebview + Edge WebView2 |
| **PPT** | python-pptx / 纯 Python（零依赖） |
| **存储** | localStorage + SQLite |

## 📄 License

MIT

**Made with 🦞 ❤️ by 骆戡 & OpenClaw Team**
