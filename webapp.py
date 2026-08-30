#!/usr/bin/env python3
import sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Issue 1 fix: Windows GBK terminal emoji crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# 配置统一从 pyclaw.json 读取，不读取 .env

import asyncio, uuid, time, json, re, secrets, hmac
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pyclaw import Gateway
from pyclaw.pyclaw_types import Message, MessageRole
from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool, WebSearchTool, WebFetchTool
from pyclaw.agent import Agent, SubAgent, SubAgentManager
from pyclaw.subagent_tools import DelegateToTool, DelegateTmpTool
from pyclaw.cancel import registry
from pyclaw.runner import run_agent, EVT_THINKING, EVT_REASONING, EVT_STREAM, EVT_TOOL_CALL, EVT_TOOL_RESULT, EVT_AGENT_BUBBLE, EVT_FINAL, EVT_STOPPED, EVT_ERROR
from skills.workspace import WorkspaceSkill

gateway = None
ACCESS_TOKEN = ""

def load_api_config():
    """从 U 盘根目录的 volc_api.txt 读取火山引擎 API Key（跨平台)"""
    import glob as _glob
    
    possible_paths = [
        "../volc_api.txt",           # U 盘根目录 - 火山引擎（优先)
        "./volc_api.txt",            # 当前目录
        "/media/claw/_ز_/volc_api.txt",  # Linux 绝对路径
        "D:/volc_api.txt",           # Windows U盘 D 盘
        "E:/volc_api.txt",           # Windows U盘 E 盘
        "F:/volc_api.txt",           # Windows U盘 F 盘
        # 兼容旧版 DeepSeek
        "../API.txt",
        "./API.txt",
        "/media/claw/_ز_/API.txt",
        "D:/API.txt",
        "E:/API.txt",
        "F:/API.txt",
    ]
    
    # 首先尝试 glob 匹配 /media/*/API.txt (Linux 通用挂载点)
    try:
        for f in _glob.glob("/media/*/API.txt"):
            if f not in possible_paths:
                possible_paths.append(f)
    except Exception:
        pass
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
                    if api_key:
                        api_name = "火山引擎 API Key" if "volc" in path else "API Key"
                        print(f"✅ 已从 {path} 读取 {api_name}")
                        return api_key
            except (IOError, OSError):
                pass
    
    print("⚠️  未找到 volc_api.txt / API.txt，使用默认配置")
    return ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    global gateway
    api_key = load_api_config()
    data_dir = None
    if not data_dir:
        # 默认存储在 workspace 下，避免 U 盘空间爆满
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyclaw_data")
    
    os.makedirs(data_dir, exist_ok=True)
    print(f"📂 会话持久化目录: {data_dir}")

    # Issue 2 fix: default before config loop
    allowed_agents = None
    
    # 读取配置
    api_key = load_api_config()
    
    # Issue 5 fix: empty API key guidance
    if not api_key:
        print("")
        print("⚠️  未配置 API Key。PyClaw 将无法连接 LLM。")
        print()
        print("快速配置:")
        print("  1. 编辑 pyclaw.json（位于项目根目录）")
        print("  2. 填入以下内容:")
        print("     API_KEY=your_api_key_here")
        print("     ENDPOINT=https://api.example.com/v1")
        print("     MODEL=your-model")
        print("  3. 重启 PyClaw")
        print()
    
    # 从 pyclaw.json 读取配置（统一来源）
    lang = "zh-CN"
    sub_enabled = True
    for p in ["pyclaw.json", "../pyclaw.json", "API.txt", "../API.txt"]:
        if os.path.exists(p):
            try:
                if p.endswith(".json"):
                    import json
                    with open(p, encoding='utf-8') as f:
                        cfg = json.load(f)
                    lang = cfg.get("LANGUAGE", lang)
                    sub_enabled = cfg.get("SUB_AGENTS_ENABLED", True)
                    allowed_agents = cfg.get("SUB_AGENTS", None)
                    data_dir = cfg.get("DATA_DIR", data_dir)
                    if not api_key:
                        api_key = cfg.get("API_KEY", api_key)
                else:
                    with open(p, encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("LANGUAGE="):
                                lang = line.split("=", 1)[1].strip()
                            elif line.startswith("SUB_AGENTS_ENABLED="):
                                val = line.split("=", 1)[1].strip().lower()
                                sub_enabled = val in ("true", "1", "yes")
            except:
                pass
    
    # 配置统一写在 pyclaw.json，不写在 .env
    base_url = "https://opencode.ai/zen/v1"
    model = "deepseek-v4-flash-free"
    for p in ["pyclaw.json", "../pyclaw.json"]:
        if os.path.exists(p):
            try:
                with open(p, encoding='utf-8') as f:
                    cfg = json.load(f)
                base_url = cfg.get("ENDPOINT", base_url)
                model = cfg.get("MODEL", model)
            except:
                pass

    # 访问令牌：首次自动生成并写回 pyclaw.json（标准库 secrets/hmac，无新依赖）
    global ACCESS_TOKEN
    ACCESS_TOKEN = ""
    for _p in ["pyclaw.json", "../pyclaw.json"]:
        if os.path.exists(_p):
            try:
                with open(_p, encoding='utf-8') as _f:
                    _cfg = json.load(_f)
                ACCESS_TOKEN = _cfg.get("ACCESS_TOKEN", "") or ""
                if ACCESS_TOKEN:
                    break
            except Exception:
                pass
    if not ACCESS_TOKEN:
        ACCESS_TOKEN = secrets.token_urlsafe(24)
        try:
            for _p in ["pyclaw.json", "../pyclaw.json"]:
                if os.path.exists(_p):
                    with open(_p, encoding='utf-8') as _f:
                        _cfg = json.load(_f)
                    _cfg["ACCESS_TOKEN"] = ACCESS_TOKEN
                    with open(_p, "w", encoding='utf-8') as _f:
                        json.dump(_cfg, _f, ensure_ascii=False, indent=2)
                    break
        except Exception as _e:
            print("warning: cannot save token to pyclaw.json: %s" % _e)
    print("ACCESS_TOKEN=%s" % ACCESS_TOKEN, flush=True)
    print("FIRST_CONNECT_HINT: paste this token in the web settings", flush=True)

    gateway = Gateway(
        llm_api_key=api_key,
        storage_path=data_dir,
        base_url=base_url,
        model=model,
        language=lang
    )
    gateway.register_tool(FileReadTool())
    gateway.register_tool(ListDirTool())
    gateway.register_tool(ExecTool())
    gateway.register_tool(TimeTool())
    gateway.register_tool(WebSearchTool())
    gateway.register_tool(WebFetchTool())
    
    # 初始化多Agent协作系统
    sub_agent_manager = SubAgentManager(gateway.agent)
    print(f"✅ 多Agent协作系统已就绪 (exec + file)")
    
    # 将SubAgentManager存在gateway上以便系统提示词引用
    gateway.sub_agent_manager = sub_agent_manager
    gateway.sub_agents_enabled = sub_enabled  # @mention 子代理开关
    gateway.sub_agents_allowed = set(allowed_agents) if allowed_agents else None
    if gateway.sub_agents_allowed:
        print(f"  📌 允许的子代理: {', '.join(sorted(gateway.sub_agents_allowed))}")
    print(f"  📌 @mention 子代理: {'开启' if sub_enabled else '关闭'}")
    if sub_enabled:
        print(f"  🔧 关闭: 在 pyclaw.json 加 \"SUB_AGENTS_ENABLED\": false")
    
    # 注册 delegate_to / delegate_tmp 委派工具
    gateway.agent.register_tool(DelegateToTool(sub_agent_manager))
    gateway.agent.register_tool(DelegateTmpTool(sub_agent_manager))
    print(f"✅ 注册了 delegate_to / delegate_tmp 委派工具")
    
    # 注册 Workspace 工作空间管理工具
    workspace_skill = WorkspaceSkill()
    for tool in workspace_skill.get_tools():
        gateway.register_tool(tool)
    print(f"✅ 注册了 {len(workspace_skill.get_tools())} 个工作空间管理工具")
    
    # 异步初始化 Skill 系统
    await gateway.initialize_skills()
    
    # 检测本地 Ollama 服务
    try:
        import json, urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            if models:
                print(f"🦙 Ollama ({len(models)} 个模型): {', '.join(models)}")
            else:
                print("🦙 Ollama 已启动，尚未拉取模型")
    except Exception:
        pass
    
    # 后台自动保存会话（每30秒)
    async def autosave():
        while True:
            await asyncio.sleep(30)
            gateway.session_manager.flush()
    
    autosave_task = asyncio.create_task(autosave())
    
    print("🚀 PyClaw Web 版已启动 - 端口 2469")
    yield
    autosave_task.cancel()
    gateway.session_manager.flush()  # 最后刷盘
    print("\n👋 PyClaw 已停止")

app = FastAPI(lifespan=lifespan)

LOGIN_HTML = '<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>PyClaw - 访问令牌</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;width:340px;box-shadow:0 8px 24px rgba(0,0,0,.4)}h1{font-size:18px;margin:0 0 6px}p{color:#8b949e;font-size:13px;margin:0 0 16px}input{width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #30363d;background:#0d1117;color:#e6edf3;font-size:14px}button{width:100%;margin-top:12px;padding:10px;border:0;border-radius:8px;background:#238636;color:#fff;font-size:14px;cursor:pointer}button:hover{background:#2ea043}#err{color:#f85149;font-size:13px;margin-top:10px;display:none}</style></head><body><div class="card"><h1>🔑 PyClaw 访问令牌</h1><p>请输入服务端启动日志里的 ACCESS_TOKEN（pyclaw.json 中的值）。验证一次后会记住。</p><input id="tok" type="password" placeholder="访问令牌" autocomplete="off"><button onclick="go()">进入</button><div id="err">令牌错误，请检查后重试</div></div><script>function go(){var t=document.getElementById(\'tok\').value.trim();if(!t)return;fetch(\'/login\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({token:t})}).then(function(r){if(r.ok){try{localStorage.setItem(\'pyclaw_access_token\',t)}catch(e){}location.href=\'/\'}else{document.getElementById(\'err\').style.display=\'block\'}}).catch(function(){document.getElementById(\'err\').style.display=\'block\'})}document.getElementById(\'tok\').addEventListener(\'keydown\',function(e){if(e.key===\'Enter\')go()});</script></body></html>'

@app.middleware("http")
async def token_gate(request: Request, call_next):
    if request.url.path == "/login":
        return await call_next(request)
    token = request.cookies.get("pyclaw_token") or request.headers.get("X-Access-Token") or request.query_params.get("token") or ""
    if token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN):
        return await call_next(request)
    if request.url.path == "/":
        return HTMLResponse(LOGIN_HTML, status_code=401)
    return JSONResponse({"error": "unauthorized", "hint": "需要访问令牌"}, status_code=401)

