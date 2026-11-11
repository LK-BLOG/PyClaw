"""文件工具：读写、列目录、内容搜索。"""
import json, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def _safe(path):
    p = pathlib.Path(path).expanduser()
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()

def read_file(args, ctx=None):
    p = _safe(args.get("path", ""))
    if not p.exists():
        return f"文件不存在: {p}"
    if p.is_dir():
        return f"这是目录，请用 list_dir: {p}"
    limit = int(args.get("max_bytes") or 512 * 1024)
    data = p.read_bytes()[:limit]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", "replace")
    return text

def write_file(args, ctx=None):
    p = _safe(args.get("path", ""))
    body = args.get("content", "")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return f"已写入 {p}（{len(body)} 字符）"

def list_dir(args, ctx=None):
    p = _safe(args.get("path", "."))
    if not p.exists():
        return f"目录不存在: {p}"
    rows = []
    for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        try:
            size = item.stat().st_size
        except OSError:
            size = 0
        rows.append(f"{'DIR ' if item.is_dir() else 'FILE'} {item.name}  {size}")
        if len(rows) >= int(args.get("limit") or 200):
            break
    return "\n".join(rows) or "(空目录)"

def grep_files(args, ctx=None):
    pattern = args.get("pattern", "")
    target = _safe(args.get("path", "."))
    if not pattern:
        return "缺少 pattern"
    hits = []
    files = [target] if target.is_file() else target.rglob("*")
    for f in files:
        if not f.is_file() or f.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            for no, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if pattern in line:
                    hits.append(f"{f.relative_to(ROOT) if ROOT in f.parents else f}:{no}: {line.strip()[:160]}")
                    if len(hits) >= 80:
                        return "\n".join(hits) + "\n...(截断)"
        except OSError:
            continue
    return "\n".join(hits) or "没有匹配"

def register(ctx):
    ctx.add_tool("read_file", "读取一个文本文件的内容", {
        "type": "object",
        "properties": {"path": {"type": "string"}, "max_bytes": {"type": "integer"}},
        "required": ["path"]}, read_file)
    ctx.add_tool("write_file", "把内容写入文件（覆盖）", {
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"]}, write_file)
    ctx.add_tool("list_dir", "列出一个目录的内容", {
        "type": "object",
        "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}},
        "required": []}, list_dir)
    ctx.add_tool("grep_files", "在目录里按子串搜索文件内容", {
        "type": "object",
        "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}},
        "required": ["pattern"]}, grep_files)
