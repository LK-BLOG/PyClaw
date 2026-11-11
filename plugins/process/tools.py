"""进程与端口工具（Windows/Linux/macOS 通用降级）。"""
import os, platform, subprocess

def _run(cmd):
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
        return (out.stdout or out.stderr).decode("utf-8", "replace")
    except Exception as exc:
        return f"执行失败: {exc}"

def list_processes(args, ctx=None):
    top = int(args.get("limit") or 30)
    if platform.system() == "Windows":
        raw = _run('tasklist /FO CSV /NH')
        rows = []
        for line in raw.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 5:
                mem = parts[4].replace(" K", "").replace(",", "").strip()
                try:
                    rows.append((int(mem), parts[0], parts[1]))
                except ValueError:
                    continue
        rows.sort(reverse=True)
        return "\n".join(f"{m:>10} K  pid={p}  {n}" for m, n, p in rows[:top]) or raw[:3000]
    raw = _run("ps aux --sort=-%mem | head -%d" % top)
    return raw or "(没有输出)"

def port_check(args, ctx=None):
    port = args.get("port")
    if not port:
        return "缺少 port"
    if platform.system() == "Windows":
        return _run(f'netstat -ano | findstr :{port}')
    return _run(f"lsof -i :{port} || ss -ltnp | grep :{port}")

def kill_process(args, ctx=None):
    pid = args.get("pid")
    if not pid:
        return "缺少 pid"
    if platform.system() == "Windows":
        return _run(f"taskkill /PID {int(pid)} /F")
    return _run(f"kill -9 {int(pid)}")

def register(ctx):
    ctx.add_tool("list_processes", "按内存占用列出进程", {
        "type": "object",
        "properties": {"limit": {"type": "integer"}},
        "required": []}, list_processes)
    ctx.add_tool("port_check", "查看某个端口被谁占用", {
        "type": "object",
        "properties": {"port": {"type": "integer"}},
        "required": ["port"]}, port_check)
    ctx.add_tool("kill_process", "结束一个进程（危险）", {
        "type": "object",
        "properties": {"pid": {"type": "integer"}},
        "required": ["pid"]}, kill_process)
