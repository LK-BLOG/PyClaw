"""时间工具。"""
import datetime, time as _time

def now(args, ctx=None):
    tz = args.get("timezone") or "Asia/Shanghai"
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.datetime.now(ZoneInfo(tz))
    except Exception:
        dt = datetime.datetime.now()
        tz = "local"
    return dt.strftime(f"%Y-%m-%d %H:%M:%S %A ({tz})")

def from_ts(args, ctx=None):
    try:
        ts = float(args.get("timestamp") or _time.time())
    except (TypeError, ValueError):
        return "timestamp 不是数字"
    if ts > 1e12:
        ts /= 1000.0
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def register(ctx):
    ctx.add_tool("now", "获取当前日期时间", {
        "type": "object",
        "properties": {"timezone": {"type": "string"}},
        "required": []}, now)
    ctx.add_tool("from_timestamp", "把 Unix 时间戳换成可读时间", {
        "type": "object",
        "properties": {"timestamp": {"type": "number"}},
        "required": ["timestamp"]}, from_ts)
