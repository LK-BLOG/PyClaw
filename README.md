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
| 🤖 delegate_to | Delegate tasks to sub-agents |

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

### Multi-Agent Architecture (1+5)

| Sub-agent | Tool Permissions | Purpose |
|-----------|------------------|---------|
| ⚡ **Exec** | `exec_command` | Execute system commands |
| 📁 **File** | `read_file`, `list_directory`, `write_file` | File read/write |
| 🔍 **Search** | `web_search`, `fetch_url` | Web search & fetch |
| 🌐 **Browser** | `web_search`, `fetch_url` | Browser automation (WIP) |
| 🖥️ **App** | `exec_command` | Desktop app operations |

**Modes**: Basic (main only) / Standard (1+2: Main + Exec + File) / Full (1+5)

Switch in Settings → Agent Architecture. Create custom sub-agents via conversation.

---

## CLI (Command Line)

### Shell script (no pip, no PEP 668 issues)

```bash
cd pyclaw/
chmod +x pyclaw.sh

# Add to PATH:
ln -sf "$(pwd)/pyclaw.sh" ~/.local/bin/pyclaw
ln -sf "$(pwd)/pyclaw.sh" ~/.local/bin/pyc      # shorter alias

# Now use it:
pyclaw setup
pyclaw start
```

### pip install (may need `--break-system-packages` in Ubuntu 24.04+)

```bash
cd pyclaw/
pip install --break-system-packages -e .
pyclaw setup
```

### Commands

| Command | Description |
|---------|-------------|
| `pyclaw setup` | Configuration wizard (API Key, model, port, thinking) |
| `pyclaw start` | Start server (interactive mode selection) |
| `pyclaw stop` | Stop running PyClaw |
| `pyclaw status` | Check running status |
| `pyclaw config` | View / set configuration |
| `pyclaw chat "hello"` | One-shot Q&A, get reply and exit |
| `pyclaw shell` | Interactive REPL chat session |
| `pyclaw version` | Show version info |

---

## Quick Start

### One-click
```bash
# Windows: Double-click 启动.bat
# Linux/macOS: ./start.sh
```
Auto-detects Python 3, installs dependencies, starts & opens UI.

### Manual
```bash
python desktop.py          # Desktop (recommended)
python run.py              # Web
python run.py --allow-external   # LAN access
```

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

Two ways to create a Skill:

### 🆕 Declarative (Recommended)

```
skills/your-skill/
└── SKILL.md       ← Pure Markdown, LLM reads it directly
```

No Python needed. No tool registration. Just tell the LLM what to do.

### Legacy: Programmatic

```
skills/your-skill/
├── __init__.py     # Python class with ToolDefinition
└── SKILL.md        # Additional documentation
```

See `skills/ppt/` for an example. For the new declarative format, see `SKILLS.md`.

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
