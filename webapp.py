#!/usr/bin/env python3
"""PyClaw WebUI —— 基于 pyclaw-lite 内核。

保留原 WebUI 的 WebSocket 协议（chat / history / list_sessions / set_config ...），
底层换成 pyclaw-lite：pluggable 插件、权限策略、上下文压缩、MCP、hooks。
"""
import sys, os, json, time, hmac, secrets, asyncio, argparse, pathlib, datetime, re

PROCESS_START = time.time()
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 启动页占位服务 ─────────────────────────────────────────────
# 为什么要抢在 import fastapi 前面：下面那几行 import 要 1.9 秒，
# 这期间端口是关的，浏览器打开就是 ERR_CONNECTION_REFUSED / offline，
# 而且它不会自己重载。所以先用标准库把端口占住，吐一个启动页，
# 应用加载完再关掉它，把端口让给 uvicorn。
_SPLASH = {"srv": None, "thread": None}


def _splash_port():
    """不 import 应用配置（那会触发 pyclaw），直接读 json 拿端口。"""
    port = 2469
    try:
        data = json.loads((ROOT / "pyclaw.json").read_text(encoding="utf-8"))
        port = int(data.get("PORT") or 2469)
    except Exception:
        pass
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=", 1)[1])
            except ValueError:
                pass
    return port


def _start_splash():
    """端口一开就返回启动页；失败就算了，别挡住真正的启动。"""
    import http.server
    import socketserver
    import threading

    try:
        page = (ROOT / "splash.html").read_bytes()
    except OSError:
        return
    port = _splash_port()

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "PyClawSplash"

        def do_GET(self):
            path = self.path.split("?")[0]
            if path in ("/api/boot", "/api/migrate/status"):
                body = (b'{"starting":true,"progress":0,"done":false,'
                        b'"migrate":{"running":true,"finished":false,"percent":0,"tips":[]}}')
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()

        def log_message(self, *args):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

        def handle_error(self, request, client_address):
            pass

    try:
        srv = Server(("127.0.0.1", port), Handler)
    except OSError as exc:
        print(f"[SPLASH] 端口 {port} 被占用，跳过启动页：{exc}", flush=True)
        return
    thread = threading.Thread(target=lambda: srv.serve_forever(poll_interval=0.05), daemon=True)
    thread.start()
    _SPLASH["srv"], _SPLASH["thread"] = srv, thread
    print(f"[SPLASH] 启动页就绪 http://127.0.0.1:{port}  ({time.time()-PROCESS_START:.2f}s)", flush=True)


def _stop_splash():
    srv = _SPLASH.get("srv")
    if not srv:
        return
    _SPLASH["srv"] = None
    try:
        srv.shutdown()
        srv.server_close()
    except Exception:
        pass
    print(f"[SPLASH] 交棒给 uvicorn  ({time.time()-PROCESS_START:.2f}s)", flush=True)


if __name__ == "__main__":
    _start_splash()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from pyclaw.config import Config
from pyclaw import agent as agent_mod
from pyclaw import providers as providers_mod
import providers_catalog

CONFIG = None
AGENTS = {}          # front_session_id -> agent
AGENT_LOCK = asyncio.Lock()
ACCESS_TOKEN = ""

BOOT = {
    "progress": 0, "stage": "boot", "label": "启动中", "done": False,
    "error": None, "started_at": time.time(), "steps": [],
}


def boot(progress, stage, label):
    BOOT["progress"] = max(BOOT["progress"], int(progress))
    BOOT["stage"] = stage
    BOOT["label"] = label
    BOOT["steps"].append({
        "stage": stage, "label": label,
        "progress": BOOT["progress"],
        "at": round(time.time() - BOOT["started_at"], 3),
    })
    print(f"[BOOT] {BOOT['progress']:3d}% {stage:<10} {label}", flush=True)


# ── 后台迁移进度（启动时就开始，前端显示进度条 + Tips）──
MIGRATE = {
    "running": False, "finished": False, "started": 0.0,
    "done": 0, "total": 0, "stage": "", "current": "",
    "sessions": 0, "memories": 0, "error": None,
}

MIGRATE_TIPS = [
    "旧会话正在搬进新目录，搬完之后点开就不再卡了。",
    "提示：顶栏那个滑块是思考强度，往上拉会想得更久也更贵。",
    "提示：回答里出现卡片时，可以直接点卡片上的按钮继续。",
    "提示：Enter 发送，Shift+Enter 换行。",
    "提示：插件在设置 → 插件里开关，改完立刻生效。",
    "提示：memory/ 里的内容每次启动都会注入系统提示。",
]


def migrate_tick(done, total, stage, current=""):
    MIGRATE["done"] = int(done)
    MIGRATE["total"] = int(total)
    MIGRATE["stage"] = stage
    MIGRATE["current"] = current
    MIGRATE["elapsed"] = round(time.time() - (MIGRATE["started"] or time.time()), 2)


def get_config():
    global CONFIG
    if CONFIG is None:
        CONFIG = Config(ROOT / "pyclaw.json", ROOT / "pyclaw.json.example")
    return CONFIG


def cfg_get(key, default=""):
    try:
        value = get_config().get(key, default)
        return value if value is not None else default
    except Exception:
        return default


def save_cfg(**patch):
    """写回 pyclaw.json，供下次启动沿用。"""
    path = ROOT / "pyclaw.json"
    data = {}
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except Exception:
        data = {}
    data.update({k: v for k, v in patch.items() if v is not None})
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"warning: 写配置失败: {exc}", flush=True)
    try:
        get_config().load()
    except Exception:
        pass


_BASE_AGENT = {"agent": None}


def get_agent(sid):
    """按会话 id 打开。

    关键优化：agent 只组装一次，切会话只是换 agent.session。
    旧实现在缓存未命中时重新 build 一次（插件扫描 + MCP + hooks，十几秒），
    所以每点一个会话都像“现场迁移”。
    """
    key = sid or "default"
    cached = AGENTS.get(key)
    if cached is not None:
        return cached
    cfg = get_config()
    base = _BASE_AGENT["agent"]
    if base is None:
        base = agent_mod.build_agent(cfg, session_id=None, resume=False, plugins=_load_plugins())
        _BASE_AGENT["agent"] = base
    existing = None
    try:
        if sid and base.store.get(sid):
            existing = sid
    except Exception:
        existing = None
    if existing:
        session = base.store.get(existing)
        if session is not None:
            # 老会话里存的 effort 会盖过全局设置，切进来时按当前配置对齐一次
            want = str(cfg.get("REASONING_EFFORT") or "")
            if want and session.meta.get("effort") != want:
                try:
                    session.set(effort=want)
                except Exception:
                    pass
            base.session = session
            try:
                base.sync_session_route()
            except Exception:
                pass
            AGENTS[key] = base
            AGENTS[base.session.id] = base
            return base
    # 新会话：只在进程里开一个，别为它重建整个 agent
    try:
        session = base.store.create(model=cfg.get("MODEL", ""), effort=cfg.get("REASONING_EFFORT", ""),
                                    approval=cfg.get("APPROVAL_MODE", ""))
        base.session = session
        base.sync_session_route()
    except Exception:
        pass
    AGENTS[key] = base
    AGENTS[base.session.id] = base
    return base


