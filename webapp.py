#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, uuid, time, json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pyclaw import Gateway
from pyclaw.pyclaw_types import Message, MessageRole
from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool
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
    except:
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
            except:
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

    gateway = Gateway(
        llm_api_key=api_key,
        storage_path=data_dir,
        base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
        model="ark-code-latest"
    )
    gateway.register_tool(FileReadTool())
    gateway.register_tool(ListDirTool())
    gateway.register_tool(ExecTool())
    gateway.register_tool(TimeTool())
    
    # 注册 Workspace 工作空间管理工具
    workspace_skill = WorkspaceSkill()
    for tool in workspace_skill.get_tools():
        gateway.register_tool(tool)
    print(f"✅ 注册了 {len(workspace_skill.get_tools())} 个工作空间管理工具")
    
    # 异步初始化 Skill 系统
    await gateway.initialize_skills()
    
    print("🚀<img src='/logo.svg' width='24' height='24' style='vertical-align:middle;margin-right:8px;margin-top:-2px'/> PyClaw Web 版已启动 - 端口 2469")
    yield
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
                    gateway.agent.base_url = base_url
                print(f"🤖 模型已切换为: {new_model}")
                continue

            if msg_type == "set_config":
                # 完整配置更新（供应商、API Key、端点、模型）
                provider = data.get("provider", "deepseek")
                api_key = data.get("api_key", "")
                base_url = data.get("base_url", "https://api.deepseek.com/v1")
                model = data.get("model", "deepseek-v4-flash")
                
                # 更新 agent 配置
                gateway.agent.reconfigure(
                    api_key=api_key if api_key else None,
                    base_url=base_url if base_url else None,
                    model=model if model else None
                )
                print(f"🔧 配置已更新: provider={provider}, model={model}, endpoint={base_url}")
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

async def process_chat(websocket, session_id):
    # 🔧 限制最大轮数，避免消息风暴导致浏览器卡死
    max_turns = 20
    last_tools = []  # 检测重复工具调用
    
    for turns in range(max_turns):
        history = gateway.session_manager.get_history(session_id)
        
        await websocket.send_json({
            "type": "thinking",
            "content": f"第 {turns + 1} 轮思考"
        })
        
        # 使用流式聊天
        full_content = ""
        final_response = None
        async for chunk_response in gateway.agent.stream_chat(history):
            if chunk_response.success:
                full_content = chunk_response.content
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
        
        # 保存最终的 assistant 消息
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
            ] if (final_response and final_response.tool_calls) else None
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
            return
        
        for tool_call in final_response.tool_calls:
            await websocket.send_json({
                "type": "tool_call",
                "tool": tool_call.name,
                "params": json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)
            })
            
            result = await gateway.agent.execute_tool(tool_call)
            
            await websocket.send_json({
                "type": "tool_result",
                "tool": tool_call.name,
                "content": result or "无返回内容"
            })
            
            tool_msg = Message(
                id=f"tool_{uuid.uuid4().hex[:6]}",
                content=result or "",
                sender="tool",
                role=MessageRole.TOOL,
                timestamp=time.time(),
                channel_id="web",
                session_id=session_id,
                tool_call_id=tool_call.id
            )
            gateway.session_manager.add_message(session_id, tool_msg)
    
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
