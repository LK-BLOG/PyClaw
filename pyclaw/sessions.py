"""Server-side session truth: an append-only event log per session plus an index."""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import uuid


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_jsonl(path):
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


class Session:
    def __init__(self, store, sid, meta=None):
        self.store = store
        self.id = sid
        self.meta = dict(meta or {})
        self.meta.setdefault("id", sid)
        self.meta.setdefault("title", "")
        self.meta.setdefault("created", _now())
        self.meta.setdefault("updated", self.meta["created"])
        self.meta.setdefault("archived", False)
        self.meta.setdefault("model", "")
        self.meta.setdefault("effort", "")
        self.meta.setdefault("approval", "")

    @property
    def path(self):
        return self.store.root / f"{self.id}.jsonl"

    def __getattr__(self, item):
        if item in ("title", "model", "effort", "approval", "archived", "created", "updated"):
            return self.meta.get(item)
        raise AttributeError(item)

    def events(self):
        return _read_jsonl(self.path)

    def append(self, event):
        event.setdefault("ts", _now())
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        if self.meta.get("updated") != event["ts"]:
            # The index only records the newest stamp, so rewriting it for every
            # single event is pure IO churn.
            self.meta["updated"] = event["ts"]
            self.store.save_index(self)
        return event

    def set(self, **fields):
        self.meta.update(fields)
        self.store.save_index(self)
        return self.meta

    def messages(self):
        """Model-facing replay: tool traffic from earlier turns is flattened to text."""
        out, pending = [], []
        fresh = True  # the first user message may follow a checkpoint
        for event in self.events():
            kind = event.get("type")
            if kind == "user":
                _flush(out, pending)
                _merge_user(out, event.get("content", ""), standalone=not fresh)
                fresh = True
            elif kind == "assistant":
                _flush(out, pending)
                message = {"role": "assistant", "content": event.get("content", "")}
                if event.get("reasoning"):
                    message["reasoning_content"] = event["reasoning"]
                out.append(message)
                fresh = True
            elif kind == "tool":
                pending.append(event)
            elif kind == "snapshot":
                _flush(out, pending)
                # Only the newest snapshot of each kind is worth sending; the
                # older ones are stale copies that only eat context.
                out.append({"role": "user", "content": event.get("content", ""),
                            "_snapshot": event.get("kind", "")})
                fresh = False
            elif kind == "compact":
                _flush(out, pending)
                out = [{"role": "user", "content": event.get("checkpoint", "")}]
                out.extend(_compact_tail(event.get("tail")))
                fresh = False
        _flush(out, pending)
        return _drop_stale_snapshots(out)

    def turns(self):
        count = 0
        for event in self.events():
            if event.get("type") == "user":
                count += 1
        return count

    def text_blob(self):
        return self.path.read_text(encoding="utf-8", errors="replace").lower() if self.path.exists() else ""


def _merge_user(out, content, standalone=False):
    """Two user messages in a row upset some APIs; fold them into one."""
    if not standalone and out and out[-1].get("role") == "user":
        previous = out[-1].get("content", "")
        if isinstance(previous, str) and isinstance(content, str):
            out[-1] = {"role": "user", "content": f"{previous}\n\n{content}"}
            return
    out.append({"role": "user", "content": content})


def _drop_stale_snapshots(out):
    """Keep only the newest snapshot of each kind."""
    latest = {}
    for index, message in enumerate(out):
        kind = message.get("_snapshot")
        if kind:
            latest[kind] = index
    kept = []
    for index, message in enumerate(out):
        kind = message.get("_snapshot")
        if kind and latest.get(kind) != index:
            continue
        kept.append({k: v for k, v in message.items() if not k.startswith("_") or k == "_standalone"})
    return kept


def _flush(out, pending):
    if not pending:
        return
    blocks = []
    for event in pending:
        command = event.get("command") or ""
        head = f"<tool name=\"{event.get('name', 'exec')}\">\n$ {command}\n{event.get('content', '')}\n</tool>"
        blocks.append(head)
    out.append({"role": "user", "content": "\n\n".join(blocks)})
    pending.clear()


def _sort_key(row):
    """Stable newest-first key: updated, then created, then id as the tiebreak.

    Sessions created inside the same second share an `updated` stamp, so the
    plain timestamp sort would fall back to insertion order.
    """
    return (row.get("updated") or "", row.get("created") or "", row.get("id") or "")


def _compact_tail(tail):
    """Replay the messages compaction kept. Old events have no tail field."""
    out = []
    for message in tail or []:
        if not isinstance(message, dict):
            continue
        role = message.get("role") or "user"
        content = message.get("content", "")
        if role not in ("user", "assistant"):
            # A tool result without its assistant call is an illegal sequence.
            role = "user"
        out.append({"role": role, "content": content})
    return out


