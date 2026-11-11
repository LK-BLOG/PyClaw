"""Terminal UI for PyClaw.

Panels follow the PyClaw layout (logo, info table, one panel per flow item, command
bar). The effort control is a port of Claude Code's `/effort` slider: a track with a
`▲` caret, Faster/Smarter ends, a divider before the top tier, and
`←/→ to adjust · Enter to confirm · Esc to cancel`.
"""

from __future__ import annotations

import sys
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .cli import CLI, _tokens

# Values the API accepts, in Claude Code's display order (off is our own extra).
EFFORT_LEVELS = ("off", "low", "medium", "high", "xhigh", "max", "ultra")
EFFORT_LABELS = {"off": "off", "low": "low", "medium": "medium", "high": "high",
                 "xhigh": "xhigh", "max": "max", "ultra": "ultra"}


def effort_level_to_symbol(level):
    """Claude Code draws one glyph per level; the top tier gets the star."""
    return {"off": "○", "low": "○", "medium": "◐", "high": "●",
            "xhigh": "●", "max": "◉", "ultra": "✦"}.get(level, "○")


def slider_text(levels, index, width=84):
    """Build the track: caret row, label row, and the tier divider."""
    span = max(1, width - 2)
    step = span / max(1, len(levels) - 1)
    caret = [" "] * (span + 1)
    caret[min(span, round(index * step))] = "▲"
    track = ["─"] * (span + 1)
    marks = []
    for i, level in enumerate(levels):
        pos = min(span, round(i * step))
        track[pos] = "┊" if level == "ultra" else "┼"
        marks.append((pos, level, i == index))
    return " " + "".join(caret), " " + "".join(track), marks


