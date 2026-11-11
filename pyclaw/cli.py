"""Interactive CLI: slash commands, status line and the y/N approval gate."""

from __future__ import annotations

import sys
import time

from . import context as ctx_mod
from .permissions import MODES, mode_label

MESSAGES = {
    "banner": ("PyClaw {version}  |  模型 {model}  |  档位 {effort}  |  权限 {mode}",
               "PyClaw {version}  |  model {model}  |  effort {effort}  |  approval {mode}"),
    "hint": ("输入消息开始；/help 看命令，exit 或 Ctrl+C 退出。",
             "Type a message; /help for commands, exit or Ctrl+C to quit."),
    "thinking": ("思考中", "thinking"),
    "exec": ("执行", "exec"),
    "stopped": ("已中断", "interrupted"),
    "denied": ("已拒绝", "denied"),
    "unknown": ("未知命令：{name}（/help 看列表）", "unknown command: {name} (/help)"),
    "confirm": ("即将执行：\n  {command}\n原因：{reason}\n放行吗？[y/N] ", 
                "About to run:\n  {command}\nReason: {reason}\nAllow? [y/N] "),
    "saved": ("会话已保存：{sid}", "session saved: {sid}"),
    "new": ("新会话：{sid}", "new session: {sid}"),
    "resumed": ("已恢复：{sid}  {title}", "resumed: {sid}  {title}"),
    "rules": ("长期规则：", "allow rules:"),
    "no_rules": ("(空)", "(none)"),
    "compacting": ("压缩中…", "compacting…"),
    "help": (
        "/model [名字]   切换模型（不带参数列出可用模型）\n"
        "/effort [档位]  思考强度：off minimal low medium high xhigh max ultra\n"
        "/permissions [档] 权限：request 请求批准 / auto 帮我批准 / full 完全访问\n"
        "/compact        立即压缩上下文\n"
        "/new            开新会话\n"
        "/resume         列出并恢复会话\n"
        "/rules          查看/删除长期授权\n"
        "/help           这份帮助",
        "/model [name]   switch model (no argument lists models)\n"
        "/effort [level] off minimal low medium high xhigh max ultra\n"
        "/permissions [mode] request | auto | full\n"
        "/compact        compact now\n"
        "/new            start a new session\n"
        "/resume         list and resume sessions\n"
        "/rules          list or drop standing approvals\n"
        "/help           this help"),
}


def t(lang, key, **kwargs):
    zh, en = MESSAGES[key]
    text = zh if lang == "zh-CN" else en
    return text.format(**kwargs) if kwargs else text


