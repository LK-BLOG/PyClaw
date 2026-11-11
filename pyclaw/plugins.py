"""Plugin discovery and contribution loading (skills, hooks, MCP servers, tools)."""

from __future__ import annotations

import json
import os
import pathlib
import re

MANIFESTS = ((".pyclaw-plugin", "plugin.json"), (".codex-plugin", "plugin.json"),
             (".claude-plugin", "plugin.json"))
SKIP_DIRS = {".git", "node_modules", "__pycache__", "tests", "benchmarks", "docs", "assets",
             "examples", "scripts", ".github", "commands", "hooks", "skills"}


class ToolContext:
    """Handed to a plugin's register(ctx) function."""

    def __init__(self, plugin):
        self.plugin = plugin
        self.root = plugin.root
        self.config = plugin.config
        self.data_dir = plugin.data_dir
        self.tools = plugin.tools

    def add_tool(self, name, description="", parameters=None, fn=None, handler=None):
        callable_fn = fn or handler
        if not name or not callable(callable_fn):
            return None
        entry = {
            "type": "function",
            "function": {
                "name": name,
                "description": description or f"{name} (from plugin {self.plugin.name})",
                "parameters": parameters or {"type": "object", "properties": {}},
            },
            "_handler": callable_fn,
            "_plugin": self.plugin.name,
        }
        self.tools.append(entry)
        return entry

    def add_mcp(self, spec):
        if isinstance(spec, dict):
            self.plugin.mcp.append(dict(spec, name=spec.get("name") or self.plugin.name))

    def add_settings(self, rows):
        return self.plugin.add_settings(rows)

    def add_webui(self, css="", js=""):
        self.plugin.ui_css += css or ""
        self.plugin.ui_js += js or ""


