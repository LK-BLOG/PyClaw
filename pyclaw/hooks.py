"""Hook engine: 12 events, 4 handler types, Codex/Claude compatible JSON on stdio."""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import time

EVENTS = ["PreToolUse", "PermissionRequest", "PostToolUse", "PreCompact", "PostCompact",
          "SessionStart", "SessionEnd", "UserPromptSubmit", "SubagentStart", "SubagentStop",
          "Stop", "Interrupt"]
HANDLER_TYPES = ("command", "mcp_tool", "prompt", "agent")
DEFAULT_TIMEOUT = 5.0

_CAMEL = {"sessionStart": "SessionStart", "sessionEnd": "SessionEnd", "userPromptSubmit": "UserPromptSubmit",
          "userPromptSubmitted": "UserPromptSubmit", "preToolUse": "PreToolUse", "postToolUse": "PostToolUse",
          "preCompact": "PreCompact", "postCompact": "PostCompact", "subagentStart": "SubagentStart",
          "subagentStop": "SubagentStop", "permissionRequest": "PermissionRequest", "stop": "Stop",
          "interrupt": "Interrupt"}


def normalise_event(name):
    name = str(name or "").strip()
    if name in EVENTS:
        return name
    return _CAMEL.get(name) or _CAMEL.get(name[:1].lower() + name[1:]) or name


def _argv(command):
    out, buf, quote = [], [], ""
    for ch in command or "":
        if quote:
            if ch == quote:
                quote = ""
            else:
                buf.append(ch)
        elif ch in "'\"":
            quote = ch
        elif ch.isspace():
            if buf:
                out.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


class HookResult:
    def __init__(self):
        self.contexts = []
        self.messages = []
        self.blocked = False
        self.reason = ""
        self.errors = []

    def merge(self, other):
        self.contexts.extend(other.contexts)
        self.messages.extend(other.messages)
        self.errors.extend(other.errors)
        if other.blocked:
            self.blocked = True
            self.reason = other.reason or self.reason
        return self

    @property
    def summary(self):
        """One readable line about what the hooks did (or failed to do)."""
        bits = []
        if self.blocked:
            bits.append(f"blocked: {self.reason}")
        if self.contexts:
            bits.append(f"{len(self.contexts)} context block(s)")
        if self.messages:
            bits.append(f"{len(self.messages)} message(s)")
        if self.errors:
            bits.append(f"{len(self.errors)} error(s)")
        return "; ".join(bits) or "no hooks ran"


