#!/usr/bin/env python3
import asyncio, uuid, time, json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pyclaw import Gateway
from pyclaw.types import Message, MessageRole
from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool

gateway = None

def load_api_config():
    """从 U 盘根目录的 API.txt 读取 API Key"""
    # 尝试从多个可能的位置读取
    possible_paths = [
        "../API.txt",           # U 盘根目录（相对路径）
        "./API.txt",            # 当前目录
        "/media/claw/_ز_/API.txt",  # 绝对路径
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
                    if api_key:
                        print(f"✅ 已从 {path} 读取 API Key")
                        return api_key
            except:
                pass
    
    print("⚠️  未找到 API.txt，使用默认配置")
    return ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    global gateway
    api_key = load_api_config()
    gateway = Gateway(
        llm_api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )
    gateway.register_tool(FileReadTool())
    gateway.register_tool(ListDirTool())
    gateway.register_tool(ExecTool())
    gateway.register_tool(TimeTool())
    
    # 异步初始化 Skill 系统
    await gateway.initialize_skills()
    
    print("🚀 PyClaw Web 版已启动 - 端口 2469")
    yield
    print("\n👋 PyClaw 已停止")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def get():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PyClaw</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; height: 100vh; display: flex; }
        .sidebar { width: 260px; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px 16px; border-bottom: 1px solid #30363d; font-size: 18px; font-weight: 600; color: #58a6ff; }
        .nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 14px; margin: 2px 8px; }
        .nav-item:hover { background: #21262d; }
        .nav-item.active { background: #21262d; color: #58a6ff; }
        .main { flex: 1; display: flex; flex-direction: column; }
        .chat-header { padding: 16px 24px; border-bottom: 1px solid #30363d; background: #161b22; font-size: 16px; font-weight: 600; }
        .messages { flex: 1; overflow-y: auto; padding: 24px; display: block; }
        .settings-panel { flex: 1; overflow-y: auto; padding: 24px; display: none; }
        .msg-wrap { max-width: 850px; margin: 0 auto 16px auto; }
        .msg-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: #8b949e; }
        .msg-header .avatar { width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; }
        .msg-header .avatar.user { background: linear-gradient(135deg, #58a6ff, #8b5cf6); }
        .msg-header .avatar.assistant { background: #238636; }
        .msg { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
        .msg.user { background: #1f6feb22; border-color: #1f6feb44; }
        .step { max-width: 850px; margin: 0 auto 8px auto; padding: 10px 14px; border-radius: 6px; font-size: 12px; font-family: monospace; border-left: 3px solid; }
        .step.thinking { background: #1a1f26; border-color: #58a6ff; color: #58a6ff; }
        .step.tool { background: #262110; border-color: #d29922; color: #d29922; }
        .step.result { background: #0f2918; border-color: #238636; color: #3fb950; }
        .input-area { padding: 16px 24px 24px 24px; background: #161b22; border-top: 1px solid #30363d; }
        .input-wrap { max-width: 850px; margin: 0 auto; position: relative; }
        #input { width: 100%; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px 100px 12px 16px; color: #e6edf3; font-size: 14px; outline: none; }
        button { position: absolute; right: 8px; bottom: 6px; background: #238636; color: white; border: none; border-radius: 6px; padding: 7px 16px; cursor: pointer; }
        .welcome { max-width: 850px; margin: 0 auto; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; text-align: center; }
        .examples { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
        .example { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: left; cursor: pointer; font-size: 13px; }
        .example:hover { border-color: #58a6ff; }
        .tools { padding: 16px; font-size: 12px; }
        .tool-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: #8b949e; }
        .card { max-width: 600px; margin: 0 auto 16px auto; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; }
        .card-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #30363d; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">🦞 PyClaw</div>
        <div style="padding: 8px 0;">
            <div class="nav-item active" id="nav-chat" onclick="switchTab('chat')"><span>💬</span><span>聊天</span></div>
            <div class="nav-item" id="nav-settings" onclick="switchTab('settings')"><span>⚙️</span><span>设置</span></div>
        </div>
        <div class="tools">
            <div style="font-weight: 600; margin-bottom: 8px; color: #e6edf3;">工具列表</div>
            <div class="tool-item">📁 目录浏览</div>
            <div class="tool-item">📄 文件读取</div>
            <div class="tool-item">💻 命令执行</div>
            <div class="tool-item">⏰ 时间查询</div>
        </div>
    </div>
    <div class="main">
        <div class="chat-header" id="header-title">🧠 Agent Chat</div>
        <div class="messages" id="messages">
            <div class="welcome">
                <div style="font-size: 48px; margin-bottom: 16px;">🦞</div>
                <div style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">欢迎使用 PyClaw</div>
                <div style="color: #8b949e; margin-bottom: 16px;">从零构建的 AI 助手框架</div>
                <div class="examples">
                    <div class="example" onclick="send('看看当前目录有什么')">📁 列出目录内容</div>
                    <div class="example" onclick="send('读取 README.md 文件')">📄 读取文件</div>
                    <div class="example" onclick="send('执行 pwd 命令')">💻 执行命令</div>
                    <div class="example" onclick="send('现在北京时间几点了')">⏰ 查询时间</div>
                </div>
            </div>
        </div>
        <div class="settings-panel" id="settings-panel">
            <div class="card">
                <div class="card-title">🧹 对话管理</div>
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 13px; color: #8b949e; margin-bottom: 8px;">当前会话ID: <code id="session-id-display" style="background: #0d1117; padding: 2px 6px; border-radius: 4px;">-</code></div>
                    <button onclick="newSession()" style="width: 100%; max-width: 200px; background: #238636; color: white; border: none; border-radius: 6px; padding: 8px 14px; cursor: pointer; font-size: 13px;">➕ 开启新会话</button>
                </div>
                <div>
                    <div style="font-size: 13px; color: #8b949e; margin-bottom: 10px;">会话列表</div>
                    <div id="session-list" style="max-height: 300px; overflow-y: auto;"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">🤖 模型设置</div>
                <div style="font-size: 14px; color: #8b949e; line-height: 1.8;">
                    <div><strong style="color: #e6edf3;">模型:</strong> DeepSeek Chat</div>
                    <div><strong style="color: #e6edf3;">Endpoint:</strong> https://api.deepseek.com/v1</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">📦 关于</div>
                <div style="font-size: 14px; color: #8b949e; line-height: 1.8;">
                    <div>🦞 <strong style="color: #e6edf3;">PyClaw</strong></div>
                    <div>版本: 0.1.0</div>
                    <div>作者: 骆戡</div>
                    <div style="margin-top: 12px;">参考 OpenClaw 设计理念，从零构建的 AI 助手框架</div>
                </div>
            </div>
        </div>
        <div class="input-area" id="input-area">
            <div class="input-wrap">
                <input id="input" placeholder="输入消息..." autocomplete="off">
                <button onclick="sendMsg()">发送</button>
            </div>
        </div>
    </div>
    <script>
        const msgs = document.getElementById('messages');
        const input = document.getElementById('input');
        
        // 从 localStorage 读取会话ID，没有则创建新的
        let sessionId = localStorage.getItem('pyclaw_session_id');
        if (!sessionId) {
            sessionId = 'web_' + Math.random().toString(36).slice(2, 10);
            localStorage.setItem('pyclaw_session_id', sessionId);
        }
        console.log('当前会话ID:', sessionId);
        
        const ws = new WebSocket('ws://' + window.location.host + '/ws');
        
        // 保存当前会话到列表
        saveSessionToList(sessionId);

        // 连接建立后恢复历史
        ws.onopen = () => {
            console.log('WebSocket 已连接，恢复对话历史...');
            document.getElementById('session-id-display').textContent = sessionId;
            restoreHistory();
            renderSessionList();
        };

        function switchTab(tab) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById('nav-' + tab).classList.add('active');
            if (tab === 'chat') {
                document.getElementById('header-title').textContent = '🧠 Agent Chat';
                msgs.style.display = 'block';
                document.getElementById('input-area').style.display = 'block';
                document.getElementById('settings-panel').style.display = 'none';
            } else {
                document.getElementById('header-title').textContent = '⚙️ 设置';
                msgs.style.display = 'none';
                document.getElementById('input-area').style.display = 'none';
                document.getElementById('settings-panel').style.display = 'block';
            }
        }

        // 保存消息历史到 localStorage
        function saveMessage(type, content, extra = '') {
            const history = JSON.parse(localStorage.getItem('pyclaw_history_' + sessionId) || '[]');
            history.push({ type, content, extra, time: Date.now() });
            localStorage.setItem('pyclaw_history_' + sessionId, JSON.stringify(history));
        }

        // 恢复消息历史
        function restoreHistory() {
            const history = JSON.parse(localStorage.getItem('pyclaw_history_' + sessionId) || '[]');
            if (history.length === 0) return;
            
            // 清空欢迎消息
            const welcome = document.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            history.forEach(msg => {
                if (msg.type === 'user') {
                    addMsgToDOM(msg.content, true, false);
                } else if (msg.type === 'assistant') {
                    addMsgToDOM(msg.content, false, false);
                } else if (msg.type === 'thinking') {
                    // 思考步骤的内容存在 extra 里
                    addStepToDOM('thinking', msg.extra, '', false);
                } else if (msg.type === 'tool_call') {
                    addStepToDOM('tool', msg.extra, msg.content, false);
                } else if (msg.type === 'tool_result') {
                    addStepToDOM('result', msg.extra, msg.content, false);
                }
            });
            msgs.scrollTop = msgs.scrollHeight;
        }

        function addMsgToDOM(content, isUser, save = true) {
            const div = document.createElement('div');
            div.className = 'msg-wrap';
            const avatar = isUser ? '👤' : '🦞';
            const name = isUser ? '你' : 'PyClaw AI';
            div.innerHTML = '<div class="msg-header"><span class="avatar ' + (isUser ? 'user' : 'assistant') + '">' + avatar + '</span>' + name + '</div><div class="msg ' + (isUser ? 'user' : '') + '">' + content + '</div>';
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
            if (save) saveMessage(isUser ? 'user' : 'assistant', content);
        }

        function addStepToDOM(type, label, content, save = true) {
            const div = document.createElement('div');
            div.className = 'step ' + type;
            div.innerHTML = '<div style="font-weight: 600;">' + label + '</div><div style="margin-top: 4px; opacity: 0.9; white-space: pre-wrap; max-height: 150px; overflow-y: auto;">' + content + '</div>';
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
            if (save) saveMessage(type, content, label);
        }

        function addMsg(content, isUser) {
            addMsgToDOM(content, isUser);
        }

        function addStep(type, label, content) {
            addStepToDOM(type, label, content);
        }

        function send(msg) { input.value = msg; sendMsg(); }
        function sendMsg() {
            const text = input.value.trim(); if (!text) return;
            addMsg(text, true); input.value = '';
            ws.send(JSON.stringify({ content: text, session_id: sessionId }));
        }

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'thinking') addStep('thinking', '🤔 ' + data.content, '');
            else if (data.type === 'tool_call') addStep('tool', '🔧 调用工具: ' + data.tool, data.params);
            else if (data.type === 'tool_result') addStep('result', '✅ 工具结果: ' + data.tool, data.content);
            else if (data.type === 'final') addMsg(data.content, false);
        };

        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMsg(); });



        // 保存会话到会话列表
        function saveSessionToList(sessionId) {
            let sessions = JSON.parse(localStorage.getItem('pyclaw_sessions') || '[]');
            if (!sessions.includes(sessionId)) {
                sessions.unshift(sessionId);
                localStorage.setItem('pyclaw_sessions', JSON.stringify(sessions));
            }
        }

        // 渲染会话列表
        function renderSessionList() {
            const sessions = JSON.parse(localStorage.getItem('pyclaw_sessions') || '[]');
            const container = document.getElementById('session-list');
            container.innerHTML = '';
            
            if (sessions.length === 0) {
                container.innerHTML = '<div style="color: #8b949e; font-size: 12px;">暂无会话</div>';
                return;
            }
            
            sessions.forEach((sid, index) => {
                const history = JSON.parse(localStorage.getItem('pyclaw_history_' + sid) || '[]');
                const msgCount = history.filter(m => m.type === 'user' || m.type === 'assistant').length;
                const isCurrent = sid === sessionId;
                
                const div = document.createElement('div');
                const borderColor = isCurrent ? '#58a6ff' : '#30363d';
                const bgColor = isCurrent ? '#1f6feb22' : '#0d1117';
                const leftBorder = isCurrent ? '3px solid #58a6ff' : '3px solid transparent';
                div.style.cssText = 'padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; font-size: 12px; background: ' + bgColor + '; border-top: 1px solid ' + borderColor + '; border-right: 1px solid ' + borderColor + '; border-bottom: 1px solid ' + borderColor + '; border-left: ' + leftBorder + '; cursor: pointer; position: relative; padding-right: 36px;';
                
                const currentText = isCurrent ? '<span style="color: #58a6ff; font-weight: 600; margin-left: 8px;">● 当前</span>' : '';
                
                div.innerHTML = '<span>' + sid.substring(0, 12) + '...</span>' +
                    '<span style="color: #8b949e; margin-left: 6px;">' + msgCount + ' 条消息</span>' +
                    currentText +
                    '<button class="del-btn" style="background: transparent; border: none; color: #8b949e; cursor: pointer; padding: 2px 4px; border-radius: 4px; font-size: 12px; position: absolute; right: 8px; top: 6px;">🗑️</button>';
                
                // 点击除按钮外的区域切换会话
                div.onclick = (e) => {
                    if (!e.target.classList.contains('del-btn')) {
                        switchSession(sid);
                    }
                };
                
                // 删除按钮事件
                const btn = div.querySelector('.del-btn');
                btn.onclick = (e) => {
                    e.stopPropagation();
                    deleteSession(sid);
                };
                btn.onmouseover = () => { btn.style.color = '#f85149'; btn.style.background = '#da363322'; };
                btn.onmouseout = () => { btn.style.color = '#8b949e'; btn.style.background = 'transparent'; };
                container.appendChild(div);
            });
        }

        // 删除会话
        function deleteSession(sid) {
            if (!confirm('确定要删除会话 "' + sid + '" 吗？')) return;
            
            let sessions = JSON.parse(localStorage.getItem('pyclaw_sessions') || '[]');
            sessions = sessions.filter(s => s !== sid);
            localStorage.setItem('pyclaw_sessions', JSON.stringify(sessions));
            localStorage.removeItem('pyclaw_history_' + sid);
            
            // 如果删除的是当前会话，切到第一个或创建新的
            if (sid === sessionId) {
                if (sessions.length > 0) {
                    localStorage.setItem('pyclaw_session_id', sessions[0]);
                } else {
                    const newId = 'web_' + Math.random().toString(36).slice(2, 10);
                    localStorage.setItem('pyclaw_session_id', newId);
                    saveSessionToList(newId);
                }
                location.reload();
            } else {
                renderSessionList();
            }
        }

        // 切换会话
        function switchSession(newSessionId) {
            localStorage.setItem('pyclaw_session_id', newSessionId);
            location.reload();
        }

        // 开启新会话
        function newSession() {
            const newId = 'web_' + Math.random().toString(36).slice(2, 10);
            saveSessionToList(newId);
            localStorage.setItem('pyclaw_session_id', newId);
            location.reload();
        }


    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
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
            # 使用前端选择的模型
            await process_chat(websocket, msg.session_id)
    except WebSocketDisconnect:
        pass

async def process_chat(websocket, session_id):
    for turns in range(20):
        history = gateway.session_manager.get_history(session_id)
        
        await websocket.send_json({
            "type": "thinking",
            "content": f"第 {turns + 1} 轮思考"
        })
        
        response = await gateway.agent.chat(history)
        
        # 无论有没有工具调用，都先保存 assistant 消息
        # DeepSeek 严格校验：tool 消息必须紧跟在带 tool_calls 的 assistant 消息后面
        assistant_msg = Message(
            id=f"assist_{uuid.uuid4().hex[:6]}",
            content=response.content or "",
            sender="assistant",
            role=MessageRole.ASSISTANT,
            timestamp=time.time(),
            channel_id="web",
            session_id=session_id,
            # 把 tool_calls 完整保存下来，用于 API 格式校验
            tool_calls=[
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.parameters, ensure_ascii=False)
                    }
                }
                for tc in response.tool_calls
            ] if response.tool_calls else None
        )
        gateway.session_manager.add_message(session_id, assistant_msg)
        
        if not response.tool_calls:
            await websocket.send_json({
                "type": "final",
                "content": response.content or "抱歉，我没有理解你的问题。"
            })
            return
        
        for tool_call in response.tool_calls:
            await websocket.send_json({
                "type": "tool_call",
                "tool": tool_call.name,
                "params": json.dumps(tool_call.parameters, ensure_ascii=False, indent=2)
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2469)