def agent_tools(agent):
    try:
        schemas = agent.tool_schemas() or []
    except Exception:
        return []
    names = []
    for item in schemas:
        fn = (item or {}).get("function") or {}
        if fn.get("name"):
            names.append(fn["name"])
    return names


# ── 旧版兼容 ──
def _legacy_state():
    """探测旧版 PyClaw 留下的东西：API.txt、ACCESS_TOKEN、pyclaw_data 会话。"""
    legacy = {"api_txt": False, "token": False, "old_sessions": 0,
              "webapp": (ROOT / "webapp_legacy.py").exists()}
    try:
        legacy["api_txt"] = (ROOT / "API.txt").exists() or (ROOT / "volc_api.txt").exists()
    except OSError:
        pass
    try:
        raw = json.loads((ROOT / "pyclaw.json").read_text(encoding="utf-8-sig") or "{}")
        legacy["token"] = bool(raw.get("ACCESS_TOKEN")) and not raw.get("WEBUI_TOKEN")
    except Exception:
        pass
    try:
        data_dir = ROOT / "pyclaw_data"
        if data_dir.exists():
            legacy["old_sessions"] = len([x for x in data_dir.rglob("*.json")])
            legacy["old_memory_db"] = (data_dir / "pyclaw_memory.db").exists()
            legacy["memory_migrated"] = (data_dir / ".memory_migrated").exists()
    except OSError:
        pass
    return legacy


_PLUGIN_CACHE = {"at": 0.0, "rows": []}


def _plugin_rows(force=False):
    """插件清单；带缓存，避免每次请求都扫一遍目录。"""
    import time as _time
    if not force and _PLUGIN_CACHE["rows"] and (_time.time() - _PLUGIN_CACHE["at"] < 30):
        return _PLUGIN_CACHE["rows"]
    rows = []
    try:
        from pyclaw import plugins as plugins_mod
        cfg = get_config()
        dirs = [ROOT / str(n) for n in (cfg.get("PLUGIN_DIRS") or ["plugins"])]
        dirs += [__import__("pathlib").Path.home() / ".pyclaw" / "plugins",
                 __import__("pathlib").Path.home() / ".codex" / "plugins"]
        for plugin in plugins_mod.discover(dirs, cfg.get("PLUGINS_ENABLED"), cfg.data):
            rows.append({
                "name": plugin.name,
                "version": getattr(plugin, "version", "") or "",
                "description": getattr(plugin, "description", "") or "",
                "tools": len(getattr(plugin, "tools", []) or []),
                "skills": len(getattr(plugin, "skills", []) or []),
                "enabled": bool(getattr(plugin, "enabled", True)),
                "errors": list(getattr(plugin, "errors", []) or [])[:3],
            })
    except Exception as exc:
        print(f"warning: 插件列表失败: {exc}", flush=True)
    _PLUGIN_CACHE.update({"at": _time.time(), "rows": rows})
    return rows


def migrate_legacy():
    """把旧版配置迁移到 lite 的键位；只补空缺，不覆盖用户现值。"""
    path = ROOT / "pyclaw.json"
    changed = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except Exception:
        raw = {}
    if raw.get("ACCESS_TOKEN") and not raw.get("WEBUI_TOKEN"):
        raw["WEBUI_TOKEN"] = raw["ACCESS_TOKEN"]
        changed.append("ACCESS_TOKEN -> WEBUI_TOKEN")
    if not str(raw.get("API_KEY") or "").strip():
        for name in ("API.txt", "volc_api.txt"):
            key_file = ROOT / name
            if key_file.exists():
                try:
                    body = key_file.read_text(encoding="utf-8", errors="replace").strip()
                except OSError:
                    continue
                if body:
                    raw["API_KEY"] = body.splitlines()[0].strip()
                    changed.append(f"API_KEY <- {name}")
                    break
    if str(raw.get("ENDPOINT") or "").rstrip("/") == "https://api.deepseek.com":
        raw["ENDPOINT"] = "https://api.deepseek.com/v1"
        changed.append("ENDPOINT 补 /v1")
    if changed:
        try:
            path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[MIGRATE] {', '.join(changed)}", flush=True)
        except Exception as exc:
            print(f"warning: 迁移写回失败: {exc}", flush=True)
    return changed


_PLUGIN_OBJECTS = {"at": 0.0, "items": []}


def _load_plugins(force=False):
    """进程内缓存：build_agent 每次都会 discover，这里只扫一次。"""
    import time as _time
    if not force and _PLUGIN_OBJECTS["items"] and (_time.time() - _PLUGIN_OBJECTS["at"] < 120):
        return _PLUGIN_OBJECTS["items"]
    items = []
    try:
        from pyclaw import plugins as plugins_mod
        cfg = get_config()
        dirs = [ROOT / str(n) for n in (cfg.get("PLUGIN_DIRS") or ["plugins"])]
        dirs += [pathlib.Path.home() / ".pyclaw" / "plugins", pathlib.Path.home() / ".codex" / "plugins"]
        items = plugins_mod.discover(dirs, cfg.get("PLUGINS_ENABLED"), cfg.data)
    except Exception as exc:
        print(f"warning: 插件加载失败: {exc}", flush=True)
    _PLUGIN_OBJECTS.update({"at": _time.time(), "items": items})
    return items


