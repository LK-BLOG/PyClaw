#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, uuid, time, json, re
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pyclaw import Gateway
from pyclaw.pyclaw_types import Message, MessageRole, ToolDefinition, ToolResult
from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool, WebSearchTool, WebFetchTool
from pyclaw.agent import Agent, SubAgent, SubAgentManager
from skills.workspace import WorkspaceSkill

gateway = None

def load_api_config():
    """从 U 盘根目录的 volc_api.txt 读取火山引擎 API Key（跨平台）"""
    import glob as _glob
    
    possible_paths = [
        "../volc_api.txt",           # U 盘根目录 - 火山引擎（优先）
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
    data_dir = os.environ.get("PYCLAW_DATA_DIR")
    if not data_dir:
        # 默认存储在 workspace 下，避免 U 盘空间爆满
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyclaw_data")
    
    os.makedirs(data_dir, exist_ok=True)
    print(f"📂 会话持久化目录: {data_dir}")

    # 读取配置
    api_key = _load_api_key(data_dir)
    disabled_skills = set()
    api_txt = os.path.join(os.path.dirname(__file__), "API.txt")
    if os.path.exists(api_txt):
        with open(api_txt) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISABLED_SKILLS="):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        disabled_skills = set(s.strip() for s in parts[1].split(",") if s.strip())
                        break
    if disabled_skills:
        print(f"⚙️  已禁用的 Skill: {', '.join(sorted(disabled_skills))}")
    
    gateway = Gateway(
        llm_api_key=api_key,
        storage_path=data_dir,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-v4-flash",
        disabled_skills=disabled_skills
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
    
    # 注册 delegate_to 委派工具
    class DelegateTool:
        """委派任务给子代理"""
        def __init__(self, mgr):
            self.mgr = mgr
        @property
        def definition(self) -> ToolDefinition:
            return ToolDefinition(
                name="delegate_to",
                description="委派任务给子代理执行。exec:命令 file:文件 search:搜索 browser:浏览器 app:桌面",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "enum": ["exec", "file", "search", "browser", "app"],
                            "description": "目标子代理: exec(执行命令) file(文件) search(搜索) browser(浏览器) app(桌面)"
                        },
                        "task": {
                            "type": "string",
                            "description": "要委派的具体任务描述"
                        }
                    },
                    "required": ["agent", "task"]
                }
            )
        async def execute(self, params) -> ToolResult:
            agent = params.get("agent", "")
            task = params.get("task", "")
            if not agent or not task:
                return ToolResult(success=False, content="", error="需要 agent 和 task 参数")
            result = await self.mgr.delegate(agent, task)
            return ToolResult(success=True, content=str(result))
    
    gateway.agent.register_tool(DelegateTool(sub_agent_manager))
    print(f"✅ 注册了 delegate_to 委派工具")
    
    # 注册 Workspace 工作空间管理工具
    workspace_skill = WorkspaceSkill()
    for tool in workspace_skill.get_tools():
        gateway.register_tool(tool)
    print(f"✅ 注册了 {len(workspace_skill.get_tools())} 个工作空间管理工具")
    
    # 异步初始化 Skill 系统
    await gateway.initialize_skills()
    
    # 后台自动保存会话（每30秒）
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
        "description": "AI 助手框架 - 从零构建",
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
        content='''self.addEventListener("install",()=>self.skipWaiting());
self.addEventListener("activate",e=>e.waitUntil(clients.claim()));
self.addEventListener("fetch",e=>e.respondWith(fetch(e.request)));''',
        media_type="application/javascript"
    )


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
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
                # 实时更新模型设置（向后兼容）
                new_model = data.get("model", "deepseek-v4-flash")
                gateway.agent.model = new_model
                # 也从 localStorage 拿 endpoint
                base_url = data.get("base_url") or data.get("endpoint")
                if base_url:
                    gateway.agent.base_url = base_url.rstrip("/")
                print(f"🤖 模型已切换为: {new_model}")
                continue

            if msg_type == "set_config":
                # 完整配置更新（供应商、API Key、端点、模型）
                provider = data.get("provider", "deepseek")
                api_key = data.get("api_key", "")
                base_url = data.get("base_url", "https://api.deepseek.com/v1")
                model = data.get("model", "deepseek-v4-flash")
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
                print(f"🤖 Agent 架构: {arch}")
                continue
            
            # 普通聊天消息
            msg = Message(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                content=data.get("content", ""),
                sender="web_user",
                role=MessageRole.USER,
                timestamp=time.time(),
                channel_id="web",
                session_id=data.get("session_id", "default")
            )
            gateway.session_manager.add_message(msg.session_id, msg)
            await process_chat(websocket, msg.session_id)
    except WebSocketDisconnect:
        pass

