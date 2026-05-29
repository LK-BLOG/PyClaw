#!/usr/bin/env python3
"""
🦞 PyClaw CLI - 命令行界面

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
from pathlib import Path

# ── 路径 ──────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent  # pyclaw/ 项目根目录
CONFIG_FILE = PROJECT_DIR / "API.txt"
PID_FILE = PROJECT_DIR / ".pyclaw.pid"

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

def logo():
    return c("""
   ╔══════════════════════════════╗
   ║     🦞 PyClaw AI CLI        ║
   ╚══════════════════════════════╝
""", "cyan")

def read_config() -> dict:
    """读取 API.txt 配置"""
    cfg = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
                else:
                    # 只有一行，当作 API_KEY
                    cfg["API_KEY"] = line
    return cfg

def write_config(cfg: dict):
    """写入配置到 API.txt"""
    with open(CONFIG_FILE, "w") as f:
        f.write("# PyClaw 配置\n")
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")

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
    except:
        pass
    return 0

def port_in_use(port: int = 2469) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

# ── 命令实现 ──────────────────────────────────────

def cmd_version(args):
    print(logo())
    print(f"  PyClaw  v1.0.0")
    print(f"  🐍 Python  {sys.version.split()[0]}")
    print(f"  📂 {PROJECT_DIR}")

def cmd_start(args):
    print(logo())
    
    mode = args.mode
    if not mode:
        print("  📋 选择启动模式：")
        print(f"    {c('1', 'cyan')}) 🖥️  Desktop  桌面窗口")
        print(f"    {c('2', 'cyan')}) 🌐  Browser  浏览器")
        print(f"    {c('3', 'cyan')}) 🔧  后台服务")
        choice = input(f"\n  {c('请输入 (1/2/3，默认 2)', 'dim')}: ").strip() or "2"
        mode = {"1": "desktop", "2": "browser", "3": "background"}.get(choice, "browser")
    
    python = sys.executable
    
    if mode == "desktop":
        print(f"  {c('🚀 启动 Desktop 模式...', 'green')}")
        os.chdir(PROJECT_DIR)
        os.execvp(python, [python, "desktop.py"])
    
    elif mode == "browser":
        print(f"  {c('🚀 启动 Browser 模式...', 'green')}")
        os.chdir(PROJECT_DIR)
        proc = subprocess.Popen(
            [python, "webapp.py"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        PID_FILE.write_text(str(proc.pid))
        print(f"  PID: {proc.pid}")
        print(f"  🌐 http://localhost:2469")
        try:
            for line in proc.stdout:
                sys.stdout.buffer.write(line)
        except KeyboardInterrupt:
            print(f"\n  {c('⏹  收到 Ctrl+C，正在关闭...', 'yellow')}")
            proc.terminate()
            proc.wait()
            PID_FILE.unlink(missing_ok=True)
    
    else:  # background
        print(f"  {c('🚀 启动后台服务...', 'green')}")
        os.chdir(PROJECT_DIR)
        proc = subprocess.Popen(
            [python, "webapp.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        PID_FILE.write_text(str(proc.pid))
        print(f"  PID: {proc.pid}  (pid 写入 {PID_FILE})")
        print(f"  🌐 http://localhost:2469")
        print(f"  {c('停止: pyclaw stop', 'dim')}")

def cmd_stop(args):
    print(logo())
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
        print(f"  {c('✅ 已停止 PyClaw (PID {})'.format(pid), 'green')}")
    else:
        print(f"  {c('ℹ️  PyClaw 未在运行', 'yellow')}")

def cmd_status(args):
    print(logo())
    pid = find_pid()
    running = port_in_use()
    
    if pid:
        print(f"  {c('🟢 运行中', 'green')}")
        print(f"  PID: {pid}")
    else:
        print(f"  {running and c('🟡 端口占用', 'yellow') or c('🔴 未运行', 'red')}")
    
    print(f"  🌐 http://localhost:2469  {'🟢' if running else '🔴'}")
    
    cfg = read_config()
    api_key = cfg.get("API_KEY", "")
    if api_key:
        masked = api_key[:6] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 16 else "****"
        print(f"  🔑 API Key: {masked}")
    else:
        print(f"  {c('  ⚠️  未配置 API Key（运行 pyclaw setup）', 'yellow')}")

def cmd_config(args):
    print(logo())
    cfg = read_config()
    
    if args.kv == "show" or not args.kv:
        print(f"  📄 配置 ({CONFIG_FILE.relative_to(PROJECT_DIR)}):\n")
        if not cfg:
            print(f"    {c('(空)', 'dim')}")
        for k, v in cfg.items():
            if k == "API_KEY" and len(v) > 8:
                v = v[:6] + "*" * (len(v) - 10) + v[-4:]
            print(f"    {c(k, 'cyan')} = {v}")
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
            print(f"  {c(f'✅ {key.upper()} = {val}', 'green')}")
        else:
            print(f"  {c('用法: pyclaw config set KEY=VALUE', 'yellow')}")
    
    elif args.kv == "edit":
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} {CONFIG_FILE}")

    # 兼容 set key=value 语法
    if args.kv and "=" in args.kv:
        key, val = args.kv.split("=", 1)
        cfg[key.upper()] = val
        write_config(cfg)
        print(f"  {c(f'✅ {key.upper()} = {val}', 'green')}")

def cmd_setup(args):
    print(logo())
    cfg = read_config()
    lang = cfg.get("LANGUAGE", "zh-CN")
    
    if lang == "en-US":
        T = lambda zh, en: en
    else:
        T = lambda zh, en: zh
    
    print(f"  {c(T('🧞 PyClaw 配置向导', '🧞 PyClaw Setup Wizard'), 'bold')}")
    print(f"  {c(T('↑↓ 移动 • Enter 确认 • Space 复选', '↑↓ Navigate • Enter Confirm • Space Toggle'), 'dim')}\n")
    
    # 1. API Key
    current = cfg.get("API_KEY", "")
    masked = current[:6] + "****" + current[-4:] if len(current) > 12 else ""
    prompt = f"  {T('🔑 API Key', '🔑 API Key')} [{c(masked, 'dim')}]: " if masked else f"  {T('🔑 API Key', '🔑 API Key')}: "
    val = input(prompt).strip()
    if val:
        cfg["API_KEY"] = val
        print()
    
    # 2. Provider
    provider_list = [("deepseek", "DeepSeek"), ("openai", "OpenAI"), ("custom", T("自定义", "Custom"))]
    provider_default = 0
    for i, (k, _) in enumerate(provider_list):
        if k == cfg.get("PROVIDER", "deepseek"):
            provider_default = i
            break
    print(f"\n  {T('📡 模型提供商 (↑↓ 选择)', '📡 Provider (↑↓ select)')}:")
    idx = arrow_select([n for _, n in provider_list], provider_default)
    cfg["PROVIDER"] = provider_list[idx][0]
    print(f"\r  {c(T('✅ 提供商: ', '✅ Provider: ') + provider_list[idx][1], 'green')}")
    
    # 3. Model
    model_list = ["deepseek-chat", "deepseek-v4-flash", "gpt-4o", "gpt-4o-mini"]
    model_default = 0
    for i, m in enumerate(model_list):
        if m == cfg.get("MODEL", "deepseek-chat"):
            model_default = i
            break
    print(f"\n  {T('🧠 模型 (↑↓ 选择)', '🧠 Model (↑↓ select)')}:")
    idx = arrow_select(model_list, model_default)
    cfg["MODEL"] = model_list[idx]
    print(f"\r  {c(T('✅ 模型: ', '✅ Model: ') + model_list[idx], 'green')}")
    
    # 4. Port
    current_port = cfg.get("PORT", "2469")
    val = input(f"\n  {T('🔌 端口', '🔌 Port')} [{c(current_port, 'dim')}]: ").strip()
    if val:
        cfg["PORT"] = val
    
    # 5. Thinking
    current_thinking = cfg.get("THINKING", "on")
    val = input(f"  {T('🧠 思考模式 (on/off)', '🧠 Thinking (on/off)')} [{c(current_thinking, 'dim')}]: ").strip()
    if val:
        cfg["THINKING"] = val
    
    # 6. Language
    lang_list = ["zh-CN", "en-US"]
    lang_default = 0
    for i, l in enumerate(lang_list):
        if l == cfg.get("LANGUAGE", "zh-CN"):
            lang_default = i
            break
    print(f"\n  {T('🌐 界面语言 (↑↓ 选择)', '🌐 Language (↑↓ select)')}:")
    idx = arrow_select([T("中文", "Chinese") if l == "zh-CN" else "English" for l in lang_list], lang_default)
    cfg["LANGUAGE"] = lang_list[idx]
    print(f"\r  {c(f'✅ ' + T('语言: ', 'Language: ') + lang_list[idx], 'green')}")
    lang = lang_list[idx]
    
    # 7. Endpoint
    current_endpoint = cfg.get("ENDPOINT", "")
    val = input(f"  {T('🔗 Endpoint', '🔗 Endpoint')} [{c(current_endpoint or T('默认', 'default'), 'dim')}]: ").strip()
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
        
        print(f"\n  {T('🧩 Skill (Space=移入/恢复 • Enter=确认)', '🧩 Skills (Space=trash/restore • Enter=confirm)')}:")
        print(f"     {c(T('[名称] = 回收站中', '[name] = in trash'), 'dim')}")
        sel = checkbox_select(all_skill_names, skill_defaults)
        
        for i, name in enumerate(active_skills):
            if i not in sel:
                src = skill_dir / name
                dst = trash_dir / name
                trash_dir.mkdir(exist_ok=True)
                src.rename(dst)
                print(f"  {c(f'{T("🗑️ 移入回收站: ", "🗑️ Trashed: ")}' + name, 'yellow')}")
        
        trashed_count = len(trashed_skills)
        active_count = len(active_skills)
        for j, name in enumerate(trashed_skills):
            if active_count + j in sel:
                src = trash_dir / name
                dst = skill_dir / name
                src.rename(dst)
                print(f"  {c(f'{T("♻️ 已恢复: ", "♻️ Restored: ")}' + name, 'green')}")
        
        print(f"  {c(T('✅ Skill 设置完成', '✅ Skills updated'), 'green')}")
    else:
        print(f"\n  {T('🧩 未发现预装 Skill', '🧩 No skills found')}")
    
    print()
    write_config(cfg)
    print(f"  {c(T('✅ 配置已保存到 API.txt', '✅ Config saved to API.txt'), 'green')}")
    print(f"  {c(T('运行 pyclaw start 来启动 🦞', 'Run pyclaw start to launch 🦞'), 'cyan')}\n")
def cmd_chat(args):
    import asyncio
    from pyclaw.agent import Agent
    from pyclaw.pyclaw_types import Message, MessageRole
    
    message = " ".join(args.message)
    print(f"  You: {message}\n")
    
    async def _chat():
        cfg = read_config()
        api_key = cfg.get("API_KEY", "")
        if not api_key:
            print(f"  {c('⚠️  未配置 API Key', 'yellow')}")
            return
        provider = cfg.get("PROVIDER", "deepseek")
        base_urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "openai": "https://api.openai.com/v1",
        }
        base_url = cfg.get("ENDPOINT") or base_urls.get(provider, "https://api.deepseek.com/v1")
        model = cfg.get("MODEL", "deepseek-chat")
        agent = Agent(api_key=api_key, base_url=base_url, model=model)
        msg = Message(
            id=f"cli_{uuid.uuid4().hex[:8]}",
            content=message,
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="cli",
            session_id="cli",
        )
        async for chunk in agent.stream_chat([msg]):
            if chunk.content:
                print(chunk.content, end="", flush=True)
            if chunk.error:
                print(f"\n  {c('❌ ' + chunk.error, 'red')}")
        print()
    
    asyncio.run(_chat())

def cmd_shell(args):
    import asyncio
    from pyclaw.agent import Agent
    from pyclaw.pyclaw_types import Message, MessageRole
    
    print(logo())
    print(f"  {c('交互模式 — 输入消息，Ctrl+C 退出', 'dim')}\n")
    
    async def _run():
        cfg = read_config()
        api_key = cfg.get("API_KEY", "")
        if not api_key:
            print(f"  {c('⚠️  未配置 API Key，请先运行 pyclaw setup', 'yellow')}")
            return
        provider = cfg.get("PROVIDER", "deepseek")
        base_urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "openai": "https://api.openai.com/v1",
        }
        base_url = cfg.get("ENDPOINT") or base_urls.get(provider, "https://api.deepseek.com/v1")
        model = cfg.get("MODEL", "deepseek-chat")
        agent = Agent(api_key=api_key, base_url=base_url, model=model)
        history: list[Message] = []
        
        while True:
            try:
                msg_text = input(f"  {c('You', 'cyan')} > ")
            except (EOFError, KeyboardInterrupt):
                print(f"\n  {c('👋 再见！', 'green')}")
                break
            
            if not msg_text.strip():
                continue
            if msg_text.lower() in ("/exit", "/quit", "exit", "quit"):
                break
            
            msg = Message(
                id=f"cli_{uuid.uuid4().hex[:8]}",
                content=msg_text,
                sender="user",
                role=MessageRole.USER,
                timestamp=time.time(),
                channel_id="cli",
                session_id="cli",
            )
            history.append(msg)
            
            print(f"  {c('PyClaw', 'green')} > ", end="", flush=True)
            all_content = ""
            async for chunk in agent.stream_chat(history):
                if chunk.content:
                    to_print = chunk.content[len(all_content):]
                    print(to_print, end="", flush=True)
                    all_content = chunk.content
                if chunk.error:
                    print(f"\n  {c('❌ ' + chunk.error, 'red')}")
            print()
            
            # 保存到历史
            history.append(Message(
                id=f"cli_{uuid.uuid4().hex[:8]}",
                content=all_content,
                sender="assistant",
                role=MessageRole.ASSISTANT,
                timestamp=time.time(),
                channel_id="cli",
                session_id="cli",
            ))
    
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print(f"\n  {c('👋 再见！', 'green')}")

# ── 终端交互 ──────────────────────────────────────
# Arrow-key / spacebar input (POSIX only: Linux/macOS)
import termios, tty

def _getch():
    """Read one keypress"""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def arrow_select(options: list, default: int = 0) -> int:
    """Arrow-key single select. Returns index."""
    idx = default
    print()
    while True:
        for i, opt in enumerate(options):
            prefix = c(" ●", "cyan") if i == idx else c(" ○", "dim")
            print(f"\r{prefix} {opt}\x1b[K")
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

def checkbox_select(items: list, defaults: set = set()) -> set:
    """Space to toggle, Enter to confirm. Returns set of selected indices."""
    selected = set(defaults)
    idx = 0
    print()
    while True:
        for i, item in enumerate(items):
            check = c("■", "green") if i in selected else c("□", "dim")
            prefix = c("→", "cyan") if i == idx else "  "
            print(f"\r{prefix} {check} {item}\x1b[K")
        print(f"\r  {c('Space 切换选中 • Enter 确认 • ↑↓ 移动', 'dim')}\x1b[K")
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
    # Clear the hint line
    print(f"\r\x1b[{len(items)+1}B", end="")
    for _ in range(len(items)):
        print(" " * 80)
    print(f"\x1b[{len(items)}A", end="")
    return selected

# ── 入口 ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="pyclaw",
        description="🦞 PyClaw AI 命令行工具",
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