def migrate_sessions(progress=None):
    """把旧版 pyclaw_data/pyclaw_sessions.json 迁进 lite 的 history/sessions。

    progress(done, total, stage, current) 用来喂前端的迁移进度条。
    """
    legacy = ROOT / "pyclaw_data" / "pyclaw_sessions.json"
    mark = ROOT / "pyclaw_data" / ".migrated_to_lite"
    if not legacy.exists():
        return {"migrated": 0, "reason": "no_legacy_file"}
    if mark.exists():
        return {"migrated": 0, "reason": "already_migrated"}
    try:
        payload = json.loads(legacy.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"migrated": 0, "reason": f"parse_error: {exc}"}
    rows = payload.get("sessions") if isinstance(payload, dict) else None
    if not isinstance(rows, dict):
        return {"migrated": 0, "reason": "unexpected_shape"}
    from pyclaw.sessions import SessionStore
    store = SessionStore(ROOT / "history" / "sessions", ROOT / "history")
    index = store._load_index()
    existing = {row.get("id") for row in index.get("sessions", [])}
    migrated = 0
    items = list(rows.items())
    total = len(items)
    for i, (sid, old) in enumerate(items, 1):
        if progress:
            progress(i, total, "会话", sid)
        if not sid or sid in existing:
            continue
        events = []
        for msg in (old.get("messages") or []):
            role = str(msg.get("role") or "")
            content = msg.get("content") or ""
            if not content:
                continue
            if role == "user":
                events.append({"type": "user", "content": content})
            elif role == "assistant":
                events.append({"type": "assistant", "content": content})
            elif role == "tool":
                events.append({"type": "tool", "name": msg.get("tool_name") or msg.get("sender") or "exec",
                               "content": content})
        if not events:
            continue
        path = store.root / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in events) + "\n", encoding="utf-8")
        meta = old.get("metadata") or {}
        index["sessions"].append({
            "id": sid,
            "title": meta.get("name") or "",
            "created": old.get("created_at") or 0,
            "updated": old.get("last_active_at") or old.get("created_at") or 0,
        })
        migrated += 1
    if migrated:
        store.index = index
        store._write_index()
        try:
            mark.write_text(f"migrated {migrated} sessions\n", encoding="utf-8")
        except OSError:
            pass
        print(f"[MIGRATE] 旧会话 {migrated} 个 -> history/sessions", flush=True)
    return {"migrated": migrated, "checked": total}



def _num(value):
    """索引里的时间戳可能是数字、ISO 字符串或 "2026-11-10 20:10:56"，统一成 float。"""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except (TypeError, ValueError):
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text[:19], fmt).timestamp()
        except ValueError:
            continue
    return 0.0