class SessionStore:
    def __init__(self, root, legacy_root=None):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.json"
        self.legacy_root = pathlib.Path(legacy_root) if legacy_root else self.root.parent
        self.index = self._load_index()
        self.migrate_legacy()

    def _load_index(self):
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("sessions"), list):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"sessions": []}

    def _write_index(self):
        self.index_path.write_text(json.dumps(self.index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def save_index(self, session=None):
        # Merge with whatever is on disk: another process (or another surface) may
        # have written rows since this store was constructed. Overwriting from our
        # in-memory snapshot silently drops their sessions.
        merged = {}
        for row in self._load_index().get("sessions", []):
            if row.get("id"):
                merged[row["id"]] = row
        for row in self.index["sessions"]:
            if row.get("id"):
                merged.setdefault(row["id"], row)
        if session is not None:
            merged[session.id] = session.meta
        self.index["sessions"] = list(merged.values())
        self._write_index()

    def _meta(self, sid):
        for row in self.index["sessions"]:
            if row.get("id") == sid:
                return row
        # Another process may have written the row since this store was built.
        for row in self._load_index().get("sessions", []):
            if row.get("id") == sid:
                return row
        return None

    def get(self, sid):
        if not sid:
            return None
        meta = self._meta(sid)
        if meta is None and (self.root / f"{sid}.jsonl").exists():
            meta = {"id": sid, "title": "", "created": _now(), "updated": _now()}
            self.index["sessions"].append(meta)
            self._write_index()
        return Session(self, sid, meta) if meta else None

    def create(self, model="", effort="", approval=""):
        sid = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
        session = Session(self, sid, {"model": model, "effort": effort, "approval": approval})
        self.save_index(session)
        return session

    def list(self, include_archived=False, query=""):
        rows = []
        query = (query or "").strip().lower()
        for meta in self.index["sessions"]:
            if meta.get("archived") and not include_archived:
                continue
            if query:
                haystack = (meta.get("title", "") or "").lower()
                if query not in haystack:
                    session = self.get(meta["id"])
                    if not session or query not in session.text_blob():
                        continue
            rows.append(dict(meta))
        rows.sort(key=_sort_key, reverse=True)
        return rows

    def delete(self, sid):
        path = self.root / f"{sid}.jsonl"
        if path.exists():
            path.unlink()
        disk = self._load_index().get("sessions", [])
        self.index["sessions"] = [row for row in disk if row.get("id") != sid]
        for row in self.index["sessions"]:
            if row.get("id") == sid:
                self.index["sessions"].remove(row)
        self.index["sessions"] = [row for row in self.index["sessions"] if row.get("id") != sid]
        self._write_index()

    def latest(self):
        rows = self.list(include_archived=True)
        return self.get(rows[0]["id"]) if rows else None

    def migrate_legacy(self):
        """Old history/session_*.jsonl files become first-class sessions."""
        if not self.legacy_root.exists():
            return 0
        moved = 0
        for path in sorted(self.legacy_root.glob("session_*.jsonl")):
            sid = "legacy-" + re.sub(r"\D", "", path.stem)[:14]
            if self._meta(sid) or (self.root / f"{sid}.jsonl").exists():
                continue
            events, first = [], ""
            for entry in _read_jsonl(path):
                role = entry.get("role")
                content = entry.get("content", "")
                if role == "user":
                    first = first or content
                    events.append({"type": "user", "content": content, "ts": entry.get("ts", _now())})
                elif role == "assistant":
                    events.append({"type": "assistant", "content": content, "ts": entry.get("ts", _now())})
                elif role == "exec":
                    events.append({"type": "tool", "name": "exec", "command": content,
                                   "content": "", "ts": entry.get("ts", _now())})
                elif role == "tool":
                    events.append({"type": "tool", "name": "exec", "command": "",
                                   "content": content, "ts": entry.get("ts", _now())})
            target = self.root / f"{sid}.jsonl"
            target.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
            session = Session(self, sid, {"title": first[:12] or path.stem, "created": _now(),
                                          "updated": _now(), "migrated_from": path.name})
            self.save_index(session)
            moved += 1
        return moved


def title_prompt(first_message):
    return [
        {"role": "system", "content":
            "You name chat sessions. Reply with exactly one markdown code block tagged text "
            "containing a neutral 5-character Chinese title describing the topic. "
            "Use plain everyday words. Never use vulgar, sexual, violent or clickbait wording. "
            "Nothing else, no punctuation, no explanation."},
        {"role": "user", "content": f"First message: {first_message[:200]}"},
    ]


FENCE = re.compile(r"```([a-zA-Z0-9_+\-]*)[ \t]*\r?\n?(.*?)```", re.S)
# Code-ish punctuation: a title never carries it, a fenced snippet always does.
CODE_CHARS = set("(){}[]<>=;|&\\")


def _fenced_title(raw):
    """Pull the title out of the code block the model was asked for.

    Single-line fences (```text Title``` / ```Title```) count as well as the
    multi-line form. The block has to be the whole answer: a stray fence
    inside prose or a fenced snippet is never treated as the title.
    """
    raw = raw or ""
    for match in FENCE.finditer(raw):
        tag = (match.group(1) or "").lower()
        if tag not in ("", "text"):
            continue
        before = raw[:match.start()].strip()
        after = raw[match.end():].strip().strip("` \t*_。，,.!！?？")
        if before or after:
            continue
        body = match.group(2).strip()
        if not body or "\n" in body:
            continue
        if any(ch in CODE_CHARS for ch in body):
            continue
        return body
    return ""


def parse_title(raw, fallback):
    title = re.sub(r"\s+", " ", _fenced_title(raw)).strip(" `*_\"'：。，；！？:;.,!?")
    if not title or len(title) > 20:
        clean = re.sub(r"[?？!！。，,、.；;：:\s]+$", "", (fallback or "").strip())
        for prefix in ("帮我", "请帮我", "请"):
            if clean.startswith(prefix) and len(clean) > len(prefix) + 2:
                clean = clean[len(prefix):]
        title = clean[:12].strip()
    return title
