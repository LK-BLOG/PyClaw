"""记忆工具：读写 memory/ 下的 markdown。"""
import datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
MEM = ROOT / "memory"

def memory_write(args, ctx=None):
    key = (args.get("key") or "notes").strip().replace("/", "_").replace("\\", "_")
    text = (args.get("text") or "").strip()
    if not text:
        return "缺少 text"
    MEM.mkdir(exist_ok=True)
    path = MEM / f"{key}.md"
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- [{stamp}] {text}\n")
    return f"已记到 {path.relative_to(ROOT)}"

def memory_read(args, ctx=None):
    key = (args.get("key") or "").strip()
    MEM.mkdir(exist_ok=True)
    if key:
        path = MEM / f"{key}.md"
        return path.read_text(encoding="utf-8") if path.exists() else "这条记忆还没有"
    out = []
    for path in sorted(MEM.glob("*.md")):
        out.append(f"== {path.name} ==\n{path.read_text(encoding='utf-8')[:2000]}")
    return "\n\n".join(out) or "(还没有记忆)"

def register(ctx):
    ctx.add_tool("memory_write", "把一条持久事实写入长期记忆", {
        "type": "object",
        "properties": {"key": {"type": "string"}, "text": {"type": "string"}},
        "required": ["text"]}, memory_write)
    ctx.add_tool("memory_read", "读取长期记忆（不传 key 就全读）", {
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": []}, memory_read)
