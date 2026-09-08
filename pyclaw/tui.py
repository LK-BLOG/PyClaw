"""Codex-style terminal UI for PyClaw - connects directly to Gateway."""
import asyncio, json, time, uuid
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings


def run_tui(project_dir, read_config, color):
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from pyclaw.gateway import Gateway
    from pyclaw.skill import skill_manager
    from pyclaw.cli import logo, info_bar

    cfg = read_config(); key = cfg.get("API_KEY", "")
    if not key:
        print("WARNING: 未配置 API Key，请先运行 pyclaw setup"); return
    urls = {"deepseek":"https://api.deepseek.com", "openai":"https://api.openai.com/v1", "opencode-zen":"https://opencode.ai/zen/v1"}
    provider = cfg.get("PROVIDER", "deepseek"); base_url = cfg.get("ENDPOINT") or urls.get(provider, urls["deepseek"])
    model = cfg.get("MODEL", "deepseek-v4-flash"); sessions = project_dir / ".sessions"; sessions.mkdir(exist_ok=True)
    skill_manager.skill_dir = project_dir / "skills"
    import sys
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8", errors="replace")
    console = Console(highlight=False, force_terminal=True, file=sys.stdout)

    def clean(value): return str(value or "").encode("utf-8", "replace").decode("utf-8", "replace")
    def stamp(value):
        try:
            n = float(value or 0); n = n / 1000 if n > 100000000000 else n
            return time.strftime("%H:%M:%S", time.localtime(n))
        except (ValueError, TypeError, OSError, OverflowError):
            return "--:--:--"

    async def app():
        gateway = Gateway(llm_api_key=key, storage_path=str(sessions), base_url=base_url, model=model, language=cfg.get("LANGUAGE", "zh-CN"))
        gateway.agent.thinking = cfg.get("THINKING", "on") == "on"; await gateway.initialize_skills()
        sid = "tui_" + uuid.uuid4().hex[:8]
        # flow: 每条是 (kind, text, stamp)，kind ∈ {user, assistant, tool_call, tool_result}
        flow = []; started = time.time(); stats = {"last_ms": 0, "chars": 0}
        session = PromptSession()

        def load(s):
            out = []
            for m in gateway.session_manager.get_history(s):
                role = getattr(m.role, "value", m.role)
                text = clean(getattr(m, "content", ""))
                ts = stamp(getattr(m, "timestamp", 0))
                tcs = getattr(m, "tool_calls", None) or []
                if role == "user" and text:
                    out.append(("user", text, ts))
                elif role == "assistant":
                    if tcs:
                        for tc in tcs:
                            for info in normalize_toolcall(tc):
                                out.append(("tool_call", info["name"] + "\n" + text_detail(parse_args(info["arguments"])), ts))
                    if text:
                        out.append(("assistant", text, ts))
                elif role == "tool":
                    out.append(("tool_result", text, ts))
            return out

        def normalize_toolcall(tc):
            if isinstance(tc, dict):
                if "function" in tc:
                    fn = tc["function"] or {}
                    name = fn.get("name") or tc.get("name") or "tool"
                    args = fn.get("arguments") or tc.get("arguments") or {}
                else:
                    name = tc.get("name") or "tool"
                    args = tc.get("arguments") or {}
                return [{"name": name, "arguments": args, "id": tc.get("id")}]
            return [{"name": getattr(tc, "name", "tool"), "arguments": getattr(tc, "arguments", {}), "id": getattr(tc, "id", None)}]

        def parse_args(raw):
            if isinstance(raw, dict): return raw
            if isinstance(raw, str):
                try: return json.loads(raw)
                except Exception: return raw
            return raw or {}

        def norm_toolcall(tc):
            if isinstance(tc, dict):
                if "function" in tc:
                    fn = tc["function"] or {}
                    return {"id": tc.get("id"), "name": fn.get("name") or tc.get("name") or "tool", "arguments": fn.get("arguments") or tc.get("arguments") or {}}
                return {"id": tc.get("id"), "name": tc.get("name") or "tool", "arguments": tc.get("arguments") or {}}
            return {"id": getattr(tc, "id", None), "name": getattr(tc, "name", "tool"), "arguments": getattr(tc, "arguments", {})}

        bindings = KeyBindings()
        @bindings.add("c-p")
        def _(event):
            event.app.exit(result="/__palette__")

        async def prompt(msg=" > "):
            return (await asyncio.to_thread(session.prompt, msg, key_bindings=bindings)).strip()

        async def chat(text):
            began = time.perf_counter()
            before = len(gateway.session_manager.get_history(sid))
            import contextlib, io
            with console.status("[cyan]Thinking...[/cyan]"):
                with contextlib.redirect_stdout(io.StringIO()):
                    reply = await gateway.chat_text(text, sid)
            stats["last_ms"] = int((time.perf_counter() - began) * 1000)
            stats["chars"] = len(clean(reply))
            # 提取本轮新增的 tool_call / tool_result，按出现顺序返回
            hist = gateway.session_manager.get_history(sid)[before:]
            tools = []; pending = {}
            for m in hist:
                role = getattr(m.role, "value", m.role)
                tcs = getattr(m, "tool_calls", None) or []
                if role == "assistant" and tcs:
                    for tc in tcs:
                        info = norm_toolcall(tc)
                        pending[info["id"]] = info["name"]
                        tools.append(("tool_call", info["name"], parse_args(info["arguments"])))
                elif role == "tool":
                    tools.append(("tool_result", pending.get(getattr(m, "tool_call_id", None), "tool"), getattr(m, "content", "")))
            return clean(reply or "(no response)"), tools

        def render():
            console.clear(); console.print(logo(), markup=False); console.print(info_bar(cfg))
            st = Table.grid(expand=True); [st.add_column() for _ in range(4)]
            st.add_row(f"[bold]Provider[/bold] {provider}", f"[bold]Model[/bold] {model}", f"[bold]Session[/bold] {sid}", f"[bold]Messages[/bold] {sum(1 for k,_,_ in flow if k in ('user','assistant'))}")
            st.add_row(f"[bold]Workspace[/bold] {project_dir}", f"[bold]Endpoint[/bold] {base_url}", f"[bold]Last[/bold] {stats['last_ms']}ms", f"[bold]Chars[/bold] {stats['chars']}")
            console.print(Panel(st, title="PyClaw  |  Ctrl+P Command Palette  |  Ctrl+C Cancel", border_style="blue"))
            for kind, text, when in flow[-30:]:
                if kind == "user":
                    console.print(Panel(Text(text), title="You  " + when, border_style="green", padding=(0, 1)))
                elif kind == "assistant":
                    console.print(Panel(Markdown(text), title="PyClaw  " + when, border_style="cyan", padding=(0, 1)))
                elif kind == "tool_call":
                    body = Text(clean(text)[:2000] + ("\n... (truncated)" if len(clean(text)) > 2000 else ""))
                    console.print(Panel(body, title="Tool call  " + when, border_style="yellow", padding=(0, 1)))
                elif kind == "tool_result":
                    body = Text(clean(text)[:2000] + ("\n... (truncated)" if len(clean(text)) > 2000 else ""))
                    console.print(Panel(body, title="Tool result  " + when, border_style="yellow", padding=(0, 1)))
            command_bar = Table.grid(expand=True); command_bar.add_column(); command_bar.add_column(justify="right")
            command_bar.add_row("[bold cyan]Commands[/bold cyan]  /help  /new  /sessions  /session  /compact  /clear  /exit", "[bold magenta]Ctrl+P[/bold magenta] Palette  [bold yellow]Ctrl+C[/bold yellow] Cancel")
            console.print(Panel(command_bar, border_style="dim"))

        def text_detail(raw):
            if isinstance(raw, dict):
                import json as _json
                return _json.dumps(raw, ensure_ascii=False, indent=2)
            return str(raw)

        PALETTE = [("/help", "show help"), ("/new", "new session"), ("/sessions", "list sessions"), ("/session <id>", "switch session"), ("/compact", "compact history"), ("/clear", "clear view"), ("/exit", "quit")]

        def show_palette():
            p = Table.grid(padding=(0, 2)); p.add_column(style="bold cyan"); p.add_column(style="dim")
            for cmd, desc in PALETTE: p.add_row(cmd, desc)
            console.print(Panel(p, title="Command Palette  Ctrl+P", border_style="magenta"))

        while True:
            render()
            try: text = await prompt()
            except (EOFError, KeyboardInterrupt): break
            if text == "/__palette__":
                show_palette()
                try: text = await prompt("[bold magenta]Command:[/bold magenta] ")
                except (EOFError, KeyboardInterrupt): break
                if not text: continue
            if not text: continue
            if text in ("/exit", "/quit", "/q"): break
            if text == "/new": sid = "tui_" + uuid.uuid4().hex[:8]; flow = []; continue
            if text == "/clear": flow = []; continue
            if text == "/help": show_palette(); await prompt(); continue
            if text == "/sessions":
                console.print(Panel("\n".join(gateway.session_manager.list_sessions()) or "(empty)", title="Sessions")); await prompt(); continue
            if text.startswith("/session "):
                target = text[9:].strip()
                if gateway.session_manager.get(target): sid = target; flow = load(sid)
                else: console.print("Unknown session: " + target); await prompt()
                continue
            if text in ("/compact", "/c"):
                result = await gateway.compact_session(sid); console.print(Panel(str(result), title="Compact")); await prompt(); continue
            flow.append(("user", clean(text), time.strftime("%H:%M:%S")))
            render()
            try:
                answer, tools = await chat(text)
                for kind, name, detail in tools:
                    if kind == "tool_call":
                        flow.append(("tool_call", name + "\n" + text_detail(detail), time.strftime("%H:%M:%S")))
                    else:
                        flow.append(("tool_result", name + "\n" + clean(detail), time.strftime("%H:%M:%S")))
                flow.append(("assistant", answer, time.strftime("%H:%M:%S")))
            except KeyboardInterrupt:
                console.print("[yellow]Current request cancelled[/yellow]"); continue
    try: asyncio.run(app())
    except KeyboardInterrupt: pass
