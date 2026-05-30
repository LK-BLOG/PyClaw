# 🦞 PyClaw — Lightweight Python AI Assistant

**Desktop + Web** — Cross-platform AI agent framework

> **Platform**: Windows ✅ Linux ✅ macOS ✅  
> **Size**: ~10MB | **Memory**: ~50MB | **Startup**: <1s  
> **Python**: 3.8–3.12 | **Old hardware friendly**

---

## Features

### Dual Mode

| Mode | Description | Command |
|------|-------------|---------|
| 🪟 **Desktop** | Native window via pywebview + WebView2 | `python desktop.py` |
| 🌐 **Web** | Open in browser | `python run.py` |

### UI
- Dark/Light theme, Chinese/English i18n, responsive layout
- AI auto-names conversations, one-click code copy
- Collapsible reasoning traces in deep-think mode

### Built-in Tools

| Tool | Description |
|------|-------------|
| 📁 ListDir | List directory contents |
| 📄 FileRead | Read file contents |
| 💻 Exec | Execute system commands |
| ⏰ Time | Query current time |
### Plugins (8 pre-installed, 36+ tools)

| Plugin | Description |
|--------|-------------|
| 🌤️ Weather | Global city weather queries |
| 📺 Bilibili | Bilibili social publishing (4 tools) |
| 🖥️ System Info | System info & process management |
| 📂 Desktop Path | Linux Chinese desktop path helper |
| ✂️ LK-Cut | Video editing toolkit (13 tools) |
| 📊 PPT | Pure Python PPTX generation (10 layouts) |
| 🧠 Memory | Long-term memory management |
| 🔧 Skill Manager | Plugin install/uninstall |

---

## Quick Start

### One-line install
```bash
# Linux / macOS:
bash <(curl -sSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh)
```
```powershell
# Windows (PowerShell):
iwr -useb https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1 | iex
```

### Manual
```bash
git clone git@github.com:LK-BLOG/PyClaw.git
cd PyClaw
python desktop.py          # Desktop
python run.py              # Web
./pyclaw.sh shell          # CLI
./start.sh                 # Auto-detect
```

> **No pip install required.** Python 3.8+ only.

---

## Configuration

Configure in Web UI Settings panel (localStorage).

| Provider | Default Model | Base URL |
|----------|---------------|----------|
| **DeepSeek** | `deepseek-v4-flash` | `https://api.deepseek.com/v1` |
| **Volcengine** | `ark-code-latest` | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| **Custom** | Manual input | Any compatible API |

Models auto-filter when switching providers.

---

## Long-Term Memory

Tell the AI "remember..." to save information permanently. Stored in `pyclaw_memory.db`.

> Remember my name is Xiao Kan, I like concise answers

---

## Coding Principles

1. **Think before coding** — no assumptions, active trade-off analysis
2. **Conciseness first** — minimal code, avoid over-engineering
3. **Precise modification** — change only what must change, match existing style
4. **Goal-driven** — define success criteria, iterate with validation

---

## PPT Generation

10 layout types via pure Python (python-pptx):

| Type | Description | Type | Description |
|------|-------------|------|-------------|
| `title` | Dark cover | `content_light` | Light content |
| `title_center` | Centered cover | `content_dark` | Dark content |
| `two_column` | Two-column | `two_column_dark` | Dark two-column |
| `features` | Feature list | `process` | Step flow |
| `quote` | Quote/ highlight | `end` | Closing page |

---

## Developing a Plugin

```
skills/your_skill/
├── __init__.py     # Plugin code
└── SKILL.md        # Plugin documentation
```

See `skills/ppt/` or `skills/weather/` for examples.

---

## Project Structure

```
pyclaw/
├── desktop.py              # Desktop launcher
├── run.py                  # Web launcher
├── webapp.py               # FastAPI backend
├── index.html              # Frontend (single file)
├── pyclaw/
│   ├── agent.py            # AI Agent core
│   ├── gateway.py          # Message routing
│   ├── tools.py            # Built-in tools
│   ├── skill.py            # Plugin system
│   ├── memory.py           # Long-term memory
│   └── ...
├── skills/
│   ├── ppt/                # PPT generation
│   ├── weather/            # Weather plugin
│   ├── bilibili/           # Bilibili plugin
│   ├── lk_cut/             # Video editing
│   └── ...
├── 启动.bat                # Windows launcher
├── start.sh                # Linux/macOS launcher
└── README.md
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| **Backend** | FastAPI + Uvicorn + WebSocket |
| **Frontend** | Single-file HTML/CSS/JS, zero build |
| **Desktop** | pywebview + Edge WebView2 |
| **PPT** | python-pptx / pure Python (zero deps) |
| **Storage** | localStorage + SQLite |

## License

MIT

Made by Campus & OpenClaw Team
