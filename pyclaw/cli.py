#!/usr/bin/env python3
"""
PyClaw CLI - 命令行界面

Usage: pyclaw <command> [options]

Commands:
  start       启动 PyClaw（桌面/浏览器/后台）
  stop        停止运行中的 PyClaw
  status      查看运行状态
  config      查看/编辑配置
  setup       配置向导
  chat        一句话问答
  shell       交互式 REPL
  version     显示版本
"""

import argparse
import sys
import os
import json
import signal
import time
import subprocess
import re
import socket
import uuid
from pathlib import Path

try:
    import readline  # 启用方向键/退格等行编辑
except ImportError:
    pass

# ── prompt_toolkit（可选）─────────────────────────
try:
    from prompt_toolkit.shortcuts import radiolist_dialog, checkboxlist_dialog
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# ── 路径 ──────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent  # pyclaw/ 项目根目录
# 配置优先: 工作区根 > 项目根 (避免 pyclaw-public 公开仓库暴露 API Key)
CONFIG_FILE = Path(os.environ.get("PYCLAW_CONFIG", "")) if os.environ.get("PYCLAW_CONFIG") else None
if not CONFIG_FILE:
    ws_root = PROJECT_DIR.parent  # workspace/
    ws_cfg = ws_root / "pyclaw.json"
    CONFIG_FILE = ws_cfg if ws_cfg.exists() else PROJECT_DIR / "pyclaw.json"
PID_FILE = PROJECT_DIR / ".pyclaw.pid"

# ── TTY检测 ─────────────────────────────────────
def _is_tty() -> bool:
    """检查 stdin 是否是真正的终端"""
    try:
        import termios
        termios.tcgetattr(sys.stdin.fileno())
        return True
    except Exception:
        return False


# ── 辅助 ──────────────────────────────────────────
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}

def c(text: str, *styles: str) -> str:
    for s in styles:
        if s in COLORS:
            text = COLORS[s] + text
    return text + COLORS["reset"]

PYCLAW_BLUE = "\033[38;2;88;166;255m"      # 亮蓝 #58a6ff
PYCLAW_YELLOW = "\033[38;2;210;153;34m"    # 金黄 #d29922

PYCLAW_ART = [
    (PYCLAW_BLUE, "██████╗ ██╗   ██╗ ██████╗██╗      █████╗ ██╗    ██╗"),
    (PYCLAW_BLUE, "██╔══██╗╚██╗ ██╔╝██╔════╝██║     ██╔══██╗██║    ██║"),
    (PYCLAW_YELLOW, "██████╔╝ ╚████╔╝ ██║     ██║     ███████║██║ █╗ ██║"),
    (PYCLAW_YELLOW, "██╔═══╝   ╚██╔╝  ██║     ██║     ██╔══██║██║███╗██║"),
    (PYCLAW_BLUE, "██║        ██║   ╚██████╗███████╗██║  ██║╚███╔███╔╝"),
    (PYCLAW_BLUE, "╚═╝        ╚═╝    ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝"),
]

def clear_screen():
    """Clear terminal"""
    import sys as _sys
    _sys.stdout.write("\033[2J\033[H")
    _sys.stdout.flush()

def logo(slim=False):
    """Return PYCLAW ASCII art. slim=True returns just the art without padding."""
    lines = []
    if not slim:
        lines.append("")
    for ansi_color, art in PYCLAW_ART:
        styled = ansi_color + art + COLORS["reset"]
        if not slim:
            lines.append("  " + styled)
        else:
            lines.append(styled)
    if not slim:
        lines.append("")
    return "\n".join(lines)

def info_bar(cfg: dict = None):
    """Return info bar with version · model · provider · lang · sessions"""
    from pyclaw import __version__ as _ver
    parts = [c(f"v{_ver}", "dim")]
    _en = False
    if cfg:
        _en = cfg.get("LANGUAGE", "zh-CN") == "en-US"
        model = cfg.get("MODEL", "?") or "?"
        provider = cfg.get("PROVIDER", "?") or "?"
        lang = cfg.get("LANGUAGE", "zh-CN") or "zh-CN"
        user_name = cfg.get("USER_NAME", "")
        parts.append(c(model, "dim"))
        if provider == "deepseek":
            parts.append(c("DeepSeek", "dim"))
        else:
            parts.append(c(provider, "dim"))
        parts.append(c("zh" if lang == "zh-CN" else "en", "dim"))
        if user_name:
            parts.append(c(user_name, "dim"))
    else:
        parts.append(c("?", "dim"))
    import time as _t
    tz = _t.tzname[0] if _t.tzname else "UTC"
    parts.append(c(tz, "dim"))
    
    _suffix = "sessions" if _en else "会话"
    _sessions_dir = PROJECT_DIR / ".sessions"
    if _sessions_dir.exists():
        try:
            _sc = len([f for f in _sessions_dir.iterdir() if f.suffix == ".json" and f.name.startswith("shell_")])
            if _sc:
                parts.append(c(f"{_sc}{_suffix}", "dim"))
        except Exception:
            pass
    
    sep = c(" · ", "dim")
    return c("━━━", "dim") + " " + sep.join(parts)

