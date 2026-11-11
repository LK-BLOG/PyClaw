"""Schema-driven settings. One schema feeds validation, the WebUI form and i18n."""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = HERE / "pyclaw.json"
EXAMPLE_PATH = HERE / "pyclaw.json.example"

# key: (zh label, en label, zh help, en help)
L = {
    "PROVIDER": ("供应商", "Provider", "预设供应商，选 Custom 时只用 ENDPOINT", "Preset provider; Custom uses ENDPOINT only"),
    "ENDPOINT": ("接口地址", "Endpoint", "OpenAI 兼容的 base URL", "OpenAI-compatible base URL"),
    "API_KEY": ("API 密钥", "API key", "只存在本机 pyclaw.json 里", "Stored locally in pyclaw.json"),
    "MODEL": ("模型", "Model", "请求原样发这个名字", "Sent to the API exactly as written"),
    "LANGUAGE": ("界面语言", "Language", "界面与 CLI 文案", "UI and CLI language"),
    "PORT": ("端口", "Port", "WebUI 监听端口", "WebUI listen port"),
    "WEBUI_HOST": ("监听地址", "Bind address", "改成非回环地址必须同时设置 token", "Non-loopback requires a token"),
    "WEBUI_TOKEN": ("访问令牌", "Access token", "跨机访问时必填", "Required for remote access"),
    "CONTEXT_WINDOW": ("上下文窗口", "Context window", "0 = 按模型表自动推断", "0 = infer from the model table"),
    "REASONING_EFFORT": ("思考强度", "Reasoning effort", "默认档，可被会话覆盖", "Default level, sessions may override"),
    "APPROVAL_MODE": ("权限档位", "Approval mode", "危险操作如何批准", "How risky actions get approved"),
    "SHELL": ("执行外壳", "Shell", "auto = WSL > Git Bash > PowerShell > CMD", "auto = WSL > Git Bash > PowerShell > CMD"),
    "TOOL_OUTPUT_MAX_LINES": ("输出行数上限", "Output line cap", "超出部分落盘", "Overflow is spilled to disk"),
    "TOOL_OUTPUT_MAX_BYTES": ("输出字节上限", "Output byte cap", "与行数上限先到者为准", "Whichever cap hits first"),
    "COMPACT_THRESHOLD": ("压缩阈值", "Compact threshold", "占窗口比例", "Fraction of the window"),
    "COMPACT_RETAIN_RATIO": ("保留比例", "Retain ratio", "压缩后逐字保留的近期比例", "Recent tail kept verbatim"),
    "COMPACT_MAX_TOKENS": ("摘要上限", "Summary cap", "压缩摘要的生成上限", "Generation cap for summaries"),
    "MAX_AGENT_STEPS": ("单轮最大步骤", "Max agent steps", "单轮最多工具循环次数", "Maximum tool-loop iterations per turn"),
    "ALLOW_RULES": ("长期规则", "Allow rules", "命令前缀规则", "Command prefix rules"),
    "MCP_SERVERS": ("MCP 服务器", "MCP servers", "stdio 或 HTTP", "stdio or HTTP"),
    "HOOKS": ("钩子", "Hooks", "事件到命令的映射", "Event to command mapping"),
    "PLUGINS_ENABLED": ("已启用插件", "Enabled plugins", "仓库 plugins/ 里的插件需要在这里打开", "Repo plugins/ must be listed here"),
    "PLUGIN_DIRS": ("插件目录", "Plugin dirs", "改动需重启", "Needs a restart"),
    "BLOCKED_EXTRA": ("追加黑名单", "Extra blocked", "额外直接拒绝的命令片段", "Extra commands refused outright"),
    "SUB_AGENTS_ENABLED": ("子智能体", "Sub-agents", "由子智能体插件读取", "Read by the sub-agent plugin"),
    "SUB_AGENTS": ("子智能体角色", "Sub-agent roles", "角色定义列表", "Role definition list"),
}