def migrate_memory():
    """把旧版 pyclaw_memory.db 里的记忆搬进 memory/*.md（lite 会全文注入系统提示）。"""
    db = ROOT / "pyclaw_data" / "pyclaw_memory.db"
    mark = ROOT / "pyclaw_data" / ".memory_migrated"
    if not db.exists():
        return {"migrated": 0, "reason": "no_db"}
    if mark.exists():
        return {"migrated": 0, "reason": "already_migrated"}
    try:
        import sqlite3
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
        rows = con.execute("select * from memories").fetchall()
        con.close()
    except Exception as exc:
        return {"migrated": 0, "reason": f"sqlite_error: {exc}"}

    mem_dir = ROOT / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    migrated = 0
    for row in rows:
        try:
            key = (row["key"] or "").strip() or f"memory-{row['id']}"
            value = (row["value"] or "").strip()
        except (KeyError, TypeError):
            continue
        if not value:
            continue
        slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in key)[:48].strip("-") or f"legacy-{row['id']}"
        target = mem_dir / f"{slug}.md"
        if target.exists():
            continue
        stamp = row["updated_at"] or row["created_at"] or 0
        try:
            when = datetime.datetime.fromtimestamp(float(stamp)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            when = "unknown"
        body = (
            f"<!-- legacy memory id={row['id']} type={row['memory_type'] or ''} "
            f"importance={row['importance'] or 0} updated={when} -->\n"
            f"# {key}\n\n{value}\n"
        )
        try:
            target.write_text(body, encoding="utf-8")
            migrated += 1
        except OSError:
            continue
    if migrated:
        try:
            mark.write_text(f"migrated {migrated} memories\n", encoding="utf-8")
        except OSError:
            pass
        print(f"[MIGRATE] 旧记忆 {migrated} 条 -> memory/", flush=True)
    return {"migrated": migrated}


_STORE = {"s": None}


def get_store():
    """全局唯一 SessionStore。多个实例并发写索引会把删掉的行合并回来。"""
    from pyclaw.sessions import SessionStore
    if _STORE["s"] is None:
        _STORE["s"] = SessionStore(ROOT / "history" / "sessions", ROOT / "history")
    return _STORE["s"]


def repair_index():
    """把索引里没有对应 .jsonl 的幽灵行清掉。"""
    st = get_store()
    try:
        index = st._load_index()
    except Exception:
        return 0
    rows = index.get("sessions") or []
    keep = [row for row in rows if row.get("id") and (st.root / f"{row.get('id')}.jsonl").exists()]
    removed = len(rows) - len(keep)
    if removed:
        st.index = {"sessions": keep}
        st._write_index()
        print(f"[FIX] 清掉 {removed} 条幽灵会话", flush=True)
    return removed


def title_from_file(sid):
    """没有标题时，拿首条用户消息当名字，别让列表全是“未命名对话”。"""
    path = ROOT / "history" / "sessions" / f"{sid}.jsonl"
    if not path.exists():
        return ""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("type") == "user":
                text = " ".join(str(evt.get("content") or "").split())
                if text:
                    return text[:14]
    except OSError:
        pass
    return ""


def session_rows():
    """直接读会话索引：不构建 agent；顺手过滤掉没有文件的幽灵行。"""
    path = ROOT / "history" / "sessions" / "index.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for meta in (data.get("sessions") or []):
        if not isinstance(meta, dict) or meta.get("archived"):
            continue
        sid = meta.get("id")
        if not sid:
            continue
        fp = ROOT / "history" / "sessions" / f"{sid}.jsonl"
        if not fp.exists():
            continue
        name = clean_title(meta.get("title") or meta.get("name") or "")
        if not name:
            name = clean_title(title_from_file(sid)) or "旧会话"
        last = _num(meta.get("updated")) or _num(meta.get("created"))
        if not last:
            try:
                last = fp.stat().st_mtime
            except OSError:
                last = 0.0
        rows.append({
            "id": sid,
            "name": name,
            "msg_count": count_turns(fp),
            "last_active": last,
        })
    rows.sort(key=lambda r: r["last_active"], reverse=True)
    return rows


def clean_title(text):
    """把编码坏掉的标题（成片 ? 或 U+FFFD）滤掉，别在列表里丢人。"""
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    bad = text.count("?") + text.count("\ufffd")
    if bad and bad / max(len(text), 1) > 0.25:
        return ""
    return text[:60]


def count_turns(path):
    """数一下会话里有多少条 user/assistant 消息，给列表显示用。"""
    n = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"user"' in line or '"assistant"' in line:
                    n += 1
    except OSError:
        return 0
    return n


def history_of(agent):
    """把 lite 的事件流翻译成前端认识的消息结构。"""
    out = []
    try:
        events = list(agent.session.events())
    except Exception:
        return out
    for evt in events:
        kind = evt.get("type")
        if kind == "user":
            out.append({"type": "user", "content": evt.get("content", "")})
        elif kind == "assistant":
            out.append({"type": "assistant", "content": evt.get("content", "")})
        elif kind == "tool":
            out.append({"type": "tool", "tool": evt.get("name") or "exec",
                        "content": evt.get("content", "")})
    return out


# ── 后台热身 ──
async def _warmup():
    """启动层只等必要项；重活（供应商探测、插件扫描、会话预热）全部后台。"""
    try:
        boot(18, "config", "读取配置")
        get_config()

        boot(28, "legacy", "检查旧数据")
        try:
            await asyncio.to_thread(migrate_legacy)
        except Exception as exc:
            print(f"warning: 配置迁移失败: {exc}", flush=True)

        boot(40, "index", "整理会话索引")
        try:
            await asyncio.to_thread(repair_index)
        except Exception as exc:
            print(f"warning: 索引修复失败: {exc}", flush=True)

        boot(62, "session", "打开会话库")
        try:
            rows = await asyncio.to_thread(session_rows)
            print(f"[BOOT] 会话 {len(rows)} 个", flush=True)
        except Exception as exc:
            print(f"warning: 会话库读取失败: {exc}", flush=True)

        boot(100, "ready", "准备就绪")
        BOOT["done"] = True
        BOOT["elapsed"] = round(time.time() - BOOT["started_at"], 3)
        print(f"[BOOT] 启动完成，用时 {BOOT['elapsed']}s", flush=True)
    except Exception as exc:
        BOOT["error"] = str(exc)
        BOOT["done"] = True
        print(f"[BOOT] 启动失败: {exc}", flush=True)
        return

    async def _background():
        try:
            await asyncio.to_thread(_load_plugins)
            print("[BOOT] 插件扫描完成", flush=True)
        except Exception as exc:
            print(f"warning: 插件扫描失败: {exc}", flush=True)
        try:
            agent = await asyncio.to_thread(get_agent, "default")
            _ = agent.system_prompt()
            print("[BOOT] 默认会话预热完成", flush=True)
        except Exception as exc:
            print(f"warning: 预热会话失败: {exc}", flush=True)

    asyncio.create_task(_background())


async def _background_migrate():
    """迁移放到启动后台：前端可以边看进度条 + Tips 边等。"""
    MIGRATE.update(running=True, finished=False, done=0, total=0,
                   stage="准备", current="", error=None, started=time.time(),
                   sessions=0, memories=0)
    try:
        def progress(done, total, stage, current):
            migrate_tick(done, total, stage, current)

        def run_sessions():
            return migrate_sessions(progress=progress)

        MIGRATE["stage"] = "会话"
        rows = await asyncio.to_thread(run_sessions)
        MIGRATE["sessions"] = int(rows.get("migrated") or 0)
        MIGRATE["checked"] = int(rows.get("checked") or 0)

        MIGRATE["stage"] = "记忆"
        mem = await asyncio.to_thread(migrate_memory)
        MIGRATE["memories"] = int(mem.get("migrated") or 0)

        MIGRATE.update(stage="完成", current="", done=MIGRATE["total"] or 1,
                       total=MIGRATE["total"] or 1, finished=True, running=False,
                       elapsed=round(time.time() - MIGRATE["started"], 2))
        print(f"[MIGRATE] 完成：会话 {MIGRATE['sessions']} · 记忆 {MIGRATE['memories']}", flush=True)
    except Exception as exc:
        MIGRATE.update(running=False, finished=True, error=str(exc), stage="失败")
        print(f"warning: 后台迁移失败: {exc}", flush=True)


@asynccontextmanager
async def lifespan(app):
    global ACCESS_TOKEN
    boot(6, "boot", "启动进程")
    print(f"[BOOT] 进程到 lifespan: {time.time()-PROCESS_START:.2f}s", flush=True)
    # 这里只做最快的事：拿令牌。其余全部丢后台，端口先连上，
    # 否则 uvicorn 绑端口前就把活干完了，前端启动页只能看到 100%。
    token = str(cfg_get("WEBUI_TOKEN") or cfg_get("ACCESS_TOKEN") or "").strip()
    if not token:
        token = secrets.token_urlsafe(18)
        save_cfg(WEBUI_TOKEN=token)
        print(f"ACCESS_TOKEN={token}", flush=True)
        print("FIRST_CONNECT_HINT: 把这个令牌填进网页设置里", flush=True)
    ACCESS_TOKEN = token
    boot(10, "token", "校验令牌")
    asyncio.create_task(_warmup())
    asyncio.create_task(_background_migrate())
    print(f"[START] PyClaw(lite) WebUI 已启动 - {ROOT}", flush=True)
    yield
    for agent in list(AGENTS.values()):
        try:
            agent_mod.end_session(agent)
        except Exception:
            pass
    print("\n PyClaw 已停止", flush=True)


app = FastAPI(lifespan=lifespan)

LOGIN_HTML = (
    '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>PyClaw · 访问令牌</title>'
    '<meta name="viewport" content="width=device-width,initial-scale=1"><style>'
    'body{margin:0;min-height:100vh;display:grid;place-items:center;background:#16181d;color:#eef1f4;'
    'font-family:system-ui,-apple-system,"Segoe UI","PingFang SC",sans-serif}'
    '.card{width:min(360px,90vw);background:#22262e;border:1px solid rgba(255,255,255,.1);'
    'border-radius:16px;padding:26px}h1{font-size:16px;margin:0 0 6px}p{color:#aeb4bb;font-size:12.5px;'
    'margin:0 0 16px;line-height:1.6}input{width:100%;box-sizing:border-box;padding:10px;border-radius:9px;'
    'border:1px solid rgba(255,255,255,.12);background:#16181d;color:#eef1f4;font-size:14px;outline:0}'
    'button{width:100%;margin-top:12px;padding:10px;border:0;border-radius:9px;background:#3776AB;'
    'color:#fff;font-size:14px;cursor:pointer}button:hover{filter:brightness(1.08)}'
    '#err{color:#e0665a;font-size:12.5px;margin-top:10px;display:none}'
    '</style></head><body><div class="card"><h1>PyClaw · 访问令牌</h1>'
    '<p>服务端启动日志里的 WEBUI_TOKEN / ACCESS_TOKEN，填一次就记住。</p>'
    '<input id="tok" type="password" placeholder="访问令牌" autocomplete="off">'
    '<button onclick="go()">进入</button><div id="err">令牌不对，再试一次</div></div><script>'
    'function go(){var t=document.getElementById("tok").value.trim();if(!t)return;'
    'fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({token:t})}).then(function(r){if(r.ok){try{localStorage.setItem("pyclaw_access_token",t)}'
    'catch(e){}location.href="/"}else{document.getElementById("err").style.display="block"}})'
    '.catch(function(){document.getElementById("err").style.display="block"})}'
    'document.getElementById("tok").addEventListener("keydown",function(e){if(e.key==="Enter")go()});'
    '</script></body></html>'
)


@app.middleware("http")
async def token_gate(request: Request, call_next):
    if request.url.path in ("/login", "/api/config", "/api/plugins", "/api/skills", "/api/tools", "/api/plugins/toggle", "/api/migrate/status", "/api/data/clean_empty", "/api/data/clear_sessions", "/api/data/export", "/api/info", "/api/boot", "/api/balance", "/api/providers", "/api/models", "/api/keycheck", "/logo.svg", "/manifest.json", "/favicon.ico"):
        return await call_next(request)
    token = (request.cookies.get("pyclaw_token")
             or request.headers.get("X-Access-Token")
             or request.query_params.get("token") or "")
    if token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN):
        return await call_next(request)
    if request.url.path == "/":
        return HTMLResponse(LOGIN_HTML, status_code=401)
    return JSONResponse({"error": "unauthorized"}, status_code=401)