@app.post("/login")
async def login(request: Request):
    import json as _json
    body = await request.body()
    try:
        data = _json.loads(body or b"{}")
    except Exception:
        data = {}
    token = data.get("token") or request.query_params.get("token") or ""
    if not (token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN)):
        return JSONResponse({"error": "bad token"}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("pyclaw_token", token, max_age=60*60*24*30, httponly=False, samesite="lax")
    return resp

@app.get("/logo.svg")
async def serve_logo():
    from fastapi.responses import FileResponse
    import os
    return FileResponse(os.path.join(os.path.dirname(__file__), "logo.svg"), media_type="image/svg+xml")

@app.get("/")
async def get():
    import os
    with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read(), media_type='text/html; charset=utf-8')

@app.get("/manifest.json")
async def manifest():
    return {
        "name": "PyClaw",
        "short_name": "PyClaw",
        "description": "AI assistant framework - built from scratch",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0d1117",
        "theme_color": "#0d1117",
        "orientation": "portrait",
        "icons": [
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'%3E%3Crect width='192' height='192' rx='38' fill='%230d1117'/%3E%3Ctext y='135' x='96' font-size='120' text-anchor='middle'%3E%F0%9F%A6%9E%3C/text%3E%3C/svg%3E",
                "sizes": "192x192",
                "type": "image/svg+xml"
            },
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Crect width='512' height='512' rx='80' fill='%230d1117'/%3E%3Ctext y='360' x='256' font-size='320' text-anchor='middle'%3E%F0%9F%A6%9E%3C/text%3E%3C/svg%3E",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }


@app.get("/sw.js")
async def service_worker():
    from fastapi.responses import Response
    return Response(
        content='''self.addEventListener("install",()=>{self.skipWaiting();console.log("PyClaw SW v2");});
self.addEventListener("activate",e=>{e.waitUntil(clients.claim());});
self.addEventListener("fetch",e=>e.respondWith(fetch(e.request).catch(()=>new Response("offline"))));''',
        media_type="application/javascript"
    )


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    # 全套 web 都需令牌：query token 优先，兼容 cookie
    token = websocket.query_params.get("token", "") or websocket.cookies.get("pyclaw_token", "")
    if not (token and ACCESS_TOKEN and hmac.compare_digest(token, ACCESS_TOKEN)):
        await websocket.close(code=4401)
        return
    await websocket.accept()
    
    # 发送工具+Skill列表给前端
    native_tool_names = {"read_file", "list_directory", "exec_command", "get_current_time", "web_search", "fetch_url"}
    native_tools = [name for name in gateway.agent.tools if name in native_tool_names]
    
    # 获取已安装的 Skill 列表
    from pyclaw.skill import skill_manager
    skills = skill_manager.list_all_skills()
    
    await websocket.send_json({
        "type": "tools_list",
        "native": sorted(native_tools),
        "skills": [s["name"] for s in skills]
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            # 处理不同类型的消息
            msg_type = data.get("type", "chat")
            
            if msg_type == "set_model":
                # 实时更新模型设置（向后兼容)
                new_model = data.get("model", "deepseek-v4-flash-free")
                gateway.agent.model = new_model
                # 也从 localStorage 拿 endpoint
                base_url = data.get("base_url") or data.get("endpoint")
                if base_url:
                    gateway.agent.base_url = base_url.rstrip("/")
                print(f"🤖 模型已切换为: {new_model}")
                continue

            if msg_type == "set_config":
                # 完整配置更新（供应商、API Key、端点、模型)
                provider = data.get("provider", "opencode-zen")
                api_key = data.get("api_key", "")
                base_url = data.get("base_url", "https://opencode.ai/zen/v1")
                model = data.get("model", "deepseek-v4-flash-free")
                mode = data.get("mode", gateway.agent.mode)
                max_rounds = data.get("max_rounds")
                
                # 更新最大轮数
                if max_rounds is not None and isinstance(max_rounds, (int, float)):
                    gateway.agent.max_rounds = max(10, min(999, int(max_rounds)))
                
                # 更新 agent 配置
                gateway.agent.reconfigure(
                    api_key=api_key if api_key else None,
                    base_url=base_url if base_url else None,
                    model=model if model else None,
                    mode=mode
                )
                
                # 持久化 API Key 到文件，防止重启丢失
                if api_key:
                    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "API.txt")
                    try:
                        with open(key_file, "w", encoding="utf-8") as f:
                            f.write(api_key)
                        print(f"💾 API Key 已保存到: {key_file}")
                    except Exception as e:
                        print(f"⚠️ 保存 API Key 失败: {e}")
                
                print(f"🔧 配置已更新: provider={provider}, model={model}, mode={mode}, endpoint={base_url}")
                continue
            
            if msg_type == "set_mode":
                mode = data.get("mode", "talk")
                gateway.agent.mode = mode
                print(f"🔄 模式已切换: {mode}")
                continue
            
            if msg_type == "set_thinking":
                enabled = data.get("enabled", False)
                effort = data.get("effort", "high")
                gateway.agent.thinking = enabled
                gateway.agent.reasoning_effort = effort
                gateway.agent._build_system_prompt(force=True)
                print(f"🧠 思考模式: {'开启' if enabled else '关闭'} (effort={effort})")
                continue
            
            if msg_type == "set_architecture":
                arch = data.get("architecture", "standard")
                gateway.architecture_mode = arch
                # 同步更新 sub_agents_allowed
                arch_map = {
                    "basic": set(),
                    "standard": {"exec", "file"},
                    "full": {"exec", "file", "search", "browser", "app"},
                }
                gateway.sub_agents_allowed = arch_map.get(arch, {"exec", "file"})
                allowed_str = ", ".join(sorted(gateway.sub_agents_allowed)) if gateway.sub_agents_allowed else "(none)"
                print(f"🤖 Agent 架构: {arch} (sub-agents: {allowed_str})")
                continue

            if msg_type == "compact":
                sid = data.get("session_id", "default")
                result = await gateway.compact_session(sid)
                await websocket.send_json({"type": "compact_result", "content": result})
                continue

            if msg_type == "stop":
                sid = data.get("session_id", "default")
                ok = registry.stop(sid)
                await websocket.send_json({
                    "type": "stop_ack",
                    "session_id": sid,
                    "ok": ok,
                })
                continue

            if msg_type == "list_sessions":
                _items = []
                for _sid in gateway.session_manager.list_sessions():
                    _s = gateway.session_manager.get(_sid)
                    if not _s:
                        continue
                    _items.append({
                        "id": _sid,
                        "name": (_s.metadata or {}).get("name", ""),
                        "msg_count": len(getattr(_s, "messages", []) or []),
                        "last_active": getattr(_s, "last_active_at", 0) or 0,
                    })
                _items.sort(key=lambda x: x["last_active"], reverse=True)
                await websocket.send_json({"type": "sessions_list", "sessions": _items})
                continue

            if msg_type == "delete_session":
                _sid = data.get("session_id")
                if _sid:
                    gateway.session_manager.delete_session(_sid)
                    gateway.session_manager.flush()
                continue

            if msg_type == "clear_sessions":
                for _sid in list(gateway.session_manager.list_sessions()):
                    gateway.session_manager.delete_session(_sid)
                gateway.session_manager.flush()
                continue

            if msg_type == "history":
                sid = data.get("session_id", "default")
                gateway.session_manager.get_or_create(sid)
                hist_msgs = []
                _tc_names = {}
                _tc_agents = {}
                for _m in gateway.session_manager.get_history(sid):
                    if _m.role == MessageRole.USER:
                        hist_msgs.append({"type": "user", "content": _m.content})
                    elif _m.role == MessageRole.ASSISTANT:
                        _sender = str(getattr(_m, "sender", "") or "")
                        _tcs = getattr(_m, "tool_calls", None) or []
                        if _sender.startswith("agent:"):
                            hist_msgs.append({"type": "agent", "content": _m.content, "agent": _sender.split(":", 1)[1]})
                        elif _tcs:
                            _disp = []
                            for _tc in _tcs:
                                _tid = _tc.get("id") if isinstance(_tc, dict) else getattr(_tc, "id", None)
                                if isinstance(_tc, dict):
                                    _fn = _tc.get("function") or {}
                                    _fname = str(_fn.get("name") or _tc.get("name") or "")
                                    _fargs = _fn.get("arguments") or _tc.get("arguments") or ""
                                else:
                                    _fname = str(getattr(_tc, "name", "") or "")
                                    _fargs = json.dumps(getattr(_tc, "arguments", {}) or {}, ensure_ascii=False)
                                _tc_names[_tid] = _fname
                                if _fname in ("delegate_to", "delegate_tmp"):
                                    try:
                                        _a = json.loads(_fargs) if isinstance(_fargs, str) else (_fargs or {})
                                    except Exception:
                                        _a = {}
                                    _tc_agents[_tid] = str(_a.get("agent") or _a.get("name") or "") or "exec"
                                else:
                                    _disp.append({"tool": _fname, "params": _fargs})
                            if _disp:
                                hist_msgs.append({"type": "assistant", "content": _m.content, "tool_calls": _disp})
                            elif _m.content and str(_m.content).strip():
                                hist_msgs.append({"type": "assistant", "content": _m.content})
                        else:
                            hist_msgs.append({"type": "assistant", "content": _m.content})
                    elif _m.role == MessageRole.TOOL:
                        _tid = getattr(_m, "tool_call_id", None)
                        if _tid in _tc_agents:
                            hist_msgs.append({"type": "agent", "content": _m.content, "agent": _tc_agents[_tid]})
                        else:
                            hist_msgs.append({"type": "tool", "tool": _tc_names.get(_tid, ""), "content": _m.content})
                await websocket.send_json({"type": "history", "session_id": sid, "messages": hist_msgs})
                continue

            # 普通聊天消息
            sid = data.get("session_id", "default")
            content = data.get("content", "")
            if not content.strip():
                continue

            # 任务在跑：真打断 —— stop 当前轮 + 把消息塞进历史 + 通知前端
            # runner 下次起新一轮时会读到这条 user 消息并优先处理
            if registry.is_running(sid):
                msg = Message(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    content=content,
                    sender="web_user",
                    role=MessageRole.USER,
                    timestamp=time.time(),
                    channel_id="web",
                    session_id=sid,
                )
                gateway.session_manager.add_message(sid, msg)
                gateway.session_manager.flush()
                # 关键：set stop_event 立刻停当前轮；runner 收尾后会起新轮
                # 拿到含本条 user 消息的 history
                registry.stop(sid)
                try:
                    await websocket.send_json({
                        "type": "interjected",
                        "content": content,
                        "interrupt": True,  # 标记是真打断，便于前端提示
                    })
                except Exception:
                    pass
                continue

            # 没在跑：开新一轮
            msg = Message(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                content=content,
                sender="web_user",
                role=MessageRole.USER,
                timestamp=time.time(),
                channel_id="web",
                session_id=sid,
            )
            gateway.session_manager.add_message(sid, msg)
            gateway.session_manager.flush()

            # 不阻塞 ws 循环 —— 后台跑
            stop_event = asyncio.Event()
            task = asyncio.create_task(_run_chat(websocket, sid, stop_event))
            registry.start(sid, task)
            # 把 stop_event 绑到 task 上方便 registry stop() 时能拿到
            task._pyclaw_stop = stop_event  # type: ignore[attr-defined]
    except WebSocketDisconnect:
        pass

async def _auto_name_session(websocket, session_id):
    """用 AI 给会话命名：标题严格输出到 ```text 代码块，只在第一轮调用"""
    try:
        history = gateway.session_manager.get_history(session_id)
        user_msgs = [m for m in history if hasattr(m, 'role') and str(m.role) in ('user', 'MessageRole.USER')]
        if not user_msgs:
            return
        first_msg = str(user_msgs[0].content).strip()
        if not first_msg:
            return

        title = ""
        # 1) AI 命名：要求严格只输出 ```text 代码块，块内只有标题
        try:
            raw = await gateway.agent.chat_direct(
                [
                    {"role": "system", "content": "你是会话标题命名助手。根据用户的第一条消息生成一个简洁的中文会话标题(必须恰好5个字)。严格只输出一个 markdown 代码块，语言标记为 text，代码块内只有标题本身，不要任何其他文字、解释或标点。"},
                    {"role": "user", "content": f"用户第一条消息：{first_msg[:200]}"},
                ],
                temperature=0,
                max_tokens=200,
            )
            raw = raw or ""
            # 优先取 ```text 代码块内容（未闭合也容忍）
            m = re.search(r"```text\s*\n(.*?)(?:```|$)", raw, re.S)
            if m:
                title = m.group(1).strip()
            # 部分模型可能用 ``` 无语言标记，兜底再试一次
            if not title:
                m2 = re.search(r"```[a-zA-Z]*\s*\n(.*?)(?:```|$)", raw, re.S)
                if m2:
                    title = m2.group(1).strip()
        except Exception as e:
            print(f"⚠️ AI 命名失败，降级为截断标题: {e}")

        # 清理：只留一行，去掉包裹符号；超长或为空则降级为截断标题
        title = re.sub(r"\s+", " ", title).strip(" `*_\"'\u201c\u201d\u2018\u2019\uff1a\u3002\uff0c\uff1b\uff01\uff1f:;.,!?")
        if not title or len(title) > 20:
            clean = re.sub(r'[?？!！。，,、\.。；;：:\s]+$', '', first_msg).strip()
            for pf in ['帮我', '请帮我', '请']:
                if clean.startswith(pf) and len(clean) > len(pf) + 2:
                    clean = clean[len(pf):]
            title = clean[:12].strip()

        if not title:
            return
        gateway.session_manager.set_session_name(session_id, title)
        gateway.session_manager.flush()
        await websocket.send_json({"type": "session_name", "name": title})
        print(f"📝 AI 会话命名: {title}")
    except Exception as e:
        print(f"⚠️ 命名失败: {e}")

async def process_chat(websocket, session_id):
    # 兼容旧调用（如果有），转发到 _run_chat
    await _run_chat(websocket, session_id, asyncio.Event())


async def _run_chat(websocket, session_id: str, stop_event: asyncio.Event):
    """消费 pyclaw.runner 的事件流，渲染到 websocket。
    接收 stop_event（外部置位会立刻优雅退出）。
    """
    try:
        # --- @mention 路由：直接交给子 Agent（保留旧行为） ---
        history = gateway.session_manager.get_history(session_id)
        if history:
            last_msg = history[-1]
            agent_match = re.match(r'^@(exec|file|search|browser|app)\s+(.+)', last_msg.content)
            if agent_match:
                await _run_mention(websocket, session_id, agent_match)
                return

        full_content = ""
        round_count = 0
        try:
            async for evt in run_agent(
                gateway.agent,
                gateway.session_manager,
                session_id,
                channel_id="web",
                stream=True,
                stop_event=stop_event,
            ):
                if stop_event.is_set() and evt.get("type") != EVT_STOPPED:
                    # 取消时不再派发后续事件
                    continue

                et = evt.get("type")
                if et == EVT_THINKING:
                    round_count = evt.get("round", round_count + 1)
                    await _safe_send(websocket, {
                        "type": "thinking",
                        "content": f"第 {evt['round']} 轮思考",
                    })
                elif et == EVT_REASONING:
                    await _safe_send(websocket, {
                        "type": "reasoning",
                        "content": evt["delta"],
                    })
                elif et == EVT_STREAM:
                    full_content += evt["delta"]
                    await _safe_send(websocket, {
                        "type": "stream",
                        "content": full_content,
                    })
                elif et == EVT_TOOL_CALL:
                    await _safe_send(websocket, {
                        "type": "tool_call",
                        "tool": evt["name"],
                        "params": json.dumps(evt["arguments"], ensure_ascii=False, indent=2),
                    })
                elif et == EVT_TOOL_RESULT:
                    await _safe_send(websocket, {
                        "type": "tool_result",
                        "tool": evt["name"],
                        "content": evt["content"] or "无返回内容",
                    })
                elif et == EVT_AGENT_BUBBLE:
                    await _safe_send(websocket, {
                        "type": "agent_final",
                        "agent": evt["agent"],
                        "content": evt["content"] or "（无返回内容)",
                    })
                elif et == EVT_FINAL:
                    await _safe_send(websocket, {
                        "type": "final",
                        "content": evt["content"] or (
                            "抱歉，我暂时无法回答这个问题。\n\n"
                            "💡 可能的原因：\n"
                            "   1. 问题描述不够清晰，请换个方式描述\n"
                            "   2. AI 输出被截断，请尝试简化问题\n"
                            "   3. 网络连接不稳定，请稍后重试\n"
                            "   4. 可以尝试使用工具先获取相关信息"
                        ),
                    })
                    if round_count == 1:
                        await _auto_name_session(websocket, session_id)
                elif et == EVT_STOPPED:
                    await _safe_send(websocket, {
                        "type": "stopped",
                        "partial": evt.get("partial", ""),
                        "reason": evt.get("reason", "user_requested"),
                    })
                elif et == EVT_ERROR:
                    await _safe_send(websocket, {
                        "type": "final",
                        "content": f"错误：{evt['message']}",
                    })
        finally:
            registry.finish(session_id)
    except WebSocketDisconnect:
        registry.finish(session_id)
    except Exception as e:
        print(f"❌ _run_chat error: {e}")
        try:
            await _safe_send(websocket, {"type": "final", "content": f"错误：{e}"})
        except Exception:
            pass
        registry.finish(session_id)


async def _safe_send(websocket, payload):
    try:
        await websocket.send_json(payload)
    except Exception:
        pass


async def _run_mention(websocket, session_id: str, agent_match):
    """@mention 路由：保留原 process_chat 中的子代理分支行为。"""
    agent_name = agent_match.group(1)
    task = agent_match.group(2)

    sub_mgr = getattr(gateway, 'sub_agent_manager', None)
    allowed = getattr(gateway, 'sub_agents_allowed', None)
    if allowed and agent_name not in allowed:
        await _safe_send(websocket, {
            "type": "agent_final",
            "agent": agent_name,
            "content": f"@{agent_name} not available (allowed: {', '.join(allowed)})"
        })
        return

    await _safe_send(websocket, {
        "type": "agent_thinking",
        "agent": agent_name,
        "content": f"@{agent_name} 正在处理..."
    })

    if sub_mgr:
        enabled = getattr(gateway, 'sub_agents_enabled', True)
        if not enabled:
            await _safe_send(websocket, {
                "type": "agent_final",
                "agent": agent_name,
                "content": f"@{agent_name} sub-agents disabled"
            })
            result = ""
        else:
            result = await sub_mgr.delegate(agent_name, task)
            await _safe_send(websocket, {
                "type": "agent_final",
                "agent": agent_name,
                "content": result or "（无返回内容)"
            })
        agent_msg = Message(
            id=f"agent_{uuid.uuid4().hex[:6]}",
            content=result or "",
            sender=f"agent:{agent_name}",
            role=MessageRole.ASSISTANT,
            timestamp=time.time(),
            channel_id="web",
            session_id=session_id,
        )
        gateway.session_manager.add_message(session_id, agent_msg)
        gateway.session_manager.flush()
    else:
        await _safe_send(websocket, {
            "type": "final",
            "content": "❌ 子 Agent 系统未初始化"
        })

if __name__ == "__main__":
    import argparse
    import uvicorn

    # 从 pyclaw.json 读取端口配置（比默认值优先）
    default_port = 2469
    for p in ["pyclaw.json", "../pyclaw.json"]:
        if os.path.exists(p):
            try:
                with open(p, encoding='utf-8') as f:
                    cfg = json.load(f)
                default_port = cfg.get("PORT", default_port)
            except:
                pass

    parser = argparse.ArgumentParser(description="PyClaw Web 服务")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="会话持久化存储目录（默认不持久化)。例: /home/claw/pyclaw_data")
    parser.add_argument("--port", type=int, default=default_port, help="监听端口")
    # 从环境变量获取默认 host 设置
    # 从 pyclaw.json 读取 ALLOW_EXTERNAL
    allow_external = os.environ.get("PYCLAW_ALLOW_EXTERNAL") == "1"
    if not allow_external:
        for p in ["pyclaw.json", "../pyclaw.json"]:
            if os.path.exists(p):
                try:
                    with open(p, encoding='utf-8') as f:
                        cfg = json.load(f)
                    allow_external = cfg.get("ALLOW_EXTERNAL", False)
                except:
                    pass
    default_host = "0.0.0.0" if allow_external else "127.0.0.1"
    parser.add_argument("--host", type=str, default=default_host, help="监听地址")
    args = parser.parse_args()

    if allow_external:
        print("⚠️ 已开放局域网访问，请确保已启用 WS 访问令牌（pyclaw.json 的 ACCESS_TOKEN）")
    else:
        print("🔒 默认仅本机访问 (127.0.0.1)")
        print("   开放局域网: pyclaw.json 设 ALLOW_EXTERNAL: true，或环境变量 PYCLAW_ALLOW_EXTERNAL=1（run.py --allow-external 等效）")
        print("   WS 访问令牌: pyclaw.json 的 ACCESS_TOKEN，网页设置里粘贴")

    if args.data_dir:
        # data_dir 覆盖暂未实现（计划外），留空避免 IndentationError
        pass

    uvicorn.run(app, host=args.host, port=args.port)