async def _auto_name_session(websocket, session_id):
    """Generate session name from first user message"""
    try:
        history = gateway.session_manager.get_history(session_id)
        user_msgs = [m for m in history if hasattr(m,'role') and str(m.role) in ('user','MessageRole.USER')]
        if not user_msgs: return
        first_msg = str(user_msgs[0].content).strip()
        # Clean: remove trailing punctuation, take first meaningful segment
        clean = re.sub(r'[?？!！。，,\.。；;：:\s]+$', '', first_msg).strip()
        # Remove common prefixes like "帮我" / "请" for shorter title
        for pf in ['帮我', '请帮我', '请']:
            if clean.startswith(pf) and len(clean) > len(pf)+2:
                clean = clean[len(pf):]
        title = clean[:12]
        await websocket.send_json({"type": "session_name", "name": title})
        print(f"📝 会话命名: {title}")
    except Exception as e:
        print(f"⚠️ 命名失败: {e}")

async def process_chat(websocket, session_id):
    # 最大轮数限制（取 agent 配置，默认 300）
    max_turns = getattr(gateway.agent, 'max_rounds', 300)
    
    # --- @mention 路由：直接交给子 Agent ---
    history = gateway.session_manager.get_history(session_id)
    if history:
        last_msg = history[-1]
        agent_match = re.match(r'^@(exec|file|search|browser|app)\s+(.+)', last_msg.content)
        if agent_match:
            agent_name = agent_match.group(1)
            task = agent_match.group(2)
            
            await websocket.send_json({
                "type": "agent_thinking",
                "agent": agent_name,
                "content": f"@{agent_name} 正在处理..."
            })
            
            sub_mgr = getattr(gateway, 'sub_agent_manager', None)
            if sub_mgr:
                result = await sub_mgr.delegate(agent_name, task)
                await websocket.send_json({
                    "type": "agent_final",
                    "agent": agent_name,
                    "content": result or "（无返回内容）"
                })
                # 保存到历史
                agent_msg = Message(
                    id=f"agent_{uuid.uuid4().hex[:6]}",
                    content=result or "",
                    sender=f"agent:{agent_name}",
                    role=MessageRole.ASSISTANT,
                    timestamp=time.time(),
                    channel_id="web",
                    session_id=session_id
                )
                gateway.session_manager.add_message(session_id, agent_msg)
            else:
                await websocket.send_json({
                    "type": "final",
                    "content": f"❌ 子 Agent 系统未初始化"
                })
            return
    
    for turns in range(max_turns):
        history = gateway.session_manager.get_history(session_id)
        
        # 清理脏历史：删除最后一条没有 tool 响应的 assistant(tool_calls)
        cleaned = []
        i = 0
        while i < len(history):
            h = history[i]
            if h.role == MessageRole.ASSISTANT and h.tool_calls:
                # 检查后面有没有 tool 消息响应这些 tool_calls
                needed_ids = {tc.id if hasattr(tc, 'id') else tc.get('id', None) for tc in h.tool_calls}
                found_ids = set()
                for j in range(i + 1, len(history)):
                    if history[j].role == MessageRole.TOOL and history[j].tool_call_id in needed_ids:
                        found_ids.add(history[j].tool_call_id)
                if found_ids == needed_ids:
                    cleaned.append(h)
                else:
                    print(f"🧹 清理脏历史: 删除一条未完成的 tool_calls (缺失 {needed_ids - found_ids})")
                    # 跳过这个脏消息
            else:
                cleaned.append(h)
            i += 1
        if len(cleaned) != len(history):
            print(f"🧹 历史记录已清理: {len(history)} → {len(cleaned)}")
            history = cleaned
        
        await websocket.send_json({
            "type": "thinking",
            "content": f"第 {turns + 1} 轮思考"
        })
        
        # 使用流式聊天
        full_content = ""
        final_response = None
        async for chunk_response in gateway.agent.stream_chat(history):
            if chunk_response.success:
                # 推理内容推送
                if chunk_response.reasoning_content and not chunk_response.content:
                    await websocket.send_json({
                        "type": "reasoning",
                        "content": chunk_response.reasoning_content
                    })
                # 内容增量推送
                if chunk_response.content:
                    # 带工具调用/最终总结的chunk携带的是完整累积内容，增量已在前面推送过，避免重复累加
                    if not chunk_response.tool_calls:
                        full_content += chunk_response.content
                    await websocket.send_json({
                        "type": "stream",
                        "content": full_content
                    })
            else:
                await websocket.send_json({
                    "type": "final",
                    "content": f"错误：{chunk_response.error}"
                })
                return
            
            # 如果有工具调用，处理工具
            if chunk_response.tool_calls:
                final_response = chunk_response
                break
        
        # 保存最终的 assistant 消息（含 reasoning_content）
        assistant_msg = Message(
            id=f"assist_{uuid.uuid4().hex[:6]}",
            content=full_content,
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=time.time(),
            channel_id="web",
            session_id=session_id,
            tool_calls=[
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False)
                    }
                }
                for tc in final_response.tool_calls
            ] if (final_response and final_response.tool_calls) else None,
            reasoning_content=final_response.reasoning_content if (final_response and final_response.tool_calls) else None
        )
        gateway.session_manager.add_message(session_id, assistant_msg)
        
        if not (final_response and final_response.tool_calls):
            await websocket.send_json({
                "type": "final",
                "content": full_content or ("抱歉，我暂时无法回答这个问题。\n\n"
                    "💡 可能的原因：\n"
                    "   1. 问题描述不够清晰，请换个方式描述\n"
                    "   2. AI 输出被截断，请尝试简化问题\n"
                    "   3. 网络连接不稳定，请稍后重试\n"
                    "   4. 可以尝试使用工具先获取相关信息")
            })
            # Auto-name session after first exchange completes
            if turns == 0:
                print(f"🔤 开始命名会话 {session_id}...")
                await _auto_name_session(websocket, session_id)
            return
        
        # 通知前端 + 并行执行所有工具
        for tool_call in final_response.tool_calls:
            # delegate_to 是内部实现细节，不展示给用户
            if tool_call.name == "delegate_to":
                continue
            await websocket.send_json({
                "type": "tool_call",
                "tool": tool_call.name,
                "params": json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)
            })
        
        tasks = [gateway.agent.execute_tool(tc) for tc in final_response.tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 先收集 delegate_to 的结果统一发气泡，再发其他 tool_result
        agent_bubbles = []
        for tool_call, result in zip(final_response.tool_calls, results):
            if isinstance(result, Exception):
                result = f"工具执行异常: {str(result)}"
            
            if tool_call.name == "delegate_to":
                agent_name = tool_call.arguments.get("agent", "") if isinstance(tool_call.arguments, dict) else ""
                if agent_name in ("exec", "file", "search", "browser", "app"):
                    agent_bubbles.append((agent_name, result))
            else:
                await websocket.send_json({
                    "type": "tool_result",
                    "tool": tool_call.name,
                    "content": result or "无返回内容"
                })
            
            # 所有工具结果都必须保存到历史
            tool_msg = Message(
                id=f"tool_{uuid.uuid4().hex[:6]}",
                content=str(result) if result else "",
                sender="tool",
                role=MessageRole.TOOL,
                timestamp=time.time(),
                channel_id="web",
                session_id=session_id,
                tool_call_id=tool_call.id
            )
            gateway.session_manager.add_message(session_id, tool_msg)
        
        # 发 Agent 气泡（SubAgent 的 LLM 已格式化，不是 raw stdout）
        for agent_name, result in agent_bubbles:
            await websocket.send_json({
                "type": "agent_final",
                "agent": agent_name,
                "content": result or "（无返回内容）"
            })
        
        # Name session after first exchange (tool path)
        if turns == 0:
            print(f"🔤 开始命名会话(工具路径) {session_id}...")
            await _auto_name_session(websocket, session_id)
    
    await websocket.send_json({
        "type": "final",
        "content": "思考轮次超过限制，请换个方式提问。"
    })

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="PyClaw Web 服务")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="会话持久化存储目录（默认不持久化）。例: /home/claw/pyclaw_data")
    parser.add_argument("--port", type=int, default=2469, help="监听端口")
    # 从环境变量获取默认 host 设置
    default_host = "0.0.0.0" if os.environ.get('PYCLAW_ALLOW_EXTERNAL') == '1' else "127.0.0.1"
    parser.add_argument("--host", type=str, default=default_host, help="监听地址")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["PYCLAW_DATA_DIR"] = args.data_dir

    uvicorn.run(app, host=args.host, port=args.port)