@app.post("/login")
async def login(request: Request):
    body = await request.body()
    try:
        data = json.loads(body or b"{}")
    except Exception:
        data = {}
    token = data.get("token") or request.query_params.get("token") or ""
    if not (token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN)):
        return JSONResponse({"error": "bad token"}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("pyclaw_token", token, max_age=60 * 60 * 24 * 30, httponly=False, samesite="lax")
    return resp


@app.post("/api/config")
async def api_config(request: Request):
    """保存运行参数：权限模式、思考强度、助手名称。"""
    body = await request.body()
    try:
        data = json.loads(body or b"{}")
    except Exception:
        data = {}
    patch = {}
    if data.get("approval") in ("request", "auto", "full"):
        patch["APPROVAL_MODE"] = data["approval"]
    if data.get("effort"):
        patch["REASONING_EFFORT"] = str(data["effort"])
    if data.get("agent_name"):
        patch["AGENT_NAME"] = str(data["agent_name"])[:40]
    if data.get("language") in ("zh-CN", "en-US"):
        patch["LANGUAGE"] = data["language"]
    if "sub_agents" in data:
        patch["SUB_AGENTS_ENABLED"] = bool(data["sub_agents"])
    if data.get("font_scale") is not None:
        try:
            patch["FONT_SCALE"] = max(0.8, min(1.4, float(data["font_scale"])))
        except (TypeError, ValueError):
            pass
    if patch:
        save_cfg(**patch)
        AGENTS.clear()
        # 光写文件不够：复用的 agent 里 session.effort 会盖过全局配置，
        # 不热更新的话界面显示“关”实际还在思考。
        base = _BASE_AGENT.get("agent")
        if base is not None:
            try:
                if patch.get("REASONING_EFFORT"):
                    base.session.set(effort=patch["REASONING_EFFORT"])
                if patch.get("APPROVAL_MODE"):
                    base.session.set(approval=patch["APPROVAL_MODE"])
                if patch.get("MODEL"):
                    base.provider.model = patch["MODEL"]
            except Exception as exc:
                print(f"warning: 配置热更新失败: {exc}", flush=True)
    return JSONResponse({"ok": True, "saved": patch})


@app.get("/api/migrate/status")
async def api_migrate_status():
    """后台迁移进度：前端启动之后就轮询这个，显示进度条与 Tips。"""
    payload = dict(MIGRATE)
    total = payload.get("total") or 0
    done = payload.get("done") or 0
    payload["percent"] = round(done / total * 100, 1) if total else (100.0 if payload.get("finished") else 0.0)
    payload["tips"] = MIGRATE_TIPS
    return JSONResponse(payload)


@app.post("/api/migrate")
async def api_migrate():
    return JSONResponse({"sessions": migrate_sessions(), "memory": migrate_memory(),
                         "legacy": _legacy_state()})


def _skill_rows():
    """从插件里汇总技能：name + 来源插件 + 描述。"""
    rows = []
    try:
        for plugin in _load_plugins():
            for skill in (getattr(plugin, "skills", None) or []):
                name = getattr(skill, "name", None) or (skill.get("name") if isinstance(skill, dict) else None)
                desc = getattr(skill, "description", None) or (skill.get("description") if isinstance(skill, dict) else "")
                if name:
                    rows.append({"name": str(name), "plugin": plugin.name, "description": str(desc or "")[:160]})
    except Exception as exc:
        print(f"warning: 技能清单失败: {exc}", flush=True)
    return rows


def _tool_rows():
    """内置 exec + 所有插件工具。"""
    rows = [{"name": "exec", "plugin": "kernel", "description": "执行 shell 命令"}]
    try:
        for plugin in _load_plugins():
            for tool in (getattr(plugin, "tools", None) or []):
                fn = tool.get("function") or {}
                if fn.get("name"):
                    rows.append({"name": fn["name"], "plugin": plugin.name,
                                 "description": str(fn.get("description") or "")[:160]})
    except Exception as exc:
        print(f"warning: 工具清单失败: {exc}", flush=True)
    return rows


@app.post("/api/data/clean_empty")
async def api_clean_empty():
    """删掉没有用户消息的空会话，不动有内容的。"""
    store = get_store()
    index = store._load_index()
    keep, removed = [], 0
    for row in index.get("sessions") or []:
        sid = row.get("id")
        if not sid:
            continue
        path = store.root / f"{sid}.jsonl"
        has_user = False
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:60]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except Exception:
                        continue
                    if evt.get("type") == "user" and str(evt.get("content") or "").strip():
                        has_user = True
                        break
            except OSError:
                pass
        if has_user:
            keep.append(row)
        else:
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                keep.append(row)
                continue
            removed += 1
    store.index = {"sessions": keep}
    store._write_index()
    AGENTS.clear()
    _BASE_AGENT["agent"] = None
    print(f"[DATA] 清掉空会话 {removed} 个", flush=True)
    return JSONResponse({"ok": True, "removed": removed, "left": len(keep)})


