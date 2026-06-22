<div align="center">

# 🦞 PyClaw

**你的私人 AI 助手 · 桌面 + Web + CLI**  
*也跑在 OpenClaw 上的 Agent 框架*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.6.4.1-blue)](https://github.com/LK-BLOG/PyClaw/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

> **轻量 · 跨平台 · 数据你自己的**

</div>

---

## 这是什么

PyClaw 是一个**跨平台 AI 助手框架**，完全由你自己掌控。没有云订阅，数据不离开你的机器。

- 🪟 **桌面应用** — 原生窗口，pywebview + WebView2
- 🌐 **Web 应用** — 浏览器打开即用（手机/LAN 也能访问）
- 💻 **CLI 工具** — `pyclaw chat "你好"` 一句话问答，`pyclaw shell` 交互式对话
- 🤖 **OpenClaw Agent** — 共用配置，在 OpenClaw 上跑

**适合谁？**
- Python 开发者，想自己搭 AI 助手
- 需要数据留在本地的用户
- 视频创作者（内置 LK-Cut 剪辑工具）
- PPT 想快速出稿的人
- OpenClaw 用户想扩展 Agent 能力

---

## 快速开始

一行命令，从零到跑：

```bash
curl -fsSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh | bash
```

```powershell
# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1 | iex
```

> ⚠️ `curl | bash` 用着方便，建议跑之前先看一眼脚本内容，或核对仓库 commit hash。

### 手动安装

```bash
git clone https://github.com/LK-BLOG/PyClaw.git
cd PyClaw/
pip install -e .
pyclaw setup
```

### 常用命令

| 命令 | 作用 |
|------|------|
| `pyclaw setup` | 配置向导（API Key / 模型 / 端口） |
| `pyclaw start` | 启动（交互选择桌面/Web/后台模式） |
| `pyclaw chat "你好"` | 一句话问答 |
| `pyclaw shell` | 交互式对话 |
| `pyclaw stop` | 停止 PyClaw |
| `pyclaw status` | 查看运行状态 |
| `pyclaw config` | 查看/设置配置 |
| `pyclaw version` | 版本号 |

---

## 三种使用方式

| 方式 | 启动命令 | 特点 |
|------|---------|------|
| 🪟 桌面模式 | `pyclaw start` 选 desktop | 独立窗口，快捷键 |
| 🌐 网页模式 | `pyclaw start` 选 web | 浏览器/手机可访问 |
| 💻 命令行模式 | `pyclaw chat` / `pyclaw shell` | 轻量，适合脚本 |

- 深色/浅色主题 · 中英文切换
- AI 自动命名对话 · 一键复制代码
- 深度思考模式可收起推理过程

---

## 内置工具

| 工具 | 用途 |
|------|------|
| `ListDir` | 浏览目录 |
| `FileRead` | 读取文件 |
| `Exec` | 执行系统命令 |
| `Time` | 查时间 |
| `delegate_to` | 把任务交给子 Agent |

## 插件系统（8 个预装，36+ 工具）

| 插件 | 工具数 | 用途 |
|------|-------|------|
| LK-Cut ✂️ | 13 | 视频剪辑（裁剪/合并/加BGM/片尾） |
| PPT 📊 | 10 种版式 | 纯 Python 生成 PPTX |
| Weather 🌤️ | — | 全球天气查询 |
| Bilibili 📺 | 4 | B 站发布 |
| System Info 🖥️ | — | 系统信息 & 进程管理 |
| Memory 🧠 | — | 长期记忆管理 |
| Desktop Path 📂 | — | Linux 中文桌面路径辅助 |
| Skill Manager 🔧 | — | 插件安装/卸载 |

插件可以用 Markdown 写（声明式），也可以用 Python 类写。详见 [`docs/SKILLS.md`](./docs/SKILLS.md)。

---

## 多 Agent 架构

1 个主 Agent + 最多 5 个子 Agent：

| 子 Agent | 权限 | 用途 |
|----------|------|------|
| ⚡ Exec | 执行命令 | 跑脚本、部署 |
| 📁 File | 读写文件 | 代码编辑 |
| 🔍 Search | 搜索 + 抓取 | 联网查资料 |
| 🌐 Browser | 搜索 + 抓取 | 浏览器自动化（开发中） |
| 🖥️ App | 执行命令 | 桌面操作 |

三种模式：**基础**（仅主 Agent）/ **标准**（主 + Exec + File）/ **完整**（1+5）。

---

## 配置

支持多个 API 提供商：

| 提供商 | 默认模型 | Base URL |
|--------|---------|----------|
| **DeepSeek** | `deepseek-v4-flash` | `https://api.deepseek.com/v1` |
| **Volcengine** | `ark-code-latest` | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| **自定义** | 手动输入 | 任意兼容 API |

在 Web UI 设置或 `pyclaw config` 中配置。

---

## PPT 生成

纯 Python 实现，10 种版式：

| 版式 | 说明 | 版式 | 说明 |
|------|------|------|------|
| `title` | 深色封面 | `content_light` | 浅色内容 |
| `title_center` | 居中封面 | `content_dark` | 深色内容 |
| `two_column` | 双栏 | `two_column_dark` | 深色双栏 |
| `features` | 功能列表 | `process` | 步骤流程 |
| `quote` | 引用页 | `end` | 结尾页 |

---

## 长期记忆

对 AI 说"记住..."就能永久保存，存入 `pyclaw_memory.db`。

> 记住我的名字是小戡

---

## 目录结构

```
PyClaw/
├── desktop.py          # 桌面端
├── run.py              # Web 端入口
├── webapp.py           # FastAPI 后端
├── index.html          # 前端（单文件，零构建）
├── pyclaw/
│   ├── agent.py        # Agent 核心
│   ├── gateway.py      # 消息路由
│   ├── tools.py        # 内置工具
│   ├── skill.py        # 插件系统
│   ├── memory.py       # 长期记忆
│   └── ...
├── skills/
│   ├── ppt/            # PPT 生成
│   ├── weather/        # 天气
│   ├── bilibili/       # B 站
│   └── lk_cut/         # 视频剪辑
├── README.md
└── pyproject.toml
```

---

## 技术栈

| 层 | 选择 |
|----|------|
| 后端 | FastAPI + Uvicorn + WebSocket |
| 前端 | 单文件 HTML/CSS/JS，零构建 |
| 桌面 | pywebview + Edge WebView2 |
| PPT | python-pptx |
| 存储 | localStorage + SQLite |

---

## 系统要求

- **Python**: 3.9–3.12
- **安装体积**: ~10MB
- **内存**: ~50MB
- **启动**: <1 秒
- **对旧硬件友好**

---

## 许可证

MIT © 2025 骆戡 & His OpenClaw

---

<p align="center">
  <sub>🦞 Made by 骆戡 & His OpenClaw</sub>
</p>