class TUI(CLI):
    """Rich panel UI over the same Agent the plain CLI drives."""

    def __init__(self, config, agent):
        super().__init__(config, agent)
        self.console = Console(highlight=False, soft_wrap=False)
        self.flow: list[tuple[str, str, str]] = []
        self.session = PromptSession()
        self.last = {"ms": 0, "chars": 0}
        self._status = None

    # ---------------------------------------------------------------- chrome

    def logo(self):
        from . import VERSION

        return Text.from_markup("[bold yellow]◆[/bold yellow] [bold]PyClaw[/bold] "
                                f"[dim]{VERSION}[/dim]")

    def info_panel(self):
        table = Table.grid(expand=True, padding=(0, 2))
        for _ in range(4):
            table.add_column()
        agent = self.agent
        table.add_row(f"[bold]Model[/bold] {agent.provider.model}",
                      f"[bold]Effort[/bold] {effort_level_to_symbol(agent.effort())} {agent.effort()}",
                      f"[bold]Session[/bold] {agent.session.id}",
                      f"[bold]Approval[/bold] {agent.approval_mode()}")
        table.add_row(f"[bold]Shell[/bold] {agent.shell.kind}",
                      f"[bold]Workspace[/bold] {agent.shell.display_cwd}",
                      f"[bold]Last[/bold] {self.last['ms']}ms",
                      f"[bold]Chars[/bold] {self.last['chars']}")
        return Panel(table, title="PyClaw  |  /help  /effort  Ctrl+C cancel",
                     border_style="blue")

    def render(self):
        self.console.clear()
        self.console.print(self.logo(), markup=False)
        self.console.print(self.info_panel())
        for kind, text, when in self.flow[-24:]:
            if kind == "user":
                self.console.print(Panel(Text(text), title="You  " + when,
                                         border_style="green", padding=(0, 1)))
            elif kind == "assistant":
                self.console.print(Panel(Markdown(text or ""), title="PyClaw  " + when,
                                         border_style="cyan", padding=(0, 1)))
            elif kind == "tool":
                body = Text(text[:2000] + ("\n... (truncated)" if len(text) > 2000 else ""))
                self.console.print(Panel(body, title="Tool  " + when,
                                         border_style="yellow", padding=(0, 1)))
            else:
                self.console.print(Panel(Text(text), title=kind + "  " + when, border_style="dim"))
        bar = Table.grid(expand=True)
        bar.add_column()
        bar.add_column(justify="right")
        bar.add_row("[bold cyan]/help  /model  /effort  /permissions  /compact[/bold cyan]"
                    "[dim]  ·  /context /cost /status /new /resume /rules /clear[/dim]",
                    "[bold yellow]Ctrl+C[/bold yellow] cancel")
        self.console.print(Panel(bar, border_style="dim"))

    # ---------------------------------------------------------------- effort

    def _track_toolbar(self, levels, labels, state, width, note_lines):
        def toolbar():
            caret, track, marks = slider_text(levels, state["i"], width)
            pad = " " * 8
            lines = [f"{pad}{'Faster':<{width // 2}}{'Smarter':>{width // 2}}",
                     f"{pad}{caret}", f"{pad}{track}"]
            row = [" "] * (width + 1)
            for pos, level, active in marks:
                label = labels.get(level, level)
                start = max(0, min(len(row) - len(label), pos - len(label) // 2))
                for k, ch in enumerate(label):
                    row[start + k] = ch
            lines.append(pad + "".join(row).rstrip())
            lines.extend(note_lines)
            lines.append(f"{pad}[dim]←/→ to adjust · Enter to confirm · Esc to cancel[/dim]")
            return ANSI("\n".join(line if line.startswith(pad + "[dim]") else
                                  "\x1b[2m" + line + "\x1b[0m" for line in lines))
        return toolbar

    def _picker(self, levels, labels, current, title, note_lines, prompt_label):
        """Shared arrow-key picker: same bindings for effort and model."""
        if not levels:
            return None
        state = {"i": levels.index(current) if current in levels else 0}
        width = min(self.console.width - 8, 96)
        bindings = KeyBindings()

        @bindings.add("left")
        def _left(event):
            state["i"] = max(0, state["i"] - 1)
            event.app.invalidate()

        @bindings.add("right")
        def _right(event):
            state["i"] = min(len(levels) - 1, state["i"] + 1)
            event.app.invalidate()

        @bindings.add("enter", eager=True)
        def _enter(event):
            event.app.exit(result=levels[state["i"]])

        @bindings.add("escape", eager=True)
        def _cancel(event):
            event.app.exit(result=None)

        self.console.print(Panel(Text(title), border_style="blue"))
        picker = PromptSession(key_bindings=bindings,
                               bottom_toolbar=self._track_toolbar(levels, labels, state, width, note_lines))
        try:
            return picker.prompt(prompt_label)
        except (EOFError, KeyboardInterrupt):
            return None

    def effort_slider(self):
        """Claude Code's `/effort` panel: arrow keys over the level track."""
        levels = [lv for lv in EFFORT_LEVELS if self.agent.provider.supports_effort(lv)]
        if not levels:
            self.console.print("[yellow]This provider exposes no effort levels.[/yellow]")
            return None
        mapping = self.agent.provider.tiers()[1]
        notes = []
        remap = [f"{lv} → {mapping[lv]}" for lv in levels if lv in mapping and mapping[lv] != lv]
        if remap:
            notes.append(f"{' ' * 8}[dim]{' · '.join(remap)}[/dim]")
        return self._picker(levels, EFFORT_LABELS, self.agent.effort(), "Effort", notes, "Effort  ")

    def model_picker(self):
        """Model list as the same picker, fed by the provider's /models endpoint."""
        models = self.agent.provider.list_models()
        if not models:
            self.console.print("[yellow]No model list; check ENDPOINT and API key.[/yellow]")
            return None
        models = sorted(dict.fromkeys(models))
        labels = {m: m for m in models}
        notes = [f"{' ' * 8}[dim]{len(models)} models · ←/→ to switch[/dim]"]
        return self._picker(models, labels, self.agent.provider.model, "Model", notes, "Model  ")

    # ---------------------------------------------------------------- commands

    def handle(self, line):
        if not line.startswith("/"):
            return False
        name, _, arg = line[1:].partition(" ")
        agent = self.agent
        if name == "effort":
            chosen = self.effort_slider()
            if chosen:
                agent.session.set(effort=chosen)
                mapping = agent.provider.tiers()[1]
                note = f" (→ {mapping[chosen]})" if chosen in mapping and mapping[chosen] != chosen else ""
                self.flow.append(("notice", f"effort set to {chosen}{note}", _ts()))
            return True
        if name == "model":
            if arg.strip():
                agent.session.set(model=arg.strip())
                agent.sync_session_route()
                self.flow.append(("notice", f"model set to {arg.strip()}", _ts()))
                return True
            chosen = self.model_picker()
            if chosen:
                agent.session.set(model=chosen)
                agent.sync_session_route()
                self.flow.append(("notice", f"model set to {chosen} · window "
                                            f"{_tokens(agent.provider.context_window)}", _ts()))
            return True
        if name == "context":
            data = agent.last_messages
            from . import context as ctx_mod
            info = ctx_mod.breakdown(data, agent.tool_schemas(), agent.system_prompt(),
                                     agent.last_usage.get("prompt_tokens", 0),
                                     agent.provider.context_window)
            rows = "\n".join(f"{k:>10}: {_tokens(v)}" for k, v in info.items() if k in
                             ("system", "tools", "user", "assistant", "tool", "used", "free", "window"))
            self.flow.append(("context", rows + f"\n{'':>10}: {info['percent']}%", _ts()))
            return True
        if name == "cost":
            usage = agent.last_usage or {}
            cached = usage.get("cache_hit_tokens") or 0
            prompt = usage.get("prompt_tokens") or 0
            pct = f"{100 * cached / prompt:.1f}%" if prompt else "n/a"
            self.flow.append(("cost", f"prompt {prompt} · completion {usage.get('completion_tokens', 0)}\n"
                                      f"cache hit {cached} ({pct})", _ts()))
            return True
        if name == "status":
            self.flow.append(("status", f"model {agent.provider.model} · window {_tokens(agent.provider.context_window)}\n"
                                        f"shell {agent.shell.kind} · plugins {len(agent.plugins)}"
                                        f" · mcp {len(agent.mcp.servers) if agent.mcp else 0}", _ts()))
            return True
        if name == "clear":
            self.flow.clear()
            return True
        if name == "compact":
            # The plain CLI prints the compaction notice to stdout; here it has to
            # land in the panel flow instead.
            messages = agent.base_messages()
            agent.compact(messages, agent.tool_schemas(), self._collect_events, force=True)
            return True
        return super().handle(line)

    def help_text(self):
        return ("Lite ports the commands it can actually back:\n"
                "  /help /model /effort /permissions /compact /context /cost /status\n"
                "  /new /resume /rules /clear /exit\n"
                "Claude Code ships ~84 commands; the rest need services Lite does not have.")

    # ---------------------------------------------------------------- loop

    def run(self):
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return super().run()
        self.console.print(Panel(Text(self.help_text()), title="PyClaw", border_style="blue"))
        while True:
            self.render()
            try:
                line = self.session.prompt("❯ ").strip()
            except (EOFError, KeyboardInterrupt):
                return 0
            if not line:
                continue
            if line in ("exit", "quit", "/exit", "/quit"):
                return 0
            if line == "/help":
                self.flow.append(("help", self.help_text(), _ts()))
                continue
            if line.startswith("/") and self.handle(line):
                continue
            self.flow.append(("user", line, _ts()))
            self.render()
            started = time.perf_counter()
            try:
                with self.console.status("[cyan]Thinking...[/cyan]"):
                    answer = self.agent.run_turn(line, self._collect_events, self.confirm)
                self.last["ms"] = int((time.perf_counter() - started) * 1000)
                self.last["chars"] = len(answer or "")
                if not self.agent.session.title:
                    self.agent.make_title()
            except KeyboardInterrupt:
                self.flow.append(("cancelled", "request cancelled", _ts()))
            except Exception as exc:  # noqa: BLE001
                self.flow.append(("error", str(exc), _ts()))
        return 0

    def _collect_events(self, event):
        kind = event.get("type")
        if kind == "assistant":
            self.flow.append(("assistant", event.get("text", ""), _ts()))
        elif kind == "tool_call":
            self.flow.append(("tool", "$ " + event.get("command", ""), _ts()))
        elif kind == "tool_result":
            self.flow.append(("tool", event.get("text", ""), _ts()))
        elif kind == "notice":
            self.flow.append(("notice", event["text"], _ts()))
        elif kind == "error":
            self.flow.append(("error", event.get("text", ""), _ts()))
        elif kind == "compact":
            self.flow.append(("notice", f"compacted {_tokens(event['before'])} → {_tokens(event['after'])}", _ts()))


def _ts():
    return time.strftime("%H:%M:%S")