@app.post("/api/data/clear_sessions")
async def api_clear_sessions():
    """清空所有会话（不可恢复）。"""
    removed = 0
    try:
        index = ROOT / "history" / "sessions" / "index.json"
        root = ROOT / "history" / "sessions"
        if root.exists():
            for path in root.glob("*.jsonl"):
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
        if index.exists():
            try:
                index.write_text(json.dumps({"sessions": []}, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                pass
        AGENTS.clear()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:120]}, status_code=500)
    return JSONResponse({"ok": True, "removed": removed})


@app.get("/api/data/export")
async def api_export_sessions():
    """把全部会话导成一个 JSON 文件（浏览器下载）。"""
    from fastapi.responses import Response
    payload = {"exported_at": time.time(), "sessions": {}}
    root = ROOT / "history" / "sessions"
    if root.exists():
        for path in root.glob("*.jsonl"):
            try:
                rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
            except Exception:
                continue
            payload["sessions"][path.stem] = rows
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return Response(content=body, media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="pyclaw-sessions.json"'})


@app.post("/api/plugins/toggle")
async def api_plugin_toggle(request: Request):
    """启用/停用插件：写进 PLUGINS_ENABLED，重启后仍生效。"""
    body = await request.body()
    try:
        data = json.loads(body or b"{}")
    except Exception:
        data = {}
    name = str(data.get("name") or "").strip()
    if not name:
        return JSONResponse({"ok": False, "error": "missing name"}, status_code=400)
    want = bool(data.get("enabled", True))
    # pyclaw-lite 的语义：PLUGINS_ENABLED 里 "name" = 强制开启，"!name" = 强制关闭。
    # 旧实现把两者弄反了：点"停用"实际写的是 name，等于又开了一次。
    current = list(get_config().get("PLUGINS_ENABLED") or [])
    names = [n for n in current if str(n).lstrip("!") != name]
    names.append(name if want else "!" + name)
    save_cfg(PLUGINS_ENABLED=names)
    _PLUGIN_OBJECTS["items"] = []
    _PLUGIN_CACHE.update({"at": 0.0, "rows": []})
    AGENTS.clear()
    return JSONResponse({"ok": True, "name": name, "enabled": want, "PLUGINS_ENABLED": names})


@app.get("/api/skills")
async def api_skills():
    return JSONResponse({"skills": _skill_rows()})


@app.get("/api/tools")
async def api_tools():
    return JSONResponse({"tools": _tool_rows()})


@app.get("/api/plugins")
async def api_plugins():
    return JSONResponse({"plugins": _plugin_rows()})


@app.get("/api/info")
async def api_info():
    """给设置面板用的运行时信息。"""
    return JSONResponse({
        "root": str(ROOT),
        "kernel": "pyclaw-lite",
        "python": sys.version.split()[0],
        "config": str(ROOT / "pyclaw.json"),
        "model": str(cfg_get("MODEL") or ""),
        "provider": str(cfg_get("PROVIDER") or ""),
        "plugins": int(len(list((ROOT / "plugins").glob("*")))) if (ROOT / "plugins").exists() else 0,
        "sessions": len(session_rows()),
        "approval": str(cfg_get("APPROVAL_MODE") or "auto"),
        "effort": str(cfg_get("REASONING_EFFORT") or "high"),
        "agent_name": str(cfg_get("AGENT_NAME") or "PyClaw"),
        "legacy": _legacy_state(),
        "plugins": _plugin_rows(),
    })


@app.get("/api/boot")
async def api_boot():
    """启动状 + 迁移进度一次给全，前端只轮询这一个。"""
    payload = dict(BOOT)
    total = MIGRATE.get("total") or 0
    done = MIGRATE.get("done") or 0
    payload["migrate"] = dict(MIGRATE)
    payload["migrate"]["percent"] = round(done / total * 100, 1) if total else (
        100.0 if MIGRATE.get("finished") else 0.0)
    payload["migrate"]["tips"] = MIGRATE_TIPS
    payload["elapsed"] = round(time.time() - BOOT["started_at"], 3)
    return JSONResponse(payload)


@app.get("/api/providers")
async def api_providers():
    """供应商目录：前端不再硬编码。"""
    return JSONResponse({"providers": providers_catalog.public_list(),
                         "current": str(cfg_get("PROVIDER") or "deepseek"),
                         "model": str(cfg_get("MODEL") or ""),
                         "base": str(cfg_get("ENDPOINT") or ""),
                         "has_key": bool(str(cfg_get("API_KEY") or "").strip())})


@app.get("/api/models")
async def api_models(provider: str = "", base: str = "", key: str = ""):
    """后端代拉模型列表，避免浏览器跨域；失败回退目录预设。"""
    pid = provider or str(cfg_get("PROVIDER") or "deepseek")
    use_key = key.strip() or str(cfg_get("API_KEY") or "")
    result = providers_catalog.list_models(pid, use_key, base)
    result["provider"] = pid
    return JSONResponse(result)


@app.get("/api/balance")
async def api_balance(provider: str = ""):
    pid = provider or str(cfg_get("PROVIDER") or "")
    result = providers_catalog.balance(pid, str(cfg_get("API_KEY") or ""), str(cfg_get("ENDPOINT") or ""))
    return JSONResponse(result)


@app.get("/api/keycheck")
async def api_keycheck(provider: str = "", key: str = "", base: str = ""):
    """轻量校验：拿 /models 当探针，能列出来就算通。"""
    pid = provider or str(cfg_get("PROVIDER") or "deepseek")
    use_key = key.strip() or str(cfg_get("API_KEY") or "")
    result = providers_catalog.list_models(pid, use_key, base, timeout=6)
    return JSONResponse({"ok": bool(result.get("ok")), "error": result.get("error"),
                         "model_count": len(result.get("models") or []),
                         "sample": (result.get("models") or [])[:5]})

@app.get("/logo.svg")
async def serve_logo():
    from fastapi.responses import FileResponse
    path = ROOT / "logo.svg"
    if path.exists():
        return FileResponse(path, media_type="image/svg+xml")
    return JSONResponse({"error": "no logo"}, status_code=404)


@app.get("/sw.js")
async def service_worker():
    from fastapi.responses import Response
    return Response(content="self.addEventListener('install',()=>self.skipWaiting());", media_type="application/javascript")


@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/manifest.json")
async def manifest():
    return {"name": "PyClaw", "short_name": "PyClaw", "start_url": "/", "display": "standalone",
            "background_color": "#16181d", "theme_color": "#16181d"}


@app.get("/")
async def index():
    path = ROOT / "index.html"
    return HTMLResponse(path.read_text(encoding="utf-8"), media_type="text/html; charset=utf-8")


def _translate(evt, state):
    """lite 事件 → 前端消息。返回 (payload, 是否结束)。"""
    kind = evt.get("type")
    if kind == "delta":
        state["text"] += evt.get("text") or ""
        return {"type": "stream", "content": state["text"]}
    if kind == "reasoning":
        return {"type": "reasoning", "content": evt.get("text") or ""}
    if kind == "tool_call":
        return {"type": "tool_call", "tool": evt.get("command") or "exec", "params": ""}
    if kind == "tool_result":
        return {"type": "tool_result", "tool": "exec", "content": evt.get("text") or ""}
    if kind == "assistant":
        state["final"] = evt.get("text") or ""
        return None
    if kind == "error":
        return {"type": "final", "content": "错误：" + (evt.get("text") or "未知错误")}
    if kind == "notice":
        print(f"[notice] {evt.get('text')}", flush=True)
        return None
    if kind == "compact":
        return {"type": "compact_result", "content": f"上下文已压缩：{evt.get('before')} → {evt.get('after')} tokens"}
    if kind == "usage":
        state["usage"] = evt.get("usage") or {}
        return None
    return None


import threading

def safe_title(title, first_message):
    """兜底：空标题、超长标题回退到首句。内容是否得体交给模型审。"""
    text = (title or "").strip().strip("`").strip()
    if not text or len(text) > 12:
        fallback = " ".join((first_message or "").split())[:12]
        return fallback or "新对话"
    return text


REVIEW_PROMPT = (
    "你是会话标题审核。判断给定标题是否适合显示在公开界面："
    "要求中性、得体、无冒犯性、不是标题党。"
    "严格只输出一个 markdown 代码块，语言标记写成 text，块内只有 yes 或 no，不要任何多余的字。"
)


def _fenced_body(text):
    """从模型回答里取代码块内容；没有代码块就退回原文。"""
    match = re.search(r"```[a-zA-Z0-9_+\-]*[ \t]*\r?\n?(.*?)```", text or "", re.S)
    return (match.group(1) if match else (text or "")).strip()


def review_title(agent, title):
    """让模型自己审一遍标题，别把词表硬编码进代码。"""
    if not title:
        return False
    try:
        result = agent.provider.chat_with_retry(
            [{"role": "system", "content": REVIEW_PROMPT},
             {"role": "user", "content": title}],
            tools=None, effort="off", attempts=1)
        answer = _fenced_body(str(result.get("content") or "")).lower()
        return answer.startswith("yes")
    except Exception as exc:
        print(f"warning: 标题审核失败: {exc}", flush=True)
        return True


def generate_title(agent, user_text, assistant_text):
    """审核不过时重起标题：把真实一问一答给模型，让标题对齐事实。"""
    prompt = [
        {"role": "system", "content":
            "你是会话命名助手。根据下面这段真实的问答，起一个中性、得体、能概括主题的"
            "5 个字中文标题。严格只输出一个 markdown 代码块，语言标记写成 text，"
            "块内只有标题本身，不要标点，不要解释。"},
        {"role": "user", "content":
            "用户：" + (user_text or "")[:300] + "\n助手：" + (assistant_text or "")[:600]},
    ]
    result = agent.provider.chat_with_retry(prompt, tools=None, effort="off", attempts=1)
    return _fenced_body(str(result.get("content") or "")).strip()


RUNS = {}
CHAT_TASKS = {}


async def _run_chat(websocket, agent, text, sid, attachments=None):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    state = {"text": "", "final": "", "usage": {}}
    signal = threading.Event()
    RUNS[sid] = signal
    RUNS["__last__"] = signal
    # 思考关掉的时候，DeepSeek 还是会回传 reasoning，这里直接丢掉，省得前端自己判断
    hide_reasoning = str(cfg_get("REASONING_EFFORT") or "").lower() in ("off", "none", "minimal")

    def emit(evt):
        loop.call_soon_threadsafe(queue.put_nowait, evt)

    blocks = None
    if attachments:
        try:
            from pyclaw import plugins as plugins_mod
            ctx = {"config": get_config(), "session": agent.session, "root": ROOT, "agent": agent}
            collected = []
            for item in attachments:
                got = plugins_mod.transform_attachment(_load_plugins(), item, ctx)
                if got:
                    collected.extend(got)
            if collected:
                blocks = [{"type": "text", "text": text}] + collected
            print(f"[WS] attachments={len(attachments)} blocks={(len(collected) if collected else 0)}", flush=True)
        except Exception as exc:
            print(f"warning: 附件处理失败: {exc}", flush=True)

    def work():
        try:
            agent.run_turn(text, emit, signal=signal, content_blocks=blocks)
        except Exception as exc:
            emit({"type": "error", "text": str(exc)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    task = asyncio.create_task(asyncio.to_thread(work))
    while True:
        evt = await queue.get()
        if evt is None:
            break
        payload = _translate(evt, state)
        if payload and hide_reasoning and payload.get("type") in ("reasoning", "thinking"):
            payload = None
        if payload:
            try:
                await websocket.send_json(payload)
            except Exception:
                break
    try:
        await task
    except Exception:
        pass

    stopped = signal.is_set()
    final = state["final"] or state["text"]
    if stopped:
        await websocket.send_json({"type": "stopped", "partial": final})
        if final:
            await websocket.send_json({"type": "final", "content": final})
        RUNS.pop(sid, None)
        await websocket.send_json({"type": "session_id", "session_id": agent.session.id})
        await websocket.send_json({"type": "sessions_list", "sessions": session_rows()})
        return

    await websocket.send_json({"type": "final", "content": final or "（没有返回内容）"})

    try:
        if agent.session.turns() <= 2:
            title = safe_title(agent.make_title(), text)
            # 审核不过就带着真实对话内容重起，最多重来两次
            for _ in range(2):
                if title and review_title(agent, title):
                    break
                title = safe_title(generate_title(agent, text, final), text)
            if title:
                await websocket.send_json({"type": "session_name", "session_id": sid, "name": title})
    except Exception:
        pass

    await websocket.send_json({"type": "session_id", "session_id": agent.session.id})
    rows = session_rows()
    await websocket.send_json({"type": "sessions_list", "sessions": rows})


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token", "") or websocket.cookies.get("pyclaw_token", "")
    if not (token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN)):
        await websocket.close(code=4401)
        return
    await websocket.accept()

    sid = None
    try:
        while True:
            data = await websocket.receive_json()
            mtype = data.get("type", "chat")

            if mtype == "chat":
                sid = data.get("session_id") or "default"
                content = (data.get("content") or "").strip()
                if not content:
                    continue
                try:
                    agent = get_agent(sid)
                except Exception as exc:
                    await websocket.send_json({"type": "final", "content": f"错误：初始化失败 {exc}"})
                    continue
                # 别在这里 await：一旦阻塞，stop 消息就永远收不到
                attachments = data.get("attachments") or []
                task = asyncio.create_task(_run_chat(websocket, agent, content, sid, attachments))
                CHAT_TASKS[sid] = task
                continue

            if mtype == "history":
                sid = data.get("session_id") or "default"
                path = ROOT / "history" / "sessions" / f"{sid}.jsonl"
                if not path.exists():
                    # 别为了看历史就新建一个空会话文件，那是幽灵会话的源头
                    await websocket.send_json({"type": "history", "session_id": sid,
                                               "requested": sid, "messages": []})
                    continue
                try:
                    agent = get_agent(sid)
                    msgs = history_of(agent)
                    real_sid = agent.session.id
                except Exception:
                    msgs, real_sid = [], sid
                await websocket.send_json({"type": "history", "session_id": real_sid,
                                           "requested": sid, "messages": msgs})
                continue

            if mtype == "list_sessions":
                try:
                    repair_index()
                except Exception:
                    pass
                await websocket.send_json({"type": "sessions_list", "sessions": session_rows()})
                continue

            if mtype == "stop":
                target = data.get("session_id") or sid
                sig = RUNS.get(target) or RUNS.get("__last__")
                print(f"[WS] stop target={target!r} signal={sig is not None}", flush=True)
                if sig is not None:
                    sig.set()
                continue

            if mtype == "delete_session":
                target = data.get("session_id")
                print(f"[WS] delete_session target={target!r}", flush=True)
                try:
                    # 直接操作索引，别为删一条记录去构建整个 agent（那要十几秒）
                    store = get_store()
                    store.delete(target)
                    print(f"[WS] deleted, sessions now {len(session_rows())}", flush=True)
                    AGENTS.pop(target, None)
                    if _BASE_AGENT.get("agent") is not None and _BASE_AGENT["agent"].session.id == target:
                        _BASE_AGENT["agent"] = None
                    await websocket.send_json({"type": "session_deleted", "session_id": target})
                except Exception as exc:
                    print(f"warning: 删除会话失败: {exc}", flush=True)
                    await websocket.send_json({"type": "error", "content": f"删除失败: {exc}"})
                await websocket.send_json({"type": "sessions_list", "sessions": session_rows()})
                continue

            if mtype == "rename_session":
                target = data.get("session_id")
                name = (data.get("name") or "").strip()[:60]
                try:
                    store = get_store()
                    index = store._load_index()
                    hit = False
                    for row in index.get("sessions", []):
                        if row.get("id") == target:
                            row["title"] = name
                            hit = True
                            break
                    if hit:
                        store.index = index
                        store._write_index()
                    await websocket.send_json({"type": "session_renamed", "session_id": target, "name": name})
                except Exception as exc:
                    print(f"warning: 改名失败: {exc}", flush=True)
                    await websocket.send_json({"type": "error", "content": f"改名失败: {exc}"})
                await websocket.send_json({"type": "sessions_list", "sessions": session_rows()})
                continue

            if mtype == "set_config":
                patch = {}
                if data.get("api_key"):
                    patch["API_KEY"] = data["api_key"]
                if data.get("base_url"):
                    patch["ENDPOINT"] = data["base_url"]
                if data.get("model"):
                    patch["MODEL"] = data["model"]
                if data.get("provider"):
                    patch["PROVIDER"] = data["provider"]
                if data.get("approval") in ("request", "auto", "full"):
                    patch["APPROVAL_MODE"] = data["approval"]
                if data.get("effort"):
                    patch["REASONING_EFFORT"] = str(data["effort"])
                if data.get("agent_name"):
                    patch["AGENT_NAME"] = str(data["agent_name"])[:40]
                if patch:
                    save_cfg(**patch)
                    # effort/approval 不必重建 agent：写进 session，下一次请求就按新值走
                    base = _BASE_AGENT.get("agent")
                    if base is not None:
                        try:
                            if patch.get("REASONING_EFFORT"):
                                base.session.set(effort=patch["REASONING_EFFORT"])
                            if patch.get("APPROVAL_MODE"):
                                base.session.set(approval=patch["APPROVAL_MODE"])
                            if patch.get("MODEL"):
                                base.provider.model = patch["MODEL"]
                        except Exception as exc:
                            print(f"warning: 热更新失败: {exc}", flush=True)
                    AGENTS.clear()
                    _PLUGIN_OBJECTS["items"] = []
                await websocket.send_json({"type": "config_saved", "saved": patch})
                print(f"[TOOL] 配置已更新: {list(patch.keys())}", flush=True)
                continue

            if mtype == "migrate_sessions":
                result = migrate_sessions()
                await websocket.send_json({"type": "sessions_list", "sessions": session_rows()})
                print(f"[MIGRATE] {result}", flush=True)
                continue

            if mtype == "set_model":
                if data.get("model"):
                    save_cfg(MODEL=data["model"])
                    AGENTS.clear()
                continue

            if mtype == "compact":
                sid = data.get("session_id") or "default"
                try:
                    agent = get_agent(sid)
                    messages = agent.base_messages()
                    agent.compact(messages, agent.tool_schemas(), lambda e: None, force=True)
                    await websocket.send_json({"type": "compact_result", "content": "已压缩当前会话上下文"})
                except Exception as exc:
                    await websocket.send_json({"type": "compact_result", "content": f"压缩失败：{exc}"})
                continue

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"ERROR: ws loop: {exc}", flush=True)
    finally:
        if sid and sid in AGENTS:
            try:
                agent_mod.end_session(AGENTS[sid])
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="PyClaw WebUI (lite kernel)")
    parser.add_argument("--host", default=str(cfg_get("WEBUI_HOST", "127.0.0.1")))
    parser.add_argument("--port", type=int, default=int(cfg_get("PORT", 2469) or 2469))
    parser.add_argument("--allow-external", action="store_true")
    args = parser.parse_args()
    if args.allow_external and args.host in ("127.0.0.1", "localhost"):
        args.host = "0.0.0.0"
    _stop_splash()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