# key: type, default, choices, flags
SCHEMA = [
    ("PROVIDER", "str", "deepseek", None, ()),
    ("ENDPOINT", "str", "https://api.deepseek.com/v1", None, ()),
    ("API_KEY", "str", "", None, ("secret",)),
    ("MODEL", "str", "deepseek-flash", None, ()),
    ("LANGUAGE", "str", "zh-CN", ("zh-CN", "en-US"), ()),
    ("PORT", "int", 2469, None, ("restart",)),
    ("WEBUI_HOST", "str", "127.0.0.1", None, ("restart",)),
    ("WEBUI_TOKEN", "str", "", None, ("secret", "restart")),
    ("CONTEXT_WINDOW", "int", 0, None, ()),
    ("REASONING_EFFORT", "str", "high", ("off", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"), ()),
    ("APPROVAL_MODE", "str", "auto", ("request", "auto", "full"), ()),
    ("SHELL", "str", "auto", ("auto", "wsl", "gitbash", "powershell", "cmd"), ()),
    ("TOOL_OUTPUT_MAX_LINES", "int", 500, None, ("advanced",)),
    ("TOOL_OUTPUT_MAX_BYTES", "int", 65536, None, ("advanced",)),
    ("COMPACT_THRESHOLD", "float", 0.8, None, ("advanced",)),
    ("COMPACT_RETAIN_RATIO", "float", 0.16, None, ("advanced",)),
    ("COMPACT_MAX_TOKENS", "int", 8192, None, ("advanced",)),
    ("MAX_AGENT_STEPS", "int", 1000, None, ("advanced",)),
    ("ALLOW_RULES", "list", [], None, ("advanced",)),
    ("MCP_SERVERS", "list", [], None, ("advanced",)),
    ("HOOKS", "dict", {}, None, ("advanced",)),
    ("PLUGINS_ENABLED", "list", [], None, ("advanced",)),
    ("PLUGIN_DIRS", "list", ["plugins"], None, ("advanced", "restart")),
    ("BLOCKED_EXTRA", "list", [], None, ("advanced",)),
    ("SUB_AGENTS_ENABLED", "bool", False, None, ("advanced",)),
    ("SUB_AGENTS", "list", [], None, ("advanced",)),
]
SCHEMA_BY_KEY = {row[0]: row for row in SCHEMA}

# Old keys keep working; the new name wins when both are present.
LEGACY = {
    "WEBUI_PORT": "PORT",
    "WEBUI_HOST": "WEBUI_HOST",
    "WEBUI_TOKEN": "WEBUI_TOKEN",
    "WEBUI_EXEC_BLOCKED": "BLOCKED_EXTRA",
}

DEFAULTS = {row[0]: row[2] for row in SCHEMA}


def register_keys(rows):
    """Plugins contribute their own settings keys; the form and validator grow with them."""
    added = []
    for row in rows or []:
        if isinstance(row, dict):
            key, kind = row.get("key"), row.get("type", "str")
            default, choices = row.get("default"), row.get("choices")
            flags = tuple(row.get("flags") or ())
            label = row.get("label") or key
            help_text = row.get("help", "")
            L.setdefault(key, (label, label, help_text, help_text))
        else:
            try:
                key, kind, default, choices, flags = (list(row) + [None, None, None, None, ()])[:5]
            except (TypeError, ValueError):
                continue
        if not key or key in SCHEMA_BY_KEY:
            continue
        flags = tuple(flags or ()) + ("plugin",)
        SCHEMA.append((key, kind or "str", default, tuple(choices) if choices else None, flags))
        SCHEMA_BY_KEY[key] = SCHEMA[-1]
        DEFAULTS[key] = default
        added.append(key)
    return added


FALSEY = {"false", "0", "no", "off", "none", "null", ""}
TRUTHY = {"true", "1", "yes", "on"}


def _coerce(key, value):
    kind = SCHEMA_BY_KEY[key][1]
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "bool":
        if isinstance(value, str):
            low = value.strip().lower()
            if low in FALSEY:
                return False
            if low in TRUTHY:
                return True
            return True
        return bool(value)
    if kind == "list":
        return list(value) if isinstance(value, (list, tuple)) else ([] if value in (None, "") else [value])
    if kind == "dict":
        return dict(value) if isinstance(value, dict) else {}
    return "" if value is None else str(value)


def validate(key, value):
    """Return a normalised value, raising ValueError with a readable reason."""
    if key not in SCHEMA_BY_KEY:
        raise ValueError(f"unknown key {key}")
    kind, choices = SCHEMA_BY_KEY[key][1], SCHEMA_BY_KEY[key][3]
    try:
        value = _coerce(key, value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} expects {kind}") from exc
    if choices and value not in choices:
        raise ValueError(f"{key} must be one of {', '.join(choices)}")
    if kind in ("int", "float") and value < 0:
        raise ValueError(f"{key} must not be negative")
    return value


class Config:
    """Live config object. Reloads from disk when the file changes."""

    def __init__(self, path=None, example=None):
        self.path = pathlib.Path(path or CONFIG_PATH)
        self.example = pathlib.Path(example or EXAMPLE_PATH)
        self.data = dict(DEFAULTS)
        self.mtime = 0.0
        self.load()

    def load(self):
        if not self.path.exists():
            self._seed_from_example()
        raw = {}
        if self.path.exists():
            text = self.path.read_text(encoding="utf-8-sig")
            if text.strip():
                try:
                    raw = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{self.path.name} is not valid JSON: {exc}") from exc
        for old, new in LEGACY.items():
            if old in raw and new not in raw:
                raw[new] = raw[old]
        merged = dict(DEFAULTS)
        for key, value in raw.items():
            if key in SCHEMA_BY_KEY:
                try:
                    merged[key] = validate(key, value)
                except ValueError:
                    continue  # keep the default; the settings panel shows the fix
            elif key not in LEGACY:
                merged[key] = value  # plugin keys survive even before their plugin loads
        self.data = merged
        self.touch()
        return self.data

    def _seed_from_example(self):
        template = {}
        if self.example.exists():
            text = self.example.read_text(encoding="utf-8-sig")
            template = _strip_comments(text)
        for key, value in DEFAULTS.items():
            template.setdefault(key, value)
        self.path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.mtime = self.path.stat().st_mtime

    def touch(self):
        try:
            self.mtime = self.path.stat().st_mtime
        except OSError:
            self.mtime = 0.0

    def maybe_reload(self):
        try:
            if self.path.stat().st_mtime != self.mtime:
                self.load()
                return True
        except OSError:
            pass
        return False

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]

    def update(self, values):
        """Validate a patch and persist it. Returns the accepted keys."""
        accepted = {}
        for key, value in values.items():
            # Old key names still work here, exactly like on load.
            key = LEGACY.get(key, key)
            accepted[key] = validate(key, value)
        self.data.update(accepted)
        self.save()
        return accepted

    def save(self):
        ordered = {row[0]: self.data.get(row[0], row[2]) for row in SCHEMA}
        # Plugin keys are not in SCHEMA; dropping them would wipe the plugin's
        # own settings on every save.
        for key, value in self.data.items():
            if key not in ordered:
                ordered[key] = value
        self.path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.touch()
        return ordered

    def public(self, lang="zh-CN"):
        """Schema + values for the settings form. Secrets come back as-is so the
        password input can show dots; the UI never renders them anywhere else."""
        rows = []
        for key, kind, default, choices, flags in SCHEMA:
            zh, en, dzh, den = L.get(key, (key, key, "", ""))
            rows.append({
                "key": key, "type": kind, "value": self.data.get(key, default),
                "choices": list(choices or []), "flags": list(flags),
                "label": zh if lang == "zh-CN" else en,
                "help": dzh if lang == "zh-CN" else den,
            })
        return rows

    def register_plugin_keys(self, rows):
        """Merge plugin-declared settings and pick up newly written values."""
        added = register_keys(rows)
        for key in added:
            self.data.setdefault(key, DEFAULTS.get(key))
        if added:
            self.load()
        return added

    def is_ready(self):
        return bool(str(self.data.get("API_KEY", "")).strip() and str(self.data.get("ENDPOINT", "")).strip())


def _strip_comments(text):
    """pyclaw.json.example allows // and /* */ comments; JSON does not."""
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            i = text.find("\n", i)
            if i < 0:
                break
        elif text.startswith("/*", i):
            i = text.find("*/", i + 2)
            i = n if i < 0 else i + 2
        else:
            out.append(ch)
            i += 1
    cleaned = "".join(out)
    return json.loads(cleaned) if cleaned.strip() else {}