class Plugin:
    def __init__(self, name, root, manifest, source="user"):
        self.name = name
        self.root = pathlib.Path(root)
        self.manifest = manifest or {}
        self.source = source
        self.skills = []
        self.hooks = {}
        self.mcp = []
        self.tools = []
        self.ui_css = ""
        self.ui_js = ""
        self.settings = []
        self.attachments = None
        self.errors = []
        self.enabled = bool(self.manifest.get("enabled", True))
        self.version = str(self.manifest.get("version") or "")  # optional; most plugins have none
        self.description = str(self.manifest.get("description", ""))
        self.config = {}
        self.data_dir = pathlib.Path.home() / ".pyclaw" / "plugin-data" / name

    def load(self):
        self._load_skills()
        self._load_hooks()
        self._load_webui()
        self.add_settings(self.manifest.get("settings"))
        for spec in self.manifest.get("mcp") or []:
            if isinstance(spec, dict):
                self.mcp.append(dict(spec, name=spec.get("name") or self.name))
        if isinstance(self.manifest.get("mcpServers"), dict):
            for server_name, spec in self.manifest["mcpServers"].items():
                if isinstance(spec, dict):
                    self.mcp.append(dict(spec, name=server_name))
        self._load_tools()
        self._ensure_data_dir()
        return self

    def _ensure_data_dir(self):
        """Plugins write their state here; the directory has to exist first."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.errors.append(f"data dir: {exc}")

    def add_settings(self, rows):
        added = []
        for row in rows or []:
            if isinstance(row, dict):
                added.append(row)
            elif isinstance(row, (list, tuple)):
                added.append(tuple(row))
        self.settings.extend(added)
        return added

    def _load_webui(self):
        spec = self.manifest.get("webui") or {}
        if isinstance(spec, str):
            spec = {"js": spec}
        for key, attr in (("css", "ui_css"), ("js", "ui_js")):
            target = self._path(spec.get(key))
            if target and target.exists():
                try:
                    setattr(self, attr, getattr(self, attr) + target.read_text(encoding="utf-8"))
                except OSError as exc:
                    self.errors.append(f"webui {key}: {exc}")
        self.attachments = self._load_attachment_handler(self.manifest.get("attachments"))

    def _load_attachment_handler(self, target):
        path = self._path(target)
        if not path or not path.exists():
            return None
        try:
            namespace = {"__file__": str(path), "__name__": f"pyclaw_attach_{self.name}"}
            exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)  # noqa: S102
            handler = namespace.get("transform")
            return handler if callable(handler) else None
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"attachments: {exc}")
            return None

    def _path(self, value):
        if not value:
            return None
        target = (self.root / str(value)).resolve()
        try:
            target.relative_to(self.root.resolve())
        except ValueError:
            return None
        return target

    def _load_skills(self):
        root = self._path(self.manifest.get("skills") or "skills") or (self.root / "skills")
        if root.is_file():
            root = root.parent
        if not root.exists():
            return
        for entry in sorted(root.iterdir()):
            skill_file = entry / "SKILL.md" if entry.is_dir() else (entry if entry.suffix == ".md" else None)
            if skill_file and skill_file.exists():
                self.skills.append({
                    "name": f"{self.name}:{entry.stem}" if entry.is_dir() else f"{self.name}:{entry.stem}",
                    "path": str(skill_file),
                    "summary": _frontmatter(skill_file).get("description", "")[:200],
                })

    def _load_hooks(self):
        target = self._path(self.manifest.get("hooks"))
        candidates = [target] if target else []
        candidates += [self.root / "hooks" / name for name in
                       ("claude-codex-hooks.json", "hooks.json", "codex-hooks.json")]
        for candidate in candidates:
            if candidate and candidate.exists() and candidate.is_file():
                try:
                    self.hooks = json.loads(candidate.read_text(encoding="utf-8-sig"))
                    return
                except (json.JSONDecodeError, OSError) as exc:
                    self.errors.append(f"hooks: {exc}")

    def _load_tools(self):
        target = self._path(self.manifest.get("tools"))
        candidates = [target] if target else []
        candidates += [self.root / "tools.py", self.root / "pyclaw_tools.py"]
        for candidate in candidates:
            if not candidate or not candidate.exists() or candidate.suffix != ".py":
                continue
            try:
                namespace = {"__file__": str(candidate), "__name__": f"pyclaw_plugin_{self.name}"}
                exec(compile(candidate.read_text(encoding="utf-8"), str(candidate), "exec"), namespace)  # noqa: S102
                context = ToolContext(self)
                register = namespace.get("register")
                if callable(register):
                    register(context)
                for row in namespace.get("TOOLS") or []:
                    if isinstance(row, dict) and row.get("function", {}).get("name"):
                        handler = row.get("handler") or row.get("fn")
                        if callable(handler):
                            context.add_tool(row["function"]["name"], row["function"].get("description", ""),
                                             row["function"].get("parameters"), handler)
                return
            except Exception as exc:  # noqa: BLE001 - a broken plugin must not stop startup
                self.errors.append(f"tools: {exc}")


def _frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not match:
        return {}
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip("'\"")
    return data


def _manifest_for(directory):
    for folder, filename in MANIFESTS:
        candidate = directory / folder / filename
        if candidate.exists():
            return candidate
    for filename in ("plugin.json", "plugin.yaml", "plugin.yml"):
        candidate = directory / filename
        if candidate.exists() and candidate.suffix == ".json":
            return candidate
    return None


def _config_values(config):
    """Read the settings out of whatever the caller passed as config.

    A Config object keeps its values in .data; a plain dict is already the values.
    `dict(config)` on a Config object raises, so the fallback has to be careful.
    """
    if config is None:
        return {}
    data = getattr(config, "data", None)
    if isinstance(data, dict):
        return dict(data)
    if isinstance(config, dict):
        return dict(config)
    return {}


def discover(dirs, enabled=None, config=None, max_depth=4):
    """Scan plugin roots. A manifest may declare itself on; PLUGINS_ENABLED overrides,
    and a "!name" entry forces a plugin off."""
    names = [str(name).strip() for name in (enabled or []) if str(name).strip()]
    enabled = {name for name in names if not name.startswith("!")}
    disabled = {name[1:] for name in names if name.startswith("!")}
    found, seen = [], set()
    for root in dirs:
        root = pathlib.Path(root).expanduser()
        if not root.exists():
            continue
        is_repo = root.name == "plugins" and root.parent.name != ".pyclaw"
        for directory in _walk(root, max_depth):
            manifest_path = _manifest_for(directory)
            if not manifest_path:
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except (json.JSONDecodeError, OSError):
                continue
            name = str(manifest.get("name") or directory.name)
            if name in seen:
                continue
            seen.add(name)
            plugin = Plugin(name, directory, manifest, source="repo" if is_repo else "user")
            plugin.config = _config_values(config)
            if name in disabled:
                plugin.enabled = False
            elif name in enabled:
                plugin.enabled = True
            elif is_repo and not manifest.get("enabled"):
                plugin.enabled = False
            found.append(plugin.load())
    # Plugin-declared settings have to reach the config, otherwise the plugin's
    # own knobs never show up and never take effect.
    register = getattr(config, "register_plugin_keys", None)
    if callable(register):
        rows = []
        for plugin in found:
            rows.extend(plugin.settings or [])
        if rows:
            register(rows)
    return found


def _walk(root, max_depth):
    root = pathlib.Path(root)
    stack = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        yield directory
        if depth >= max_depth:
            continue
        try:
            children = [child for child in directory.iterdir() if child.is_dir()]
        except OSError:
            continue
        for child in children:
            if child.name in SKIP_DIRS or child.name.startswith(".") and not child.name.endswith("-plugin"):
                if child.name not in (".codex-plugin", ".claude-plugin", ".pyclaw-plugin"):
                    continue
            stack.append((child, depth + 1))


def skill_index(plugins):
    rows = []
    for plugin in plugins or []:
        if plugin.enabled:
            rows.extend(plugin.skills)
    return rows


def revision(dirs, enabled=None, config=None):
    """Cheap fingerprint of every plugin file, so the WebUI can hot-reload them."""
    import hashlib

    digest = hashlib.sha1()
    for root in dirs:
        root = pathlib.Path(root).expanduser()
        if not root.exists():
            continue
        for directory in _walk(root, 4):
            manifest = _manifest_for(directory)
            if manifest and manifest.exists():
                try:
                    digest.update(str(manifest.stat().st_mtime_ns).encode())
                except OSError:
                    continue
            # The manifest is not the plugin: tools.py, hooks.json and SKILL.md
            # are the files that actually change what the plugin does.
            for candidate in _content_files(directory):
                try:
                    stat = candidate.stat()
                except OSError:
                    continue
                digest.update(str(candidate).encode())
                digest.update(str(stat.st_mtime_ns).encode())
                digest.update(str(stat.st_size).encode())
    for name in sorted(enabled or []):
        digest.update(str(name).encode())
    return digest.hexdigest()[:16]


# Files whose change must invalidate the plugin revision.
REVISION_FILES = ("tools.py", "pyclaw_tools.py", "plugin.json", "hooks.json",
                  "claude-codex-hooks.json", "codex-hooks.json", "SKILL.md")


def _content_files(directory):
    """The plugin files that matter for hot-reload, without walking huge trees."""
    out = []
    for name in REVISION_FILES:
        candidate = directory / name
        if candidate.is_file():
            out.append(candidate)
    for folder in ("hooks", "skills"):
        base = directory / folder
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in (".json", ".md") and not path.name.startswith("."):
                out.append(path)
    return out


def ui_bundle(plugins):
    css = "\n".join(plugin.ui_css for plugin in plugins or [] if plugin.enabled and plugin.ui_css)
    js = "\n".join(f"/* plugin: {plugin.name} */\n{plugin.ui_js}"
                   for plugin in plugins or [] if plugin.enabled and plugin.ui_js)
    settings = []
    for plugin in plugins or []:
        if plugin.enabled:
            settings.extend(plugin.settings)
    return css, js, settings


def transform_attachment(plugins, item, context):
    """Let plugins turn an attachment into model content blocks."""
    for plugin in plugins or []:
        if not plugin.enabled or not plugin.attachments:
            continue
        try:
            blocks = plugin.attachments(item, context)
        except Exception as exc:  # noqa: BLE001 - a broken plugin must not kill a turn
            plugin.errors.append(f"attachments: {exc}")
            continue
        if blocks:
            return blocks
    return None
