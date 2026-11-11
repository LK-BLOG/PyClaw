"""The agent loop: stable prompt, tail snapshots, one tool, compaction."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time

from . import context as ctx_mod
from . import providers
from .permissions import Policy, derive_rule

MAX_STEPS = 1000
CHECKPOINT_PREAMBLE = (
    "This is an automatically generated checkpoint condensing an earlier span of the conversation "
    "to free up context. Treat the captured context as established background and build on it "
    "without restating it. Continue the task directly from the messages that follow."
)
COMPACT_INSTRUCTION = """You are now acting as a compaction engine for this AI coding assistant. Condense the conversation ABOVE into a structured checkpoint that lets another model resume the work with no loss of essential context.

Output EXACTLY the Markdown structure below: keep every section, in order. Use terse bullets, not prose paragraphs. Write "(none)" for an empty section - never drop a section.

## Primary Request and Intent
## Key Technical Concepts
## Files and Code
## Errors and Fixes
## Pending Jobs
## Current Work
## Next Step
## Critical Context

Rules:
- Write concise English engineering prose. Preserve exact file paths, commands, error strings, identifiers, numeric values and syntax fragments.
- Capture user feedback and explicit instructions faithfully, especially corrections.
- Do NOT mention this summarization request or that the context was compacted.
- Output only the checkpoint text: do not call any tool or take any other action."""
FALLBACK_CHECKPOINT = ("Earlier conversation history was dropped to free context. "
                       "Continue from the messages below; re-read files if you need details.")


def exec_schema():
    return {"type": "function", "function": {
        "name": "exec",
        "description": "Run one shell command and return its output. This is the only built-in tool; "
                       "everything else is done through it.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to run, in the platform's native syntax."},
            "requires_confirmation": {"type": "boolean", "description":
                "Set true when the command is destructive or irreversible and was not explicitly "
                "authorized in this conversation."},
        }, "required": ["command"]},
    }}


class Agent:
    def __init__(self, config, store, session, provider, shell, hooks=None, mcp=None, plugins=None, root=None):
        self.config = config
        self.store = store
        self.session = session
        self.provider = provider
        self.shell = shell
        self.hooks = hooks
        self.mcp = mcp
        self.plugins = plugins or []
        self.root = pathlib.Path(root or pathlib.Path(ctx_mod.__file__).resolve().parent.parent)
        self.spiller = ctx_mod.Spiller(
            self.root / "history" / "tool",
            int(config.get("TOOL_OUTPUT_MAX_LINES", 500)),
            int(config.get("TOOL_OUTPUT_MAX_BYTES", 65536)),
        )
        self.policy = Policy(config.get("ALLOW_RULES"), config.get("BLOCKED_EXTRA"))
        self.last_usage = {}
        self.last_messages = []
        self._snapshot_hash = {}

    def sync_session_route(self):
        model = self.session.meta.get("model") or self.config.get("MODEL", "")
        if model and model != self.provider.model:
            self.provider.model = model
            self.provider.context_window = providers.context_window(
                model, self.provider.thinking_mode,
                int(self.config.get("CONTEXT_WINDOW", 0)), self.provider.provider_id)

    # ---------------------------------------------------------------- prompt

    def skill_names(self):
        names = []
        for plugin in self.plugins:
            if plugin.enabled:
                names.extend(skill["name"] for skill in plugin.skills)
        skills_dir = self.root / "skills"
        if skills_dir.exists():
            for entry in sorted(skills_dir.iterdir()):
                if entry.suffix == ".py":
                    names.append(entry.stem)
                elif entry.is_dir() and (entry / "SKILL.md").exists():
                    names.append(entry.name)
        return names

    def system_prompt(self):
        skills = ", ".join(self.skill_names()) or "none"
        names = [str(((item or {}).get("function") or {}).get("name") or "") for item in (self.tool_schemas() or [])]
        tools = ", ".join([n for n in names if n]) or "exec"
        me = str(self.config.get("AGENT_NAME", "PyClaw") or "PyClaw")
        return (
            f"You are {me} on {self.shell.kind}. You act through tools: {tools}. "
            f"exec runs shell commands; everything else is a shortcut over it.\n"
            f"cwd is the project root: {self.shell.display_cwd}\n"
            f"{self.shell.hint}\n\n"
            "Rules:\n"
            "- Don't guess. Read the file, look at the output, then act.\n"
            "- After changing anything, run the thing that proves it works before saying done.\n"
            "- Never re-run a command that already failed the same way.\n"
            "- Destructive or irreversible commands: ask first unless already authorized.\n"
            "- Reply short: what you did, what you verified, what is still uncertain.\n\n"
            f"Skills (reusable scripts, call them via exec): {skills}\n"
            "memory/ is long-term storage; write durable facts there.\n\n"
            "## IUI cards (the web UI renders these)\n"
            "When the answer is structured (comparisons, status, steps, choices), append ONE fenced block:\n"
            "```iui\n{\"type\":\"card\",\"title\":\"...\",\"body\":\"...\","
            "\"stats\":[{\"label\":\"x\",\"value\":\"1\"}],"
            "\"actions\":[{\"label\":\"详情\",\"send\":\"展开细节\"}]}\n```\n"
            "Allowed types: card, list, table, buttons, form, chart, callout, progress, carousel, image.\n"
            "Fields: card(title,subtitle,body,icon,stats,actions) · list(items[{title,subtitle,value,icon,action}]) · "
            "table(columns,rows) · buttons(actions) · form(title,fields[{name,label,type,placeholder,options}],submitLabel,sendTemplate) · "
            "chart(bars[{label,value}]) · callout(tone: info|ok|warn|err,title,body) · progress(label,value) · image(src,caption).\n"
            "Action keys: send (send that text back as a user message), href (open link), copy (copy text).\n"
            "Rules: the block must be valid JSON (double quotes), no markdown inside JSON strings, "
            "at most one card block per answer, and keep the prose answer above it."
        )

    def memory_text(self):
        mem = self.root / "memory"
        if not mem.exists():
            return ""
        blocks = []
        for path in sorted(mem.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".txt", ".json", ".jsonl"):
                body = path.read_text(encoding="utf-8", errors="replace").strip()
                if body:
                    blocks.append(f"== {path.relative_to(mem).as_posix()} ==\n{body}")
        return "\n\n".join(blocks)

    def ensure_snapshot(self, kind, text):
        """Volatile context lives in the tail, so the cacheable prefix never changes."""
        text = (text or "").strip()
        if not text:
            return False
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if self._snapshot_hash.get(kind) == digest:
            return False
        self._snapshot_hash[kind] = digest
        labels = {"memory": "Memory", "policy": "Runtime policy", "hook": "Injected context"}
        header = labels.get(kind, kind)
        self.session.append({"type": "snapshot", "kind": kind, "hash": digest,
                             "content": f"<{kind}-snapshot>\n## {header}\n{text}\n</{kind}-snapshot>"})
        return True

    def policy_snapshot(self):
        mode = self.session.meta.get("approval") or self.config.get("APPROVAL_MODE", "auto")
        effort = self.session.meta.get("effort") or self.config.get("REASONING_EFFORT", "high")
        lines = [f"- Approval mode: {mode}", f"- Reasoning effort: {effort}",
                 f"- Shell: {self.shell.kind}", f"- Model: {self.provider.model}"]
        for rule in self.policy.rules:
            if rule.get("decision") == "allow":
                lines.append(f"- Pre-approved prefix: {' '.join(map(str, rule.get('pattern', [])))}")
        return "\n".join(lines)

    def base_messages(self):
        self.ensure_snapshot("memory", self.memory_text())
        self.ensure_snapshot("policy", self.policy_snapshot())
        return [{"role": "system", "content": self.system_prompt()}] + self.session.messages()

    # ---------------------------------------------------------------- tools

    def tool_schemas(self):
        schemas = [exec_schema()]
        if self.mcp:
            schemas.extend(self.mcp.tool_schemas())
        for plugin in self.plugins:
            if plugin.enabled:
                schemas.extend({k: v for k, v in tool.items() if k != "_handler"} for tool in plugin.tools)
        return schemas

    def _handler_for(self, name):
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            for tool in plugin.tools:
                if tool["function"]["name"] == name:
                    return tool.get("_handler")
        return None

    def execute(self, name, arguments, require_confirm=None, emit=None):
        """Run one tool call under the shared permission gate."""
        emit = emit or (lambda event: None)
        self.sync_session_route()
        if name == "exec":
            command = (arguments or {}).get("command", "")
            flagged = bool((arguments or {}).get("requires_confirmation"))
            verdict = self.policy.evaluate(command, flagged, self.approval_mode())
            if verdict.decision == "forbidden":
                return f"[refused] blocked by policy: {command}"
            if verdict.decision == "prompt":
                if self.hooks:
                    self.hooks.run("PermissionRequest", {"command": command, "reason": verdict.reason},
                                   cwd=self.root, session_id=self.session.id)
                allowed, scope = (require_confirm or (lambda *_: (False, None)))(command, verdict)
                if not allowed:
                    return f"[denied] the user did not approve: {command}"
                if scope in ("session", "persistent"):
                    rule = derive_rule(command, scope=scope,
                                       justification=f"approved from: {command[:80]}")
                    self.policy.grant(rule)
                    if scope == "persistent":
                        self.config.update({"ALLOW_RULES": self.policy.persistent})
                    self.session.append({"type": "approval", "command": command, "decision": "allow",
                                         "scope": scope, "rule": rule})
                    self._snapshot_hash.pop("policy", None)
            pre = self.hooks.run("PreToolUse", {"tool_name": "exec", "command": command},
                                 cwd=self.root, session_id=self.session.id) if self.hooks else None
            if pre and pre.blocked:
                return f"[refused] blocked by hook: {pre.reason}"
            code, output, seconds = ctx_mod.run_command(self.shell, command, self.root)
            result = ctx_mod.format_tool_result(command, code, output, seconds, self.shell.display_cwd,
                                                self.spiller, self.session.id, self.root)
            if self.hooks:
                post = self.hooks.run("PostToolUse", {"tool_name": "exec", "command": command,
                                                      "exit_code": code, "output": result[:2000]},
                                      cwd=self.root, session_id=self.session.id)
                if post.contexts:
                    self.ensure_snapshot("hook", "\n".join(post.contexts))
            return result
        handler = self._handler_for(name)
        if handler is not None:
            try:
                return str(handler(arguments or {}, {"config": self.config, "session": self.session,
                                                      "root": self.root, "agent": self}))
            except Exception as exc:  # noqa: BLE001 - surface plugin errors to the model
                return f"[tool error] {name}: {exc}"
        if self.mcp and name.startswith("mcp__"):
            return self.mcp.call(name, arguments or {})
        return f"[error] unknown tool: {name}"

    def approval_mode(self):
        return self.session.meta.get("approval") or self.config.get("APPROVAL_MODE", "auto")

    def effort(self):
        return self.session.meta.get("effort") or self.config.get("REASONING_EFFORT", "high")

    # ---------------------------------------------------------------- compaction

    def pressure(self, messages, tools):
        if self.last_usage.get("prompt_tokens"):
            return self.last_usage["prompt_tokens"]
        return (ctx_mod.estimate_messages(messages) + ctx_mod.estimate_tools(tools)
                + ctx_mod.estimate_tokens(self.system_prompt()))

    def needs_compact(self, messages, tools):
        window = self.provider.context_window
        threshold = float(self.config.get("COMPACT_THRESHOLD", 0.8)) * window
        return window > 0 and self.pressure(messages, tools) >= threshold

    def compact(self, messages, tools, emit, force=False):
        if self.hooks:
            self.hooks.run("PreCompact", {"tokens": self.pressure(messages, tools), "forced": bool(force)},
                           cwd=self.root, session_id=self.session.id)
        window = self.provider.context_window
        retain = float(self.config.get("COMPACT_RETAIN_RATIO", 0.16)) * window
        tail, used = [], 0
        for message in reversed(messages[1:]):
            size = ctx_mod.estimate_messages([message])
            if tail and used + size > retain:
                break
            tail.insert(0, message)
            used += size
        cut = len(messages) - len(tail)
        middle = messages[1:cut]
        before = self.pressure(messages, tools)
        summary = self._summarize(messages) if middle else ""
        if not summary:
            checkpoint = FALLBACK_CHECKPOINT
        else:
            checkpoint = f"{CHECKPOINT_PREAMBLE}\n\n<compacted-summary>\n{summary}\n</compacted-summary>"
        self.session.append({"type": "compact", "checkpoint": checkpoint, "from": len(middle),
                             "tokens_before": before, "forced": bool(force)})
        rebuilt = [messages[0], {"role": "user", "content": checkpoint}] + tail
        self.last_usage = {}
        emit({"type": "compact", "before": before, "after": ctx_mod.estimate_messages(rebuilt)})
        if self.hooks:
            post = self.hooks.run("PostCompact", {"tokens_before": before,
                                                  "tokens_after": ctx_mod.estimate_messages(rebuilt)},
                                  cwd=self.root, session_id=self.session.id)
            if post.contexts:
                self.ensure_snapshot("hook", "\n".join(post.contexts))
        return rebuilt

    def _summarize(self, messages):
        try:
            result = self.provider.chat_with_retry(
                list(messages) + [{"role": "user", "content": COMPACT_INSTRUCTION}],
                tools=None, effort=self.effort(), attempts=2)
            return (result.get("content") or "").strip()
        except Exception:  # noqa: BLE001 - fall back to dropping history
            return ""

    # ---------------------------------------------------------------- turn

    def run_turn(self, user_text, emit, require_confirm=None, signal=None, content_blocks=None):
        emit = emit or (lambda event: None)
        self.sync_session_route()
        self.session.append({"type": "user", "content": user_text})
        if self.hooks:
            start = self.hooks.run("UserPromptSubmit", {"prompt": user_text},
                                   cwd=self.root, session_id=self.session.id)
            if start.contexts:
                self.ensure_snapshot("hook", "\n".join(start.contexts))
        messages = self.base_messages()
        if content_blocks:
            messages[-1] = {"role": "user", "content": content_blocks}
        tools = self.tool_schemas()
        final_text, seen = "", set()
        max_steps = int(self.config.get("MAX_AGENT_STEPS", MAX_STEPS) or MAX_STEPS)
        for _ in range(max_steps):
            if signal is not None and signal.is_set():
                if self.hooks:
                    self.hooks.run("Interrupt", {"reason": "cancelled by the user"},
                                   cwd=self.root, session_id=self.session.id)
                break
            try:
                if self.needs_compact(messages, tools):
                    messages = self.compact(messages, tools, emit)
                result = self.provider.chat_with_retry(
                    messages, tools, self.effort(),
                    on_delta=lambda kind, text: emit({"type": kind, "text": text}), signal=signal)
            except providers.ProviderError as exc:
                if exc.overflow:
                    messages = self.compact(messages, tools, emit, force=True)
                    continue
                if exc.unsupported_effort:
                    emit({"type": "notice", "text": f"reasoning effort '{self.effort()}' rejected; "
                                                    f"falling back to 'high'"})
                    self.session.set(effort="high")
                    continue
                emit({"type": "error", "text": providers.response_error_hint(exc)})
                return
            self.last_usage = result.get("usage") or {}
            calls = result.get("tool_calls") or []
            text = (result.get("content") or "").strip()
            if text:
                final_text = text
            if not calls:
                if text:
                    self.session.append({"type": "assistant", "content": text,
                                         "reasoning": result.get("reasoning") or ""})
                    emit({"type": "assistant", "text": text})
                break
            assistant_message = {"role": "assistant", "content": result.get("content") or ""}
            if result.get("reasoning"):
                assistant_message["reasoning_content"] = result["reasoning"]
            assistant_message["tool_calls"] = [
                {"id": call.get("id") or f"call_{index}", "type": "function",
                 "function": {"name": call.get("name") or "exec", "arguments": call.get("arguments") or "{}"}}
                for index, call in enumerate(calls)]
            messages.append(assistant_message)
            for call in assistant_message["tool_calls"]:
                name = call["function"]["name"]
                try:
                    arguments = json.loads(call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    arguments = {"command": call["function"]["arguments"]}
                if name == "exec":
                    command = str(arguments.get("command", ""))
                    emit({"type": "tool_call", "command": command})
                    if command.strip() and command.strip() in seen:
                        out = "[skipped] this exact command already ran once this turn."
                    else:
                        seen.add(command.strip())
                        out = self.execute(name, arguments, require_confirm, emit)
                else:
                    emit({"type": "tool_call", "command": name})
                    out = self.execute(name, arguments, require_confirm, emit)
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": out})
                self.session.append({"type": "tool", "name": name,
                                     "command": (arguments or {}).get("command", ""), "content": out})
                emit({"type": "tool_result", "text": out})
                if self.needs_compact(messages, tools):
                    messages = self.compact(messages, tools, emit)
        else:
            emit({"type": "notice", "text": f"stopped after {max_steps} steps"})
        emit({"type": "usage", "usage": self.last_usage,
              "breakdown": ctx_mod.breakdown(messages, tools, self.system_prompt(),
                                             self.last_usage.get("prompt_tokens", 0),
                                             self.provider.context_window)})
        if self.hooks:
            stop = self.hooks.run("Stop", {"turns": self.session.turns()}, cwd=self.root,
                                  session_id=self.session.id)
            if stop.contexts:
                self.ensure_snapshot("hook", "\n".join(stop.contexts))
        emit({"type": "done"})
        return final_text

    def make_title(self):
        first = ""
        for event in self.session.events():
            if event.get("type") == "user":
                first = event.get("content", "")
                break
        if not first:
            return ""
        try:
            from .sessions import parse_title, title_prompt

            result = self.provider.chat_with_retry(title_prompt(first), tools=None, effort="off", attempts=1)
            title = parse_title(result.get("content") or "", first)
        except Exception:  # noqa: BLE001 - a missing title must not block the turn
            from .sessions import parse_title

            title = parse_title("", first)
        if title:
            self.session.set(title=title)
        return title


def build_agent(config, session_id=None, resume=False, plugins=None):
    """Wire everything up. Shared by the CLI and the WebUI."""
    from . import mcp as mcp_mod
    from . import plugins as plugins_mod
    from .hooks import HookEngine
    from .sessions import SessionStore

    root = pathlib.Path(ctx_mod.__file__).resolve().parent.parent
    store = SessionStore(root / "history" / "sessions", root / "history")
    session = store.get(session_id) if session_id else None
    if session is None:
        session = store.latest() if resume else None
    if session is None:
        session = store.create(model=config.get("MODEL", ""), effort=config.get("REASONING_EFFORT", ""),
                               approval=config.get("APPROVAL_MODE", ""))
    shell = ctx_mod.detect_shell(root, config.get("SHELL", "auto"))
    provider = providers.Provider(config)
    if plugins is None:
        dirs = [root / str(name) for name in (config.get("PLUGIN_DIRS") or ["plugins"])]
        dirs += [pathlib.Path.home() / ".pyclaw" / "plugins", pathlib.Path.home() / ".codex" / "plugins"]
        loaded = plugins_mod.discover(dirs, config.get("PLUGINS_ENABLED"), config)
    else:
        loaded = plugins
    mcp_manager = mcp_mod.MCPManager(mcp_mod.specs_from_config(config, [{"name": p.name, "mcp": p.mcp}
                                                                      for p in loaded]), cwd=root)
    hooks = HookEngine(config.get("HOOKS"), [{"name": p.name, "root": str(p.root), "hooks": p.hooks}
                                             for p in loaded],
                       mcp_call=mcp_manager.call,
                       model_call=lambda instruction, payload: provider.chat_with_retry(
                           [{"role": "user", "content": f"{instruction}\n\n{json.dumps(payload, ensure_ascii=False)}"}],
                           tools=None, effort="off", attempts=1).get("content", ""),
                       data_dir=pathlib.Path.home() / ".pyclaw" / "plugin-data")
    agent = Agent(config, store, session, provider, shell, hooks, mcp_manager, loaded, root=root)
    if session.turns() <= 1:
        hooks.run("SessionStart", {"source": "startup" if not resume else "resume"},
                  cwd=root, session_id=session.id)
    return agent


def end_session(agent):
    """Fire SessionEnd exactly once when a surface shuts down."""
    if agent is not None and getattr(agent, "hooks", None):
        agent.hooks.run("SessionEnd", {"session_id": agent.session.id}, cwd=agent.root,
                        session_id=agent.session.id)