class CLI:
    def __init__(self, config, agent):
        self.config = config
        self.agent = agent
        self.lang = config.get("LANGUAGE", "zh-CN")
        self.turn_tools = 0
        self._in_reasoning = False
        self._streamed = False

    # ---------------------------------------------------------------- output

    def emit(self, event):
        kind = event.get("type")
        if kind == "reasoning":
            if not self._in_reasoning:
                sys.stdout.write("\033[2m  ~ ")
                self._in_reasoning = True
            sys.stdout.write(event["text"].replace("\n", "\n    "))
        elif kind == "delta":
            if self._in_reasoning:
                sys.stdout.write("\033[0m\n")
                self._in_reasoning = False
            self._streamed = True
            sys.stdout.write(event["text"])
            sys.stdout.flush()
        elif kind == "assistant":
            # Safety net: a provider that answered without deltas still gets shown.
            if not self._streamed:
                self._newline()
                print(event.get("text", ""))
            self._streamed = False
        elif kind == "tool_call":
            self._newline()
            self.turn_tools += 1
            print(f"\033[33m{t(self.lang, 'exec')} > {event['command']}\033[0m")
        elif kind == "tool_result":
            preview = event["text"].strip().splitlines()
            head = "\n".join(preview[:12])
            print(f"\033[2m{head}\033[0m" + ("\n\033[2m  …\033[0m" if len(preview) > 12 else ""))
        elif kind == "compact":
            self._newline()
            print(f"\033[36m[{t(self.lang, 'compacting')} "
                  f"{_tokens(event['before'])} -> {_tokens(event['after'])}]\033[0m")
        elif kind == "notice":
            self._newline()
            print(f"\033[33m! {event['text']}\033[0m")
        elif kind == "error":
            self._newline()
            print(f"\033[31m! {event['text']}\033[0m")
        elif kind == "usage":
            self._newline()
            self.status(event)
            self._streamed = False

    def _newline(self):
        if self._in_reasoning:
            sys.stdout.write("\033[0m\n")
            self._in_reasoning = False
        sys.stdout.write("\n")

    def status(self, event):
        usage = event.get("usage") or {}
        data = event.get("breakdown") or {}
        cache = ""
        prompt = usage.get("prompt_tokens") or 0
        if prompt and usage.get("cache_hit_tokens"):
            cache = f" | cache {100 * usage['cache_hit_tokens'] / prompt:.1f}%"
        print(f"\033[2mctx {_tokens(data.get('used', 0))}/{_tokens(data.get('window', 0))} "
              f"({data.get('percent', 0)}%){cache} | effort {self.agent.effort()} | "
              f"tools {self.turn_tools}\033[0m")
        self.turn_tools = 0

    # ---------------------------------------------------------------- approvals

    def confirm(self, command, verdict):
        rule = verdict.rule or {}
        reason = rule.get("justification") or verdict.reason
        try:
            answer = input(t(self.lang, "confirm", command=command, reason=reason)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False, None
        if answer in ("y", "yes", "yy"):
            # "yy" means: allow now and remember the rule for good.
            scope = "persistent" if answer.startswith("yy") else "session"
            return True, scope
        return False, None

    # ---------------------------------------------------------------- commands

    def handle(self, line):
        """Returns True when the line was a slash command."""
        if not line.startswith("/"):
            return False
        parts = line[1:].split()
        name = (parts[0] if parts else "").lower()
        arg = parts[1] if len(parts) > 1 else ""
        agent = self.agent
        if name == "help":
            print(t(self.lang, "help"))
        elif name == "model":
            if not arg:
                models = agent.provider.list_models()
                for model in models[:60]:
                    mark = "*" if model == agent.provider.model else " "
                    print(f" {mark} {model}")
                if not models:
                    print("  (endpoint did not return a model list)")
                return True
            agent.session.set(model=arg)
            agent.provider.reload(_patched(self.config, MODEL=arg))
            try:
                self.config.update({"MODEL": arg})
            except (ValueError, OSError):
                pass  # a read-only config must not break the switch
            print(f"model -> {arg}  (context {_tokens(agent.provider.context_window)})")
        elif name == "effort":
            tiers, mapping = agent.provider.tiers()
            if not arg:
                current = agent.effort()
                for tier in ["off"] + tiers:
                    print(f"  {'*' if tier == current else ' '} {tier}"
                          + (f"  -> {mapping[tier]}" if tier in mapping else ""))
                if not tiers:
                    print("  (this provider exposes no effort levels)")
                return True
            if arg != "off" and arg not in tiers:
                print(f"! {arg} is not supported by {agent.provider.model}")
                return True
            agent.session.set(effort=arg)
            print(f"effort -> {arg}" + (f"  (maps to {mapping[arg]})" if arg in mapping else ""))
        elif name == "permissions":
            if arg not in MODES:
                for mode in MODES:
                    info = mode_label(mode, self.lang)
                    print(f"  {'*' if mode == agent.approval_mode() else ' '} {mode:8} {info['label']} - {info['help']}")
                return True
            agent.session.set(approval=arg)
            print(f"approval -> {arg}")
        elif name == "compact":
            messages = agent.base_messages()
            agent.compact(messages, agent.tool_schemas(), self.emit, force=True)
        elif name == "new":
            sid = agent.store.create(model=agent.provider.model, effort=agent.effort(),
                                     approval=agent.approval_mode())
            agent.session = agent.store.get(sid.id)
            print(t(self.lang, "new", sid=sid.id))
        elif name == "resume":
            rows = agent.store.list(include_archived=True)
            for index, row in enumerate(rows[:20]):
                print(f"  {index:2}  {row.get('title') or '(untitled)':24} {row.get('updated', '')}  {row['id']}")
            try:
                pick = input("resume # (blank to cancel): ").strip()
            except (EOFError, KeyboardInterrupt):
                return True
            if pick.isdigit() and int(pick) < len(rows):
                target = agent.store.get(rows[int(pick)]["id"])
                agent.session = target
                # The restored session may run a different model/effort than the
                # provider currently holds.
                agent.sync_session_route()
                print(t(self.lang, "resumed", sid=target.id, title=target.title))
        elif name == "rules":
            rows = agent.policy.rules
            if not rows:
                print(t(self.lang, "no_rules"))
                return True
            for index, rule in enumerate(rows):
                print(f"  {index:2}  {' '.join(map(str, rule.get('pattern', [])))}"
                      f"  [{rule.get('scope')}]  {rule.get('created', '')}")
            try:
                pick = input("drop # (blank to cancel): ").strip()
            except (EOFError, KeyboardInterrupt):
                return True
            if pick.isdigit() and int(pick) < len(rows):
                # The list shown above is the combined one, so the index has to be
                # resolved against the same order.
                dropped = agent.policy.revoke_combined(int(pick))
                if dropped and dropped.get("scope") == "persistent":
                    self.config.update({"ALLOW_RULES": agent.policy.persistent})
        else:
            print(t(self.lang, "unknown", name=name))
        return True

    # ---------------------------------------------------------------- loop

    def run(self):
        agent = self.agent
        banner = t(self.lang, "banner", version=_version(), model=agent.provider.model,
                   effort=agent.effort(), mode=agent.approval_mode())
        print(f"\033[1m{banner}\033[0m")
        print(f"  {t(self.lang, 'hint')}")
        print(f"  session {agent.session.id}  shell {agent.shell.kind}  skills "
              f"[{', '.join(agent.skill_names()) or 'none'}]")
        while True:
            try:
                line = input("\n\033[36m> \033[0m")
            except (EOFError, KeyboardInterrupt):
                print("\n" + t(self.lang, "saved", sid=agent.session.id))
                return 0
            line = line.strip()
            if not line:
                continue
            if line in ("exit", "quit"):
                print(t(self.lang, "saved", sid=agent.session.id))
                return 0
            if self.handle(line):
                continue
            try:
                agent.run_turn(line, self.emit, self.confirm)
                if not agent.session.title:
                    agent.make_title()
            except KeyboardInterrupt:
                print(f"\n\033[33m{t(self.lang, 'stopped')}\033[0m")


def _patched(config, **overrides):
    """A view of the config with a couple of values swapped, for hot model swaps."""
    class View(dict):
        def get(self, key, default=None):
            return overrides.get(key, config.get(key, default))

        def __getitem__(self, key):
            if key in overrides:
                return overrides[key]
            return config[key]

    view = View()
    view.get = lambda key, default=None: overrides.get(key, config.get(key, default))
    return view


def _tokens(value):
    value = int(value or 0)
    if value >= 1000000:
        return f"{value / 1000000:.1f}M"
    if value >= 1000:
        return f"{value // 1000}K"
    return str(value)


def _version():
    from . import VERSION

    return VERSION
