"""Environment execution, token accounting and tool-output spill."""

from __future__ import annotations

import datetime
import locale
import os
import pathlib
import re
import shutil
import subprocess
import time
import uuid

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef\u3040-\u30ff]")


# ---------------------------------------------------------------- token accounting

def estimate_tokens(text):
    if not text:
        return 0
    cjk = len(CJK.findall(text))
    other = len(text) - cjk
    return int(cjk * 0.7 + other * 0.25) + 1


# 非文本块（图片等）的成本估算基准：一张图至少按这个 token 数算，别让它免费。
IMAGE_TOKEN_BASE = 1024
IMAGE_BYTES_PER_TOKEN = 750


def _block_tokens(block):
    """单个 content block 的 token 估算。非文本块（图片等）也要算钱。"""
    if "text" in block:
        return estimate_tokens(block.get("text") or "")
    kind = str(block.get("type") or "")
    data = ""
    image = block.get("image_url")
    if isinstance(image, dict):
        data = str(image.get("url") or "")
    elif isinstance(image, str):
        data = image
    if not data:
        data = str(block.get("data") or block.get("b64_json") or "")
    if kind.startswith("image") or "image_url" in block or data.startswith("data:image"):
        return max(IMAGE_TOKEN_BASE, len(data) // IMAGE_BYTES_PER_TOKEN)
    # 其它看不懂的块：至少记一笔，别让它白嫖上下文
    return max(8, len(json_dumps(block)) // 4)


def estimate_messages(messages):
    total = 0
    for message in messages:
        total += 4
        content = message.get("content")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += _block_tokens(block) + 4
        for call in message.get("tool_calls") or []:
            fn = call.get("function", {}) if isinstance(call, dict) else {}
            total += estimate_tokens(fn.get("name", "")) + estimate_tokens(fn.get("arguments", "")) + 4
        total += estimate_tokens(message.get("reasoning_content") or "")
    return total


def estimate_tools(tools):
    return estimate_tokens(json_dumps(tools)) + 4 if tools else 0


def json_dumps(value):
    import json

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------- truncation + spill

def truncate(text, max_lines=500, max_bytes=65536, line_max=500):
    """Keep the head. Returns (head, omitted_bytes, truncated_lines)."""
    raw = text or ""
    encoded = raw.encode("utf-8")
    lines = raw.splitlines()
    kept, truncated = [], 0
    size = 0
    for line in lines[:max_lines]:
        piece = line if len(line) <= line_max else line[:line_max] + "..."
        size += len(piece.encode("utf-8")) + 1
        if size > max_bytes:
            truncated = max(truncated, len(lines) - len(kept))
            break
        kept.append(piece)
    if len(lines) > len(kept):
        truncated = len(lines) - len(kept)
    head = "\n".join(kept)
    # The total minus the head already covers whole dropped lines *and* the bytes
    # cut off inside a line by line_max.
    omitted = len(encoded) - len(head.encode("utf-8"))
    return head, max(0, omitted), truncated


class Spiller:
    """Writes oversized tool output under history/tool/<session>/ and hands back a pointer."""

    def __init__(self, root, max_lines=500, max_bytes=65536, line_max=500):
        self.root = pathlib.Path(root)
        self.max_lines = max_lines
        self.max_bytes = max_bytes
        self.line_max = line_max
        self._counter = 0

    def dir_for(self, session_id):
        path = self.root / (session_id or "default")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def touches_spill(self, command):
        """True when the command reads a spill file, so the pointer would be useless.

        The old check ("tool" anywhere in the command) matched things like
        `cat tool.py` or `ls toolkit/`, which then swallowed the pointer to the
        omitted output and the model never got to see it.
        """
        text = (command or "").lower()
        if not text:
            return False
        root_name = str(self.root.name).lower()
        if root_name not in text:
            return False
        # A path into history/tool/<session>, or the .log file the spiller writes.
        if f"{root_name}/" in text or f"{root_name}\\" in text:
            return True
        if re.search(r"\d{6}-\d+\.log", text):
            return True
        return False

    def save(self, text, session_id):
        self._counter += 1
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self.dir_for(session_id) / f"{stamp}-{self._counter}-{uuid.uuid4().hex[:6]}.log"
        path.write_text(text, encoding="utf-8", errors="replace")
        return path


def format_tool_result(command, exit_code, output, seconds, cwd_label, spiller, session_id, root):
    """Model-facing tool result: head of the output plus a pointer to the rest."""
    body = ANSI.sub("", output or "")
    head, omitted, truncated = truncate(body, spiller.max_lines, spiller.max_bytes, spiller.line_max)
    parts = [f"[exit {exit_code}] [cwd {cwd_label}] [{seconds:.1f}s]"]
    parts.append(head if head.strip() else "(no output)")
    if omitted > 0:
        if not spiller.touches_spill(command):
            try:
                path = spiller.save(body, session_id)
                try:
                    rel = path.relative_to(root).as_posix()
                except ValueError:
                    # The spill dir lives outside the project root: fall back to
                    # the absolute path rather than losing the pointer.
                    rel = path.as_posix()
                parts.append(f"(Omitted {omitted} bytes, {truncated} lines. Full output: {rel} "
                             f"- read it with cat/less, or search it with rg.)")
            except OSError:
                parts.append(f"(Omitted {omitted} bytes, {truncated} lines.)")
        else:
            parts.append(f"(Omitted {omitted} bytes, {truncated} lines.)")
    return "\n".join(parts)


# ---------------------------------------------------------------- shell

class Shell:
    def __init__(self, kind, argv_prefix, display_cwd, hint, uses_windows_paths):
        self.kind = kind
        self.argv_prefix = argv_prefix
        self.display_cwd = display_cwd
        self.hint = hint
        self.uses_windows_paths = uses_windows_paths

    def argv(self, command):
        return list(self.argv_prefix) + [command]


def _wsl_mount(win_path):
    path = str(win_path).replace("\\", "/")
    match = re.match(r"^([A-Za-z]):(.*)$", path)
    if not match:
        return path
    return f"/mnt/{match.group(1).lower()}{match.group(2)}"


def _git_bash():
    for base in ("D:/Program Files/Git", "C:/Program Files/Git", "C:/Program Files (x86)/Git"):
        exe = pathlib.Path(base) / "bin" / "bash.exe"
        if exe.exists():
            return str(exe)
    found = shutil.which("bash.exe") or shutil.which("bash")
    return found if found and "System32" not in found else None


def detect_shell(cwd, forced="auto"):
    """WSL > Git Bash > PowerShell > CMD, unless the config forces one."""
    cwd = pathlib.Path(cwd).resolve()
    windows = os.name == "nt"
    if forced and forced != "auto":
        return _build_shell(forced, cwd, windows)
    if windows and shutil.which("wsl.exe"):
        mounted = _wsl_mount(cwd)
        if _wsl_ok(mounted):
            return _build_shell("wsl", cwd, windows, mounted)
    if windows and _git_bash():
        return _build_shell("gitbash", cwd, windows)
    if windows and shutil.which("powershell.exe"):
        return _build_shell("powershell", cwd, windows)
    if windows:
        return _build_shell("cmd", cwd, windows)
    return _build_shell("bash", cwd, windows)


def _build_shell(kind, cwd, windows, mounted=None):
    posix = str(cwd).replace("\\", "/")
    if kind == "wsl":
        target = mounted or _wsl_mount(cwd)
        return Shell("wsl", ["wsl.exe", "--cd", target, "bash", "-lc"], target,
                     "You are inside WSL (Linux). Use bash syntax, POSIX paths (/mnt/c/...) and Linux tools. "
                     "The project is mounted at the cwd above.", False)
    if kind == "gitbash":
        exe = _git_bash() or "bash.exe"
        return Shell("gitbash", [exe, "-lc"], posix, "Use bash syntax in Git Bash.", True)
    if kind == "powershell":
        return Shell("powershell", ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"], str(cwd),
                     "Use PowerShell syntax (no bash heredocs, no && chaining on older builds).", True)
    if kind == "cmd":
        return Shell("cmd", ["cmd.exe", "/d", "/s", "/c"], str(cwd),
                     "Use cmd.exe syntax (no bash heredocs, no /tmp).", True)
    return Shell("bash", ["bash", "-lc"], posix, "Use bash syntax.", False)


def _wsl_ok(mounted):
    try:
        probe = subprocess.run(["wsl.exe", "--cd", mounted, "true"], capture_output=True, timeout=8)
        return probe.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _decode(raw):
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw
    # Windows wsl.exe may hand a UTF-16LE console stream to a byte pipe.
    if raw.count(b"\x00") > max(2, len(raw) // 10):
        try:
            return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff")
        except UnicodeDecodeError:
            pass
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False), errors="replace")


def run_command(shell, command, cwd, timeout=300):
    """Run one command segment. Never raises for command failure."""
    started = time.time()
    try:
        proc = subprocess.run(shell.argv(command), cwd=None if shell.kind == "wsl" else str(cwd),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        output = _decode(proc.stdout)
        error = _decode(proc.stderr)
        error_lines = [line for line in error.splitlines()
                       if not ("localhost" in line and "WSL" in line and "NAT" in line)]
        error = "\n".join(error_lines)
        # stdout usually ends with a newline; joining blindly adds a blank line.
        merged = output.rstrip("\n")
        if error:
            merged = (merged + "\n" + error.rstrip("\n")) if merged else error.rstrip("\n")
        return proc.returncode, merged.strip(), time.time() - started
    except subprocess.TimeoutExpired as exc:
        partial = _decode(exc.stdout or b"")
        return 124, partial + f"\n(command timed out after {timeout}s)", time.time() - started
    except OSError as exc:
        return 127, f"(failed to start: {exc})", time.time() - started


def breakdown(messages, tools, system_prompt, pressure_tokens, window):
    """Five-way composition plus the free tail. All estimates share one estimator."""
    system_tokens = estimate_tokens(system_prompt)
    tools_tokens = estimate_tools(tools)
    user = assistant = tool = 0
    for message in messages:
        role = message.get("role")
        size = estimate_tokens(message.get("content") if isinstance(message.get("content"), str) else "")
        size += estimate_tokens(message.get("reasoning_content") or "")
        if role == "user":
            user += size
        elif role == "assistant":
            assistant += size
        elif role == "tool":
            tool += size
    used = pressure_tokens or (system_tokens + tools_tokens + user + assistant + tool)
    return {
        "system": system_tokens, "tools": tools_tokens, "user": user,
        "assistant": assistant, "tool": tool,
        "used": used, "window": window, "free": max(0, window - used),
        "percent": round(100.0 * used / window, 1) if window else 0.0,
    }
