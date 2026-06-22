<div align="center">

# 🦞 PyClaw

**Your Private AI Assistant — Desktop · Web · CLI**  
*Also runs as an OpenClaw Agent*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.6.4.1-blue)](https://github.com/LK-BLOG/PyClaw/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

> **Lightweight · Cross-platform · Your data stays yours**

</div>

---

## What is PyClaw?

PyClaw is a **cross-platform AI assistant framework** you can fully control. No cloud subscriptions, no data leaving your machine — just you and your AI.

- 🪟 **Desktop app** — Native window via pywebview + WebView2
- 🌐 **Web app** — Open in your browser (also accessible from mobile / LAN)
- 💻 **CLI** — `pyclaw chat "hello"` for quick Q&A, `pyclaw shell` for interactive REPL
- 🤖 **OpenClaw Agent** — Share configs and run as an OpenClaw sub-agent

**Who is it for?**
- Python developers building their own AI agent
- Users who need local-first, data-sovereign AI
- Video creators (built-in LK-Cut editor)
- Anyone who needs quick slide decks (built-in PPT generator)
- OpenClaw users extending their agent's capabilities

---

## Quick Start

One line, zero to running:

```bash
curl -fsSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh | bash
```

```powershell
# Windows PowerShell
iwr -useb https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1 | iex
```

> ⚠️ `curl | bash` is convenient — consider reviewing the script or checking the commit hash first.

### Manual Install

```bash
git clone https://github.com/LK-BLOG/PyClaw.git
cd PyClaw/
pip install -e .
pyclaw setup
```

### Commands

| Command | What it does |
|---------|-------------|
| `pyclaw setup` | Configuration wizard (API key, model, language, port) |
| `pyclaw start` | Launch (interactive: desktop / web / background) |
| `pyclaw chat "hello"` | One-shot Q&A |
| `pyclaw shell` | Interactive conversation |
| `pyclaw stop` | Stop PyClaw |
| `pyclaw status` | Check running status |
| `pyclaw config` | View / edit config |
| `pyclaw version` | Print version |

---

## Three Modes

| Mode | Launch | Highlights |
|------|--------|-----------|
| 🪟 **Desktop** | `pyclaw start` → desktop | Native window, keyboard shortcuts |
| 🌐 **Web** | `pyclaw start` → web | Browser / phone accessible, dark/light theme |
| 💻 **CLI** | `pyclaw chat` / `pyclaw shell` | Lightweight, script-friendly, headless |

- Dark/Light themes · Chinese/English i18n
- AI auto-names conversations · One-click code copy
- Collapsible reasoning traces in deep-think mode

---

## Built-in Tools

| Tool | Purpose |
|------|---------|
| `ListDir` | Browse directories |
| `FileRead` | Read files |
| `Exec` | Run system commands |
| `Time` | Query date/time |
| `delegate_to` | Delegate tasks to sub-agents |

## Plugin System (8 pre-installed, 36+ tools)

| Plugin | Tools | Purpose |
|--------|-------|---------|
| LK-Cut ✂️ | 13 | Video editing (trim, merge, add BGM/outro) |
| PPT 📊 | 10 layouts | Pure-Python PPTX generation |
| Weather 🌤️ | — | Global weather query |
| Bilibili 📺 | 4 | Bilibili publishing |
| System Info 🖥️ | — | System info & process management |
| Memory 🧠 | — | Long-term memory management |
| Desktop Path 📂 | — | Linux Chinese desktop path helper |
| Skill Manager 🔧 | — | Plugin install / uninstall |

Skills can be written in Markdown (declarative) or Python classes. See [`docs/SKILLS.md`](./docs/SKILLS.md).

---

## Multi-Agent Architecture

1 main agent + up to 5 sub-agents:

| Sub-agent | Permissions | Purpose |
|-----------|-------------|---------|
| ⚡ Exec | Run commands | Scripts, deploy |
| 📁 File | Read/write files | Code editing |
| 🔍 Search | Search + fetch | Web research |
| 🌐 Browser | Search + fetch | Browser automation (WIP) |
| 🖥️ App | Run commands | Desktop operations |

Three tiers: **Basic** (main only) / **Standard** (main + Exec + File) / **Full** (1+5).

---

## Configuration

Multiple API providers supported:

| Provider | Default Model | Base URL |
|----------|--------------|----------|
| **DeepSeek** | `deepseek-v4-flash` | `https://api.deepseek.com/v1` |
| **Volcengine** | `ark-code-latest` | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| **Custom** | Manual input | Any compatible API |

Configure in the Web UI or via `pyclaw config`.

---

## PPT Generation

Pure Python, 10 layouts:

| Layout | Description | Layout | Description |
|--------|------------|--------|------------|
| `title` | Dark cover | `content_light` | Light content |
| `title_center` | Centered cover | `content_dark` | Dark content |
| `two_column` | Two-column | `two_column_dark` | Dark two-column |
| `features` | Feature list | `process` | Step flow |
| `quote` | Quote page | `end` | Closing page |

---

## Long-term Memory

Tell your AI "remember this" and it's saved permanently in `pyclaw_memory.db`.

> Remember my name is Xiaokan

---

## Directory Structure

```
PyClaw/
├── desktop.py          # Desktop app
├── run.py              # Web entry
├── webapp.py           # FastAPI backend
├── index.html          # Frontend (single file, zero build)
├── pyclaw/
│   ├── agent.py        # Agent core
│   ├── gateway.py      # Message routing
│   ├── tools.py        # Built-in tools
│   ├── skill.py        # Plugin system
│   ├── memory.py       # Long-term memory
│   └── ...
├── skills/
│   ├── ppt/            # PPT generation
│   ├── weather/        # Weather
│   ├── bilibili/       # Bilibili
│   └── lk_cut/         # Video editing
├── README.md
└── pyproject.toml
```

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + Uvicorn + WebSocket |
| Frontend | Single-file HTML/CSS/JS, zero build |
| Desktop | pywebview + Edge WebView2 |
| PPT | python-pptx |
| Storage | localStorage + SQLite |

---

## Requirements

- **Python**: 3.9–3.12
- **Install size**: ~10MB
- **Memory**: ~50MB
- **Startup**: <1 second
- **Old hardware friendly**

---

## License

MIT © 2026 Luokan & His OpenClaw

---

<p align="center">
  <sub>🦞 Made by Luokan & His OpenClaw</sub>
</p>