class HookEngine:
    """Runs matching handlers and collects additionalContext for the tail snapshot."""

    def __init__(self, config=None, plugins=None, mcp_call=None, model_call=None, data_dir=None):
        self.handlers = []
        self.mcp_call = mcp_call
        self.model_call = model_call
        # A relative data dir breaks as soon as the hook runs from another cwd.
        self.data_dir = pathlib.Path(data_dir).expanduser().absolute() if data_dir \
            else pathlib.Path.home() / ".pyclaw" / "plugin-data"
        self._load(config or {}, None)
        for plugin in plugins or []:
            self._load(plugin.get("hooks") or {}, plugin)

    def _load(self, config, plugin):
        hooks = config.get("hooks", config) if isinstance(config, dict) else {}
        if not isinstance(hooks, dict):
            return
        for raw_event, groups in hooks.items():
            event = normalise_event(raw_event)
            for group in groups if isinstance(groups, list) else []:
                if not isinstance(group, dict):
                    continue
                entries = group.get("hooks") if isinstance(group.get("hooks"), list) else [group]
                matcher = group.get("matcher", "")
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    kind = str(entry.get("type", "command"))
                    if kind not in HANDLER_TYPES:
                        continue
                    self.handlers.append({
                        "event": event, "matcher": matcher, "type": kind,
                        "command": entry.get("command") or entry.get("bash") or entry.get("powershell") or "",
                        "timeout": float(entry.get("timeout") or entry.get("timeoutSec") or DEFAULT_TIMEOUT),
                        "status": entry.get("statusMessage", ""),
                        "prompt": entry.get("prompt", ""),
                        "plugin_root": (plugin or {}).get("root", ""),
                        "plugin": (plugin or {}).get("name", ""),
                    })

    def describe(self):
        return [{"event": h["event"], "type": h["type"], "plugin": h["plugin"], "command": h["command"][:120]}
                for h in self.handlers]

    def _matches(self, handler, payload):
        matcher = handler.get("matcher") or ""
        if not matcher:
            return True
        probe = " ".join(str(payload.get(key, "")) for key in ("source", "tool_name", "command", "event"))
        try:
            return re.search(matcher, probe) is not None
        except re.error:
            return matcher in probe

    def run(self, event, payload=None, cwd=None, session_id=""):
        result = HookResult()
        payload = dict(payload or {})
        payload["hook_event_name"] = event
        for handler in self.handlers:
            if handler["event"] != event or not self._matches(handler, payload):
                continue
            try:
                result.merge(self._invoke(handler, payload, cwd, session_id))
            except Exception as exc:  # noqa: BLE001 - hooks never break a turn
                result.errors.append(f"{handler['plugin'] or 'config'}:{event}: {exc}")
        return result

    def _invoke(self, handler, payload, cwd, session_id):
        kind = handler["type"]
        if kind == "command":
            return self._command(handler, payload, cwd, session_id)
        if kind == "mcp_tool":
            return self._mcp(handler, payload, session_id)
        return self._model(handler, payload, kind)

    def _environment(self, handler, session_id):
        env = dict(os.environ)
        root = handler.get("plugin_root") or ""
        env["CLAUDE_PLUGIN_ROOT"] = root
        env["PYCLAW_PLUGIN_ROOT"] = root
        env["PLUGIN_ROOT"] = root
        env["PLUGIN_DATA"] = str(self.data_dir)
        env["CLAUDE_PLUGIN_DATA"] = str(self.data_dir)
        env["CLAUDE_CONFIG_DIR"] = env.get("CLAUDE_CONFIG_DIR") or str(pathlib.Path.home() / ".claude")
        if session_id:
            env["PYCLAW_SESSION_ID"] = session_id
        if handler.get("plugin"):
            env["PYCLAW_PLUGIN_NAME"] = handler["plugin"]
        return env

    def _command(self, handler, payload, cwd, session_id):
        result = HookResult()
        command = (handler["command"] or "").replace("${CLAUDE_PLUGIN_ROOT}", handler.get("plugin_root") or "") \
                                            .replace("${PLUGIN_ROOT}", handler.get("plugin_root") or "")
        argv = _argv(command)
        if not argv:
            return result
        timeout = max(0.2, min(handler["timeout"], 60.0))
        try:
            proc = subprocess.run(argv, input=json.dumps(payload, ensure_ascii=False), text=True,
                                  encoding="utf-8", errors="replace", capture_output=True,
                                  timeout=timeout, cwd=cwd, env=self._environment(handler, session_id))
        except subprocess.TimeoutExpired:
            result.errors.append(f"{handler['plugin'] or 'config'}:{handler['event']} timed out after {timeout}s")
            return result
        except OSError as exc:
            result.errors.append(f"{handler['plugin'] or 'config'}:{handler['event']} failed to start: {exc}")
            return result
        self._absorb(result, proc.stdout, handler)
        return result

    def _mcp(self, handler, payload, session_id):
        result = HookResult()
        if not self.mcp_call:
            result.errors.append("mcp_tool hook ignored: MCP is unavailable")
            return result
        target = handler.get("command") or handler.get("tool") or ""
        try:
            output = self.mcp_call(target, payload)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"mcp hook {target}: {exc}")
            return result
        self._absorb(result, output if isinstance(output, str) else json.dumps(output, ensure_ascii=False), handler)
        return result

    def _model(self, handler, payload, kind):
        result = HookResult()
        if not self.model_call:
            result.errors.append(f"{kind} hook ignored: no model available")
            return result
        instruction = handler.get("prompt") or handler.get("command") or ""
        try:
            answer = self.model_call(instruction, payload)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{kind} hook: {exc}")
            return result
        if isinstance(answer, str) and answer.strip():
            result.contexts.append(answer.strip())
        return result

    @staticmethod
    def _absorb(result, stdout, handler):
        text = (stdout or "").strip()
        if not text:
            return
        payload = None
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = None
        if not isinstance(payload, dict):
            result.contexts.append(text)
            return
        if payload.get("systemMessage"):
            result.messages.append(str(payload["systemMessage"]))
        for key in ("additionalContext", "additional_context"):
            if payload.get(key):
                result.contexts.append(str(payload[key]))
        specific = payload.get("hookSpecificOutput") or payload.get("hook_specific_output") or {}
        if not isinstance(specific, dict):
            specific = {}
        for key in ("additionalContext", "additional_context"):
            if specific.get(key):
                result.contexts.append(str(specific[key]))
        # A refusal can be stated at the top level or, as Claude Code and Codex
        # do it, nested in hookSpecificOutput. Only reading the top level meant
        # a hook that said "deny" was ignored and the command ran anyway.
        sources = (payload, specific)
        for source in sources:
            for key in ("decision", "permissionDecision", "permission_decision"):
                if str(source.get(key, "")).lower() in ("block", "deny", "denied", "forbidden"):
                    result.blocked = True
                    result.reason = (source.get("reason") or source.get("justification")
                                     or source.get("permissionDecisionReason")
                                     or payload.get("reason") or "blocked by hook")
                    break
        if payload.get("error") or payload.get("errors"):
            result.errors.append(f"{handler.get('plugin') or 'config'}: {payload.get('error') or payload.get('errors')}")