def read_config() -> dict:
    """读取 pyclaw.json 配置（兼容旧 API.txt）"""
    cfg = {}
    
    # 自动从旧 API.txt 迁移
    old_file = PROJECT_DIR / "API.txt"
    if not CONFIG_FILE.exists() and old_file.exists():
        with open(old_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
                else:
                    cfg["API_KEY"] = line
        write_config(cfg)
        old_file.unlink(missing_ok=True)
        return cfg
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return cfg

def write_config(cfg: dict):
    """写入配置到 pyclaw.json"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")

def find_pid() -> int:
    """查找运行中的 PyClaw PID"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)  # 检查进程是否存在
            return pid
        except (ValueError, ProcessLookupError):
            PID_FILE.unlink(missing_ok=True)
    
    # 也用 pgrep 找
    try:
        result = subprocess.run(
            ["pgrep", "-f", "webapp.py"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            return int(pids[0])
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    return 0

def port_in_use(port: int = 2469) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

# ── 命令实现 ──────────────────────────────────────

def cmd_version(args):
    cfg = read_config()
    print(logo())
    print(info_bar(cfg))
    print()
    from pyclaw import __version__
    print(f"  {c('PyClaw', 'blue')}  v{__version__}")
    print(f"  {c('🐍 Python', 'green')}  {sys.version.split()[0]}")
    print(f"  {c('📂', 'yellow')}  {PROJECT_DIR}")

def cmd_start(args):
    _cfg = read_config()
    _en = _cfg.get("LANGUAGE", "zh-CN") == "en-US"
    
    print(logo())
    print(info_bar(_cfg))
    print()
    
    mode = args.mode
    if not mode:
        if _en:
            print(f"  {c('◆ PyClaw · Start', 'blue')}")
            print()
            print(f"    {c('1', 'cyan')})  {c('[D] Desktop', 'bold')}    — Native window")
            print(f"    {c('2', 'cyan')})  {c('[B] Browser', 'bold')}    — Web interface (:2469)")
            print(f"    {c('3', 'cyan')})  {c('[G] Background', 'bold')}  — Run in background")
            print(f"  {c('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'dim')}")
            choice = input(f"\n  {c('Select mode [1-3, default 2]', 'dim')}: ").strip() or "2"
        else:
            print(f"  {c('◆ PyClaw · 启动', 'blue')}")
            print()
            print(f"    {c('1', 'cyan')})  {c('[D] Desktop', 'bold')}    — 桌面窗口")
            print(f"    {c('2', 'cyan')})  {c('[B] Browser', 'bold')}    — 浏览器 (:2469)")
            print(f"    {c('3', 'cyan')})  {c('[G] Background', 'bold')}  — 后台服务")
            print(f"  {c('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'dim')}")
            choice = input(f"\n  {c('选择模式 [1-3，默认 2]', 'dim')}: ").strip() or "2"
        mode = {"1": "desktop", "2": "browser", "3": "background"}.get(choice, "browser")
    
    python = sys.executable
    
    if mode == "desktop":
        print(f"  {c('-> Starting Desktop...', 'green')}")
        os.chdir(PROJECT_DIR)
        os.execvp(python, [python, "desktop.py"])
    
    elif mode == "browser":
        msg = "-> Starting Browser..." if _en else "-> Starting Browser..."
        print(f"  {c(msg, 'green')}")
        os.chdir(PROJECT_DIR)
        proc = subprocess.Popen(
            [python, "webapp.py"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        PID_FILE.write_text(str(proc.pid))
        print(f"  PID: {proc.pid}")
        print(f"    http://localhost:2469")
        try:
            for line in proc.stdout:
                sys.stdout.buffer.write(line)
        except KeyboardInterrupt:
            ctrlc_msg = "  Ctrl+C received, shutting down..." if _en else "  Ctrl+C received，正在关闭..."
            print(f"\n  {c(ctrlc_msg, 'yellow')}")
            proc.terminate()
            proc.wait()
            PID_FILE.unlink(missing_ok=True)
    
    else:  # background
        msg = "-> Starting background service..." if _en else "-> Starting background service..."
        print(f"  {c(msg, 'green')}")
        os.chdir(PROJECT_DIR)
        proc = subprocess.Popen(
            [python, "webapp.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        PID_FILE.write_text(str(proc.pid))
        print(f"  PID: {proc.pid}  (pid saved to {PID_FILE})")
        print(f"    http://localhost:2469")
        stop_msg = "Stop: pyclaw stop" if _en else "停止: pyclaw stop"
        print(f"  {c(stop_msg, 'dim')}")

def cmd_stop(args):
    cfg = read_config()
    print(logo())
    print(info_bar(cfg))
    print()
    pid = find_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.3)
            except ProcessLookupError:
                break
        PID_FILE.unlink(missing_ok=True)
        print(f"  {c('●', 'green')} PyClaw {c('stopped', 'green')}  (PID {pid})")
    else:
        print(f"  {c('●', 'yellow')} PyClaw {c('not running', 'yellow')}")

def cmd_status(args):
    cfg = read_config()
    _en = cfg.get("LANGUAGE", "zh-CN") == "en-US"
    
    def _kv(k, v):
        pad = max(0, 8 - len(k))
        dots = "·" * max(4, pad)
        return f"    {c(k, 'cyan')}  {c(dots, 'dim')} {v}"

    print(logo())
    print(info_bar(cfg))
    print()
    pid = find_pid()
    running = port_in_use()
    
    if pid:
        run_msg = "is running" if _en else "运行中"
        print(f"  {c('●', 'green')} PyClaw {c(run_msg, 'green')}")
        print()
        pid_label = "PID" if _en else "进程"
        print(_kv(pid_label, pid))
        port_label = "Port" if _en else "端口"
        print(_kv(port_label, '2469'))
        model_label = "Model" if _en else "模型"
        print(_kv(model_label, cfg.get("MODEL", "?")))
        try:
            import psutil
            p = psutil.Process(pid)
            created = p.create_time()
            uptime_sec = time.time() - created
            if _en:
                uptime_str = f"{int(uptime_sec//3600)}h {int((uptime_sec%3600)//60)}m"
            else:
                uptime_str = f"{int(uptime_sec//3600)}时 {int((uptime_sec%3600)//60)}分"
            mem = p.memory_info().rss // 1048576
            uptime_label = "Uptime" if _en else "运行时长"
            mem_label = "Memory" if _en else "内存"
            print(_kv(uptime_label, uptime_str))
            print(_kv(mem_label, f'{mem} MB'))
        except Exception:
            pass
    else:
        if running:
            msg = "port in use" if _en else "端口占用"
            print(f"  {c('●', 'yellow')} PyClaw {c(msg, 'yellow')}")
        else:
            msg = "not running" if _en else "未在运行"
            print(f"  {c('●', 'red')} PyClaw {c(msg, 'red')}")
        print()
        port_label = "Port" if _en else "端口"
        port_icon = '🟡' if running else '🔴'
        print(_kv(port_label, f'2469 {port_icon}'))
    
    api_key = cfg.get("API_KEY", "")
    if api_key:
        masked = api_key[:6] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 16 else "****"
        print(_kv('API Key', masked))
    else:
        warn = "No API Key (run pyclaw setup)" if _en else "未配置 API Key（运行 pyclaw setup）"
        print(f"  {c(f'  ⚠️  {warn}', 'yellow')}")

def cmd_config(args):
    cfg = read_config()
    print(logo())
    print(info_bar(cfg))
    print()
    
    if args.kv == "show" or not args.kv:
        try:
            cfg_rel = CONFIG_FILE.relative_to(PROJECT_DIR)
        except ValueError:
            cfg_rel = CONFIG_FILE
        print(f"  {c('◆ Config', 'blue')}  {c(f'({cfg_rel})', 'dim')}")
        print()
        if not cfg:
            print(f"    {c('(empty)', 'dim')}")
        for k, v in cfg.items():
            if k == "API_KEY" and len(v) > 8:
                v = v[:6] + "*" * (len(v) - 10) + v[-4:]
            pad = max(0, 12 - len(k))
            dots = "·" * max(4, pad)
            print(f"    {c(k, 'cyan')}  {c(dots, 'dim')} {v}")
        print()
    
    elif args.kv == "set":
        key = args.value
        val = args.__dict__.get("value2")
        # parse key=value format
        if "=" in (key or ""):
            key, val = key.split("=", 1)
        if key and val:
            cfg[key.upper()] = val
            write_config(cfg)
            print(f"  {c(f'{key.upper()} = {val}', 'green')}")
        else:
            usage = "Usage: pyclaw config set KEY=VALUE" if _en else "用法: pyclaw config set KEY=VALUE"
            print(f"  {c(usage, 'yellow')}")
    
    elif args.kv == "edit":
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {CONFIG_FILE}")

    # 兼容 set key=value 语法
    if args.kv and "=" in args.kv:
        key, val = args.kv.split("=", 1)
        cfg[key.upper()] = val
        write_config(cfg)
        print(f"  {c(f'{key.upper()} = {val}', 'green')}")

def cmd_setup(args):
    cfg = read_config()
    lang = cfg.get("LANGUAGE", "zh-CN")
    
    if lang == "en-US":
        T = lambda zh, en: en
    else:
        T = lambda zh, en: zh
    
    print(logo())
    print(info_bar(cfg))
    print()
    print(f"  {c(T('◆ PyClaw · Setup', '◆ PyClaw · Setup'), 'blue')}")
    print()
    print(f"  {c(T('↑↓ navigate · Enter confirm · Space toggle', '↑↓ navigate · Enter confirm · Space toggle'), 'dim')}\n")
    
    # 1. API Key
    current = cfg.get("API_KEY", "")
    masked = current[:6] + "****" + current[-4:] if len(current) > 12 else ""
    prompt = f"  {T('🔑 API Key', '🔑 API Key')} [{c(masked, 'dim')}]: " if masked else f"  {T('🔑 API Key', '🔑 API Key')}: "
    val = input(prompt).strip()
    if val:
        cfg["API_KEY"] = val
    print()
    
    # 1.5 User Name
    current_name = cfg.get("USER_NAME", "")
    val = input(f"  {T('👤 你的名字', '👤 Your name')} [{c(current_name or 'User', 'dim')}]: ").strip()
    if val:
        cfg["USER_NAME"] = val
    print()
    
    # 2. Provider
    provider_list = [("deepseek", "DeepSeek"), ("openai", "OpenAI"), ("opencode-zen", "OpenCode Zen"), ("ollama", "Ollama (本地)"), ("custom", T("自定义", "Custom"))]
    provider_default = 0
    for i, (k, _) in enumerate(provider_list):
        if k == cfg.get("PROVIDER", "opencode-zen"):
            provider_default = i
            break
    print(f"\n  {T('📡 模型提供商 (↑↓ 选择)', '📡 Provider (↑↓ select)')}:")
    idx = arrow_select([n for _, n in provider_list], provider_default)
    cfg["PROVIDER"] = provider_list[idx][0]
    print(f"\r  {c(T('提供商: ', 'Provider: ') + provider_list[idx][1], 'green')}")
    
    # 3. Model
    provider_name = cfg.get("PROVIDER", "")
    if provider_name == "ollama":
        # 检测本地 Ollama 模型
        model_list = ["llama3", "llama3.1", "qwen2", "qwen2.5", "mistral", "deepseek-coder-v2", "gemma2"]
        try:
            import json, urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read())
                local_models = [m["name"] for m in data.get("models", [])]
                if local_models:
                    model_list = local_models
                    print(f"  {c('[Ollama] Local models: ' + ', '.join(local_models), 'green')}")
        except Exception:
            pass
    else:
        model_list = ["deepseek-v4-flash-free", "deepseek-chat", "deepseek-v4-flash", "gpt-4o", "gpt-4o-mini"]
    model_default = 0
    for i, m in enumerate(model_list):
        if m == cfg.get("MODEL", "deepseek-v4-flash-free"):
            model_default = i
            break
    print(f"\n  {T('Model (↑↓ select)', 'Model (↑↓ select)')}:")
    idx = arrow_select(model_list, model_default)
    cfg["MODEL"] = model_list[idx]
    print(f"\r  {c(T('Model: ', 'Model: ') + model_list[idx], 'green')}")
    
    # 4. Port
    current_port = str(cfg.get("PORT", "2469"))
    val = input(f"\n  {T('Port', 'Port')} [{c(current_port, 'dim')}]: ").strip()
    if val:
        cfg["PORT"] = val
    
    # 5. Thinking
    endpoint = cfg.get("ENDPOINT", "")
    is_local = any(h in endpoint for h in ["localhost", "127.0.0.1", "0.0.0.0"])
    if is_local:
        cfg["THINKING"] = "off"
        print(f"  {c('Thinking: off (local model)', 'dim')}")
    else:
        current_thinking = str(cfg.get("THINKING", "on"))
        val = input(f"  {T('Thinking (on/off)', 'Thinking (on/off)')} [{c(current_thinking, 'dim')}]: ").strip()
        if val:
            cfg["THINKING"] = val
    
    # 6. Language
    lang_list = ["zh-CN", "en-US"]
    lang_default = 0
    for i, l in enumerate(lang_list):
        if l == cfg.get("LANGUAGE", "zh-CN"):
            lang_default = i
            break
    print(f"\n  {T('Language (↑↓ select)', 'Language (↑↓ select)')}:")
    idx = arrow_select([T("中文", "Chinese") if l == "zh-CN" else "English" for l in lang_list], lang_default)
    cfg["LANGUAGE"] = lang_list[idx]
    print(f"\r  {c(f'' + T('语言: ', 'Language: ') + lang_list[idx], 'green')}")
    lang = lang_list[idx]
    
    # 7. Endpoint（只有自定义才问）
    endpoint_map = {
        "deepseek": "https://api.deepseek.com",
        "openai": "https://api.openai.com/v1",
        "opencode-zen": "https://opencode.ai/zen/v1",
        "ollama": "http://localhost:11434/v1",
    }
    provider_name = cfg.get("PROVIDER", "opencode-zen")
    if provider_name in endpoint_map:
        cfg["ENDPOINT"] = endpoint_map[provider_name]
        print(f"  {c(f'Endpoint: {endpoint_map[provider_name]}', 'dim')}")
    else:
        current_endpoint = cfg.get("ENDPOINT", "")
        val = input(f"  {T('Custom Endpoint', 'Custom Endpoint')} [{c(current_endpoint or T('必填', 'required'), 'dim')}]: ").strip()
        if val:
            cfg["ENDPOINT"] = val
    
    # 8. Skill 管理 (Space=移入回收站, Enter=确认)
    skill_dir = PROJECT_DIR / "skills"
    trash_dir = skill_dir / ".trash"
    active_skills = []
    trashed_skills = []
    
    if skill_dir.exists():
        active_skills = sorted([
            d.name for d in skill_dir.iterdir()
            if d.is_dir() and (d / "__init__.py").exists() and d.name != "__pycache__" and d.name != ".trash"
        ])
        if trash_dir.exists():
            trashed_skills = sorted([
                d.name for d in trash_dir.iterdir()
                if d.is_dir() and d.name != "__pycache__"
            ])
    
    all_skill_names = active_skills + [c(f"[{s}]", "dim") for s in trashed_skills]
    if all_skill_names:
        skill_defaults = set(range(len(active_skills)))
        
        print(f"\n  {T('Skills (Space=trash/restore, Enter=confirm)', 'Skills (Space=trash/restore, Enter=confirm)')}:")
        print(f"     {c(T('[名称] = 回收站中', '[name] = in trash'), 'dim')}")
        sel = checkbox_select(all_skill_names, skill_defaults, _en=lang == "en-US")
        
        for i, name in enumerate(active_skills):
            if i not in sel:
                src = skill_dir / name
                dst = trash_dir / name
                trash_dir.mkdir(exist_ok=True)
                src.rename(dst)
                print(f"  {c(f'{T("Trashed: ", "Trashed: ")}' + name, 'yellow')}")
        
        trashed_count = len(trashed_skills)
        active_count = len(active_skills)
        for j, name in enumerate(trashed_skills):
            if active_count + j in sel:
                src = trash_dir / name
                dst = skill_dir / name
                src.rename(dst)
                print(f"  {c(f'{T("Restored: ", "Restored: ")}' + name, 'green')}")
        
        print(f"  {c(T('Skills updated', 'Skills updated'), 'green')}")
    else:
        print(f"\n  {T('No skills found', 'No skills found')}")
    
    # 保存所有配置
    write_config(cfg)
    print(f"  {c(T('Config saved to pyclaw.json', 'Config saved to pyclaw.json'), 'green')}")
    
def cmd_chat(args):
    import asyncio
    from pyclaw.agent import Agent, SubAgentManager
    from pyclaw.pyclaw_types import Message, MessageRole, ToolDefinition, ToolResult
    
    cfg = read_config()
    _en = cfg.get("LANGUAGE", "zh-CN") == "en-US"
    message = " ".join(args.message)
    you_label = "You" if _en else "You"
    print(f"  {you_label}: {message}\n")
    
    async def _chat():
        cfg = read_config()
        api_key = cfg.get("API_KEY", "")
        if not api_key:
            warn = "⚠️ No API Key configured" if _en else "⚠️ 未配置 API Key"
            print(f"  {c(warn, 'yellow')}")
            return
        provider = cfg.get("PROVIDER", "opencode-zen")
        base_urls = {
            "deepseek": "https://api.deepseek.com",
            "openai": "https://api.openai.com/v1",
            "opencode-zen": "https://opencode.ai/zen/v1",
        }
        base_url = cfg.get("ENDPOINT") or base_urls.get(provider, "https://api.deepseek.com")
        model = cfg.get("MODEL", "deepseek-v4-flash-free")
        lang = cfg.get("LANGUAGE", "zh-CN")
        agent = Agent(api_key=api_key, base_url=base_url, model=model, language=lang)
        # 本地模型不支持思考模式
        base_url = cfg.get("ENDPOINT", "")
        is_local = any(h in base_url for h in ["localhost", "127.0.0.1", "0.0.0.0"])
        if is_local:
            agent.thinking = False
        else:
            agent.thinking = cfg.get("THINKING", "on") == "on"
        
        # 注册多Agent协作
        sub_agent_manager = SubAgentManager(agent)
        class DelegateTool:
            def __init__(self, mgr):
                self.mgr = mgr
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="delegate_to",
                    description="委派任务给子代理执行。exec:命令 file:文件 search:搜索 browser:浏览器 app:桌面",
                    parameters={
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "enum": ["exec", "file", "search", "browser", "app"], "description": "目标子代理"},
                            "task": {"type": "string", "description": "要委派的任务描述"}
                        },
                        "required": ["agent", "task"]
                    }
                )
            async def execute(self, params) -> ToolResult:
                agent_name = params.get("agent", "")
                task = params.get("task", "")
                if not agent_name or not task:
                    return ToolResult(success=False, content="", error="需要 agent 和 task 参数")
                result = await self.mgr.delegate(agent_name, task)
                return ToolResult(success=True, content=str(result))
        agent.register_tool(DelegateTool(sub_agent_manager))
        
        msg = Message(
            id=f"cli_{uuid.uuid4().hex[:8]}",
            content=message,
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="cli",
            session_id="cli",
        )
        resp = await agent.chat([msg])
        if resp.error:
            err_label = "Error" if _en else "错误"
            print(f"\n  {c(f'❌ {err_label}: ' + resp.error, 'red')}")
        else:
            print(resp.content or "")
    
    asyncio.run(_chat())

def cmd_shell(args):
    import asyncio
    from pyclaw.agent import Agent
    from pyclaw.pyclaw_types import Message, MessageRole
    
    cfg = read_config()
    _en = cfg.get("LANGUAGE", "zh-CN") == "en-US"
    
    clear_screen()
    
    # 填充终端高度
    import shutil as _shutil
    _term_h = _shutil.get_terminal_size().lines
    _fill = max(0, (_term_h - 20) // 2)
    print("\n" * _fill, end="")
    
    print(logo())
    print(info_bar(cfg))
    print()
    
    model_tag = cfg.get("MODEL", "?")
    connected = c("●", "green")
    badge_model = c(f"[{model_tag}]", "blue")
    badge_help = c("/help", "dim")
    
    if _en:
        print(f"  {connected} Connected · {badge_model} · type {badge_help} for commands")
    else:
        print(f"  {connected} 已连接 · {badge_model} · 输入 {badge_help} 查看帮助")
    print(f"  {c('─────────────────────────────────────────────────────────', 'dim')}")
    
    async def _run():
        cfg = read_config()
        _en = cfg.get("LANGUAGE", "zh-CN") == "en-US"
        api_key = cfg.get("API_KEY", "")
        if not api_key:
            msg = "⚠️ No API Key configured. Run 'pyclaw setup' first" if _en else "⚠️ 未配置 API Key，请先运行 pyclaw setup"
            print(f"  {c(msg, 'yellow')}")
            return
        provider = cfg.get("PROVIDER", "opencode-zen")
        base_urls = {
            "deepseek": "https://api.deepseek.com",
            "openai": "https://api.openai.com/v1",
            "opencode-zen": "https://opencode.ai/zen/v1",
        }
        base_url = cfg.get("ENDPOINT") or base_urls.get(provider, "https://api.deepseek.com")
        model = cfg.get("MODEL", "deepseek-v4-flash-free")
        lang = cfg.get("LANGUAGE", "zh-CN")
        # 确保 skill 目录指向项目目录（而非 CWD）
        from pyclaw.skill import skill_manager
        skill_manager.skill_dir = PROJECT_DIR / "skills"
        skill_manager.skill_dir.mkdir(exist_ok=True)
        from pyclaw.gateway import Gateway
        sessions_dir = PROJECT_DIR / ".sessions"
        sessions_dir.mkdir(exist_ok=True)
        # 静默初始化（重定向 stdout 到 /dev/null 防止 Gateway/Skill 加载信息打印）
        import contextlib as _ctx
        with open(os.devnull, 'w') as _null, _ctx.redirect_stdout(_null):
            gateway = Gateway(
                llm_api_key=api_key,
                storage_path=str(sessions_dir),
                base_url=base_url,
                model=model,
                language=lang,
            )
            # 本地模型不支持思考模式
            base_url = cfg.get("ENDPOINT", "")
            is_local = any(h in base_url for h in ["localhost", "127.0.0.1", "0.0.0.0"])
            if is_local:
                gateway.agent.thinking = False
            else:
                gateway.agent.thinking = cfg.get("THINKING", "on") == "on"
            await gateway.initialize_skills()
        bye_msg = "👋 Bye!" if _en else "👋 再见！"
        _T = lambda zh, en: en if _en else zh
        
        # ── 扫描现有会话 ──
        def _list_sessions():
            """从 pyclaw_sessions.json 读取所有会话，返回 [(id, name, last_active, preview), ...]"""
            sf = sessions_dir / "pyclaw_sessions.json"
            if not sf.exists():
                return []
            try:
                with open(sf) as f:
                    data = json.load(f)
                rows = []
                for sid, sdata in data.get("sessions", {}).items():
                    msgs = sdata.get("messages", [])
                    preview = ""
                    for m in reversed(msgs):
                        if m.get("role") == "user":
                            preview = m["content"][:60].replace("\n", " ")
                            break
                    last_ts = sdata.get("last_active_at", sdata.get("created_at", 0))
                    rows.append((sid, preview, last_ts))
                rows.sort(key=lambda r: r[2], reverse=True)
                return rows
            except Exception:
                return []
        
        def _pick_session():
            """会话选择器"""
            sessions = _list_sessions()
            fresh_label = c(_T("✨ 新会话", "✨ New Session"), "green")
            if not sessions:
                return "cli", True
            
            print(f"\n  {c(_T('📋 选择会话:', '📋 Choose Session:'), 'bold')}")
            print()
            now = time.time()
            options = [(None, fresh_label)]
            for i, (sid, preview, ts) in enumerate(sessions[:8]):
                ago = now - ts
                if ago < 60:
                    time_str = _T("刚刚", "just now")
                elif ago < 3600:
                    time_str = _T(f"{int(ago//60)}分钟前", f"{int(ago//60)}m ago")
                elif ago < 86400:
                    time_str = _T(f"{int(ago//3600)}小时前", f"{int(ago//3600)}h ago")
                else:
                    days = int(ago // 86400)
                    time_str = _T(f"{days}天前", f"{days}d ago")
                label = f"  {c(str(i+1), 'cyan')})  {c(preview or sid, 'bold')}  {c(time_str, 'dim')}"
                options.append((sid, label))
            
            # 历史会话（已自带编号）
            for _, label in options[1:]:
                print(label)
            # 新会话选项
            new_idx = len(sessions) + 1
            print(f"  {c(str(new_idx), 'cyan')})  {fresh_label}")
            
            max_n = new_idx
            prompt = _T(f"选择会话 [1-{max_n}, 默认新建]", f"Pick session [1-{max_n}, default new]")
            val = input(f"\n  {c(prompt, 'dim')}: ").strip()
            if val and val.isdigit():
                idx = int(val)
                if 1 <= idx < new_idx:
                    sid = options[idx][0]
                    if sid:
                        return sid, False
                # 输入的是新建会话的编号
                if idx == new_idx:
                    return _gen_id(), True
            return _gen_id(), True
        
        def _gen_id():
            return f"s_{time.strftime('%m%d')}_{uuid.uuid4().hex[:4]}"
        
        # ── 选择/新建会话 ──
        session_id, is_new = _pick_session()
        if not is_new:
            joined_label = _T(f"已恢复会话", f"Resumed session")
            print(f"  {c(f'{joined_label}: {session_id}', 'dim')}")
        else:
            new_label = _T(f"新会话", f"New session")
            preview = _list_sessions()
            nth = len([s for s in preview if s[0].startswith(f"s_{time.strftime('%m%d')}")]) + 1
            session_id = f"s_{time.strftime('%m%d')}_{uuid.uuid4().hex[:4]}"
            print(f"  {c(f'{new_label}: {session_id}', 'dim')}")
        print(f"  {c('─────────────────────────────────────────────────────────', 'dim')}")
        
        # ── 主循环 ──
        while True:
            try:
                ts = time.strftime("%H:%M:%S")
                msg_text = input(f"\n  {c('You', 'blue')} {c(ts, 'dim')}  {c(f'[{session_id}]', 'dim')}\n{'> '}")
            except (EOFError, KeyboardInterrupt):
                print(f"\n  {c(bye_msg, 'green')}")
                break
            
            if not msg_text.strip():
                continue
            
            # ── 会话管理命令 ──
            cmd = msg_text.strip().lower()
            if cmd in ("/exit", "/quit", "exit", "quit"):
                print(f"  {c(bye_msg, 'green')}")
                break
            if cmd == "/sessions":
                sessions = _list_sessions()
                if not sessions:
                    print(f"  {c(_T('没有历史会话', 'No sessions yet'), 'dim')}")
                else:
                    print(f"  {c(_T('历史会话:', 'Sessions:'), 'bold')}")
                    for sid, preview, ts in sessions[:10]:
                        mark = c("●", "green") if sid == session_id else c("○", "dim")
                        ts_str = time.strftime("%m-%d %H:%M", time.localtime(ts))
                        print(f"    {mark} {c(sid, 'cyan')}  {c(preview[:50], 'dim')}  {c(ts_str, 'dim')}")
                continue
            if cmd.startswith("/session "):
                target = cmd[9:].strip()
                if target:
                    session_id = target
                    print(f"  {c(_T(f'切换到: {target}', f'Switched to: {target}'), 'green')}")
                continue
            if cmd == "/new":
                session_id = _gen_id()
                print(f"  {c(_T(f'新会话: {session_id}', f'New session: {session_id}'), 'green')}")
                continue
            if cmd in ("/compact", "/c"):
                result = await gateway.compact_session(session_id)
                print(f"  {c(result, 'green')}")
                continue
            
            # ── 正常对话 ──
            print(f"  {c('PyClaw', 'purple')} {c(ts, 'dim')}  {c(f'[{session_id}]', 'dim')}")
            response = await gateway.chat_text(msg_text, session_id)
            if response:
                from rich.console import Console as _Console
                from rich.markdown import Markdown as _Markdown
                _console = _Console(width=80, highlight=False)
                _md = _Markdown(response, code_theme="monokai")
                _console.print(_md)
            else:
                print(f"    {c('(no response)', 'dim')}")
    
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        bye_msg = "👋 Bye!" if _en else "👋 再见！"
        print(f"\n  {c(bye_msg, 'green')}")


# ── 交互选择 ──────────────────────────────────

def arrow_select(options: list, default: int = 0) -> int:
    """Arrow-key single select. Returns index."""
    if HAS_PROMPT_TOOLKIT:
        values = [(i, opt) for i, opt in enumerate(options)]
        result = radiolist_dialog(
            title=None,
            text="",
            values=values,
            default=default,
        ).run()
        if result is not None:
            return result
        return default

    # Fallback: no TTY → pick default
    if not _is_tty():
        print(f"\n  (non-interactive: using default: {options[default]})")
        return default
    
    idx = default
    print()
    while True:
        # 先清屏（消除上一轮残留）
        print(f"\x1b[J", end="")
        for i, opt in enumerate(options):
            prefix = c(" ●", "cyan") if i == idx else c(" ○", "dim")
            print(f"{prefix} {opt}\x1b[K")
        if idx < len(options) - 1:
            print(f"\x1b[{len(options)}A", end="", flush=True)
        ch = _getch()
        if ch == '\x1b[A':  # Up
            idx = (idx - 1) % len(options)
        elif ch == '\x1b[B':  # Down
            idx = (idx + 1) % len(options)
        elif ch in ('\r', '\n'):
            break
    return idx

def checkbox_select(items: list, defaults: set = set(), _en: bool = False) -> set:
    """Space to toggle, Enter to confirm. Returns set of selected indices."""
    if HAS_PROMPT_TOOLKIT:
        values = [(i, item) for i, item in enumerate(items)]
        result = checkboxlist_dialog(
            title=None,
            text="",
            values=values,
            default_values=list(defaults),
        ).run()
        if result is not None:
            return set(result)
        return defaults
    
    selected = set(defaults)
    
    # Non-TTY fallback: text-based input
    if not _is_tty():
        print(f"\n  {c('(non-interactive: enter numbers to toggle, empty=confirm)', 'dim')}")
        while True:
            for i, item in enumerate(items):
                check = "[x]" if i in selected else "[ ]"
                print(f"    {i}) {check} {item}")
            val = input(f"  {c('Toggle (e.g. "0 2 4") or Enter to confirm:', 'dim')} ").strip()
            if not val:
                break
            for token in val.split():
                try:
                    i = int(token)
                    if 0 <= i < len(items):
                        if i in selected:
                            selected.discard(i)
                        else:
                            selected.add(i)
                except ValueError:
                    pass
            # Redraw
            print(f"\x1b[{len(items)}A", end="")
            for _ in range(len(items)):
                print(f"\x1b[K\n", end="")
            print(f"\x1b[{len(items)}A", end="", flush=True)
        return selected
    
    idx = 0
    print()
    while True:
        print(f"\x1b[J", end="")
        for i, item in enumerate(items):
            check = c("■", "green") if i in selected else c("□", "dim")
            prefix = c("→", "cyan") if i == idx else "  "
            print(f"{prefix} {check} {item}\x1b[K")
        _cb_txt = "Space toggle · Enter confirm · ↑↓ navigate" if _en else "Space 切换选中 • Enter 确认 • ↑↓ 移动"
        print(f"  {c(_cb_txt, 'dim')}\x1b[K")
        print(f"\x1b[{len(items)+1}A", end="", flush=True)
        ch = _getch()
        if ch == '\x1b[A':
            idx = (idx - 1) % len(items)
        elif ch == '\x1b[B':
            idx = (idx + 1) % len(items)
        elif ch == ' ':
            if idx in selected:
                selected.discard(idx)
            else:
                selected.add(idx)
        elif ch in ('\r', '\n'):
            break
    # Clear interface
    print(f"\x1b[{len(items)+1}B", end="")
    for _ in range(len(items) + 1):
        print(" " * 80, end="")
    print(f"\x1b[{len(items)+1}A", end="")
    return selected

# ── 入口 ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="pyclaw",
        description="PyClaw AI 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{c('命令示例:', 'dim')}
  pyclaw setup                 打开配置向导
  pyclaw start                 启动（交互式选择模式）
  pyclaw start --mode browser  浏览器模式启动
  pyclaw start --mode desktop  桌面模式启动
  pyclaw stop                  停止 PyClaw
  pyclaw status                查看状态
  pyclaw config                查看配置
  pyclaw config API_KEY=sk-xxx 设置配置
  pyclaw chat "你好"            一句话问答
  pyclaw shell                 交互式对话
""",
    )
    
    parser.add_argument("--version", "-v", action="store_true", help="显示版本")
    
    sub = parser.add_subparsers(dest="command", metavar="")
    
    p_start = sub.add_parser("start", help="启动 PyClaw")
    p_start.add_argument("--mode", "-m", choices=["desktop", "browser", "background"],
                         help="启动模式")
    p_start.add_argument("--port", "-p", type=int, default=2469, help="端口（默认 2469）")
    
    sub.add_parser("stop", help="停止 PyClaw")
    sub.add_parser("status", help="查看运行状态")
    
    p_config = sub.add_parser("config", help="查看/设置配置")
    p_config.add_argument("kv", nargs="?", help="KEY=VALUE 或 show/edit")
    
    sub.add_parser("setup", help="配置向导")
    
    p_chat = sub.add_parser("chat", help="一句话问答")
    p_chat.add_argument("message", nargs="+", help="消息内容")
    
    sub.add_parser("shell", help="交互式 REPL")
    

    sub.add_parser("version", help="显示版本信息")
    
    args = parser.parse_args()
    
    if args.version:
        cmd_version(args)
        return
    
    if args.command is None:
        parser.print_help()
        return
    
    cmds = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "config": cmd_config,
        "setup": cmd_setup,
        "chat": cmd_chat,
        "shell": cmd_shell,
        "version": cmd_version,
    }
    
    if args.command in cmds:
        cmds[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
