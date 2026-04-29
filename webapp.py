#!/usr/bin/env python3
import asyncio, uuid, time, json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pyclaw import Gateway
from pyclaw.pyclaw_types import Message, MessageRole
from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool
from skills.workspace import WorkspaceSkill

gateway = None

def load_api_config():
    """从 U 盘根目录的 API.txt 读取 API Key（跨平台）"""
    import glob as _glob
    
    possible_paths = [
        "../API.txt",           # U 盘根目录（相对路径，Linux/Win）
        "./API.txt",            # 当前目录
        "/media/claw/_ز_/API.txt",  # Linux 绝对路径
        "D:/API.txt",           # Windows U盘 D 盘
        "E:/API.txt",           # Windows U盘 E 盘
        "F:/API.txt",           # Windows U盘 F 盘
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
    data_dir = os.environ.get("PYCLAW_DATA_DIR")
    if not data_dir:
        # 默认存储在 workspace 下，避免 U 盘空间爆满
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyclaw_data")
    
    os.makedirs(data_dir, exist_ok=True)
    print(f"📂 会话持久化目录: {data_dir}")

    gateway = Gateway(
        llm_api_key=api_key,
        storage_path=data_dir,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-v4-flash"
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#0d1117">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="PyClaw">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230d1117'/%3E%3Ctext y='70' x='50' font-size='60' text-anchor='middle'%3E%F0%9F%A6%9E%3C/text%3E%3C/svg%3E">
    <title>PyClaw</title>
    <style>
        /* ===== 全局重置 / 基础 ===== */
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        html, body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; width: 100%; height: 100%; overflow: hidden; display: flex; flex-direction: row; }
        html { overflow: hidden; }
        body { min-height: 100vh; }
        
        /* ===== 移动端侧栏遮罩 ===== */
        .sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 98; }
        .sidebar-overlay.show { display: block; }
        
        /* ===== 侧边栏 ===== */
        .sidebar { width: 260px; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; height: 100vh; flex-shrink: 0; z-index: 99; transition: transform .3s ease; }
        .sidebar-header { padding: 20px 16px; border-bottom: 1px solid #30363d; font-size: 18px; font-weight: 600; color: #58a6ff; flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; }
        .nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 14px; margin: 2px 8px; }
        .nav-item:hover { background: #21262d; }
        .nav-item.active { background: #21262d; color: #58a6ff; }
        .main { flex: 1; display: flex; flex-direction: column; height: 100vh; min-width: 0; }
        
        /* ===== 顶栏 ===== */
        .chat-header { padding: 12px 16px; border-bottom: 1px solid #30363d; background: #161b22; font-size: 16px; font-weight: 600; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; gap: 8px; }
        .hamburger { display: none; background: none; border: none; color: #e6edf3; font-size: 22px; cursor: pointer; padding: 4px; position: static; } /* desktop hidden */
        
        /* ===== 消息区 ===== */
        .messages { flex: 1; overflow-y: auto; padding: 16px; display: block; min-height: 0; -webkit-overflow-scrolling: touch; }
        .settings-panel { flex: 1; overflow-y: auto; padding: 16px; display: none; min-height: 0; }
        .msg-wrap { max-width: 850px; margin: 0 auto 12px auto; }
        .msg-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: #8b949e; }
        .msg-header .avatar { width: 20px; height: 20px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
        .msg-header .avatar.user { background: linear-gradient(135deg, #58a6ff, #8b5cf6); }
        .msg-header .avatar.assistant { background: #238636; }
        .msg { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; font-size: 14px; line-height: 1.6; overflow-wrap: break-word; word-break: break-word; }
        .msg.user { background: #1f6feb22; border-color: #1f6feb44; }
        .step { max-width: 850px; margin: 0 auto 6px auto; padding: 8px 12px; border-radius: 6px; font-size: 12px; font-family: monospace; border-left: 3px solid; overflow-wrap: break-word; word-break: break-word; }
        .step.thinking { background: #1a1f26; border-color: #58a6ff; color: #58a6ff; }
        .step.tool { background: #262110; border-color: #d29922; color: #d29922; }
        .step.result { background: #0f2918; border-color: #238636; color: #3fb950; }
        
        /* ===== 输入区 ===== */
        .input-area { padding: 12px 16px 16px; background: #161b22; border-top: 1px solid #30363d; flex-shrink: 0; }
        .input-wrap { max-width: 850px; margin: 0 auto; display: flex; gap: 8px; align-items: flex-end; }
        #input { flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; color: #e6edf3; font-size: 16px; line-height: 1.4; outline: none; min-height: 44px; resize: none; }
        #input:focus { border-color: #58a6ff; }
        #send-btn { background: #238636; color: white; border: none; border-radius: 8px; padding: 12px 20px; cursor: pointer; font-size: 14px; font-weight: 600; white-space: nowrap; flex-shrink: 0; position: static; }  /* override old absolute */
        #send-btn:active { background: #1e7a2f; }
        
        /* ===== 欢迎页 ===== */
        .welcome { max-width: 850px; margin: 0 auto; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; text-align: center; }
        .examples { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
        .example { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: left; cursor: pointer; font-size: 13px; user-select: none; }
        .example:active { border-color: #58a6ff; background: #161b22; }
        
        /* ===== 工具列表（侧栏底部） ===== */
        .tools { padding: 16px; font-size: 12px; flex: 1; overflow-y: auto; min-height: 0; }
        .tool-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: #8b949e; }
        
        /* ===== 设置卡片 ===== */
        .card { max-width: 600px; margin: 0 auto 16px; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; flex-shrink: 0; }
        .card-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #30363d; }
        .lang-switch { background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 13px; color: #8b949e; flex-shrink: 0; }
        .lang-switch:active { border-color: #58a6ff; color: #e6edf3; }
        
        /* ===== 电脑端全屏（≥1024px） ===== */
        @media (min-width: 1024px) {
            .sidebar-header .hamburger { display: none !important; }
            .msg-wrap { max-width: none; width: 100%; margin: 0 auto 12px auto; }
            .input-wrap { max-width: none; width: 100%; }
            .welcome { max-width: none; width: 100%; }
            .step { max-width: none; width: 100%; }
            #input { font-size: 15px; }
            .messages { padding: 20px 32px; }
            .input-area { padding: 16px 32px; }
            .msg { padding: 14px 20px; font-size: 15px; }
            .step { padding: 10px 16px; font-size: 13px; }
            .sidebar { width: 280px; }
            .chat-header { padding: 14px 20px; }
        }
        
        /* ===== 手机响应式 ===== */
        @media (max-width: 768px) {
            .sidebar { position: fixed; left: 0; top: 0; transform: translateX(-100%); width: 280px; height: 100vh; }
            .sidebar.open { transform: translateX(0); }
            .sidebar-header { position: relative; z-index: 100; }
            .hamburger { display: inline-flex; align-items: center; justify-content: center; font-size: 24px; }
            .chat-header { padding: 10px 12px; }
            .messages { padding: 12px; }
            .input-area { padding: 10px 12px 14px; }
            #input { font-size: 16px; padding: 10px 14px; } /* avoid zoom on iOS */
            #send-btn { padding: 10px 16px; font-size: 14px; }
            .msg-wrap { margin-bottom: 10px; }
            .msg { padding: 10px 14px; font-size: 14px; }
            .step { padding: 6px 10px; font-size: 11px; }
            .welcome { padding: 16px; }
            .examples { grid-template-columns: 1fr; }
            .settings-panel { padding: 12px; }
            .card { padding: 16px; }
        }

        /* ===== 配置向导 ===== */
        .wizard-overlay {
            display: none;
            position: fixed; inset: 0; z-index: 9999;
            background: rgba(0,0,0,0.6);
            align-items: center; justify-content: center;
        }
        .wizard-overlay.show { display: flex; }
        .wizard-box {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 16px;
            max-width: 480px; width: 90%;
            max-height: 80vh; overflow-y: auto;
            padding: 32px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .wizard-box h2 {
            margin: 0 0 8px 0;
            font-size: 22px; color: #e6edf3;
        }
        .wizard-box p {
            color: #8b949e; font-size: 14px;
            margin: 0 0 24px 0;
        }
        .wizard-box label {
            display: block;
            margin-bottom: 6px;
            font-size: 13px; font-weight: 600; color: #e6edf3;
        }
        .wizard-box select, .wizard-box input[type="text"], .wizard-box input[type="password"] {
            width: 100%;
            padding: 10px 14px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #e6edf3;
            font-size: 14px;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        .wizard-box select:focus, .wizard-box input:focus {
            border-color: #58a6ff;
            outline: none;
        }
        .wizard-btn {
            width: 100%;
            padding: 12px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }
        .wizard-btn:hover { background: #2ea043; }
        .wizard-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .wizard-box .hint {
            font-size: 12px;
            color: #8b949e;
            margin: -12px 0 16px 0;
        }
        .wizard-step { display: none; }
        .wizard-step.active { display: block; }
        .wizard-progress {
            display: flex; gap: 8px; margin-bottom: 24px;
        }
        .wizard-progress .dot {
            flex: 1; height: 3px; border-radius: 2px;
            background: #30363d;
        }
        .wizard-progress .dot.done { background: #238636; }
        .wizard-progress .dot.current { background: #58a6ff; }
    </style>
</head>
<body>
    <!-- 配置向导弹窗 -->
    <div class="wizard-overlay" id="wizardOverlay">
        <div class="wizard-box">
            <div class="wizard-progress">
                <div class="dot current" id="dot1"></div>
                <div class="dot" id="dot2"></div>
                <div class="dot" id="dot3"></div>
            </div>

            <!-- 步骤 1: 选择供应商 -->
            <div class="wizard-step active" id="wizardStep1">
                <h2 data-i18n="wizTitle1">🚀 选择 AI 供应商</h2>
                <p data-i18n="wizDesc1">选择一个供应商来开始对话。DeepSeek 推荐，其他供应商需自行配置 API Key。</p>
                <label for="wizProvider"><span data-i18n="providerLabel">供应商</span></label>
                <select id="wizProvider" onchange="onWizProviderChange()">
                    <option value="deepseek">DeepSeek</option>
                    <option value="other">🌐 其他供应商</option>
                </select>
                <button class="wizard-btn" onclick="wizardNext()" data-i18n="wizNext">下一步 →</button>
            </div>

            <!-- 步骤 2: API 配置 -->
            <div class="wizard-step" id="wizardStep2">
                <h2 data-i18n="wizTitle2">🔑 API 配置</h2>
                <p data-i18n="wizDesc2">填写 API Key 和端点地址。</p>
                
                <label for="wizApiKey"><span data-i18n="apiKeyLabel">API Key</span></label>
                <input id="wizApiKey" type="password" placeholder="sk-...">
                <div id="wizApiKeyHint" style="font-size: 12px; color: #238636; margin: -12px 0 16px 0; display: none;">✔️ <span data-i18n="useFileApiKey">将使用 API.txt 中的配置</span></div>
                
                <div id="wizEndpointBlock">
                    <label for="wizEndpoint"><span data-i18n="endpointLabel">Endpoint</span></label>
                    <input id="wizEndpoint" type="text" value="https://api.deepseek.com/v1">
                    <div class="hint" data-i18n="endpointHint">完整的 Base URL，例如 https://api.deepseek.com/v1</div>
                </div>
                
                <div id="wizModelInputBlock" style="display:none;">
                    <label for="wizModelInput"><span data-i18n="customModelLabel">模型名称</span></label>
                    <input id="wizModelInput" type="text" placeholder="gpt-4o, qwen-max...">
                    <div class="hint" data-i18n="modelHint">输入你使用的模型名称</div>
                </div>
                
                <div id="wizModelSelectBlock">
                    <label for="wizModelSelect"><span data-i18n="modelLabel">模型</span></label>
                    <select id="wizModelSelect">
                        <option value="deepseek-v4-flash">DeepSeek V4 Flash (推荐)</option>
                        <option value="deepseek-chat">DeepSeek Chat V3.2</option>
                        <option value="deepseek-reasoner">DeepSeek R1 (推理模型)</option>
                    </select>
                </div>
                
                <button class="wizard-btn" onclick="wizardFinish()" data-i18n="wizFinish">✅ 开始对话</button>
            </div>
        </div>
    </div>

    <!-- 侧栏遮罩（移动端） -->
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
    
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header"><span data-i18n="sidebarTitle">🦞 PyClaw</span><span class="hamburger" onclick="toggleSidebar()">✕</span></div>
        <div style="padding: 8px 0;">
            <div class="nav-item active" id="nav-chat" onclick="switchTab('chat')"><span>💬</span><span data-i18n="navChat">聊天</span></div>
            <div class="nav-item" id="nav-settings" onclick="switchTab('settings')"><span>⚙️</span><span data-i18n="navSettings">设置</span></div>
        </div>
        <div class="tools">
            <div style="font-weight: 600; margin-bottom: 8px; color: #e6edf3;" data-i18n="toolsTitle">工具列表</div>
            <div class="tool-item">📁 <span data-i18n="tool1">目录浏览</span></div>
            <div class="tool-item">📄 <span data-i18n="tool2">文件读取</span></div>
            <div class="tool-item">💻 <span data-i18n="tool3">命令执行</span></div>
            <div class="tool-item">⏰ <span data-i18n="tool4">时间查询</span></div>
        </div>
    </div>
    <div class="main">
        <div class="chat-header">
            <span class="hamburger" id="hamburgerBtn" onclick="toggleSidebar()">☰</span>
            <span id="header-title" data-i18n="headerChat">🧠 Agent Chat</span>
            <button class="lang-switch" onclick="toggleLang()" id="lang-btn">🌐 EN</button>
        </div>
        <div class="messages" id="messages">
            <div class="welcome">
                <div style="font-size: 48px; margin-bottom: 16px;">🦞</div>
                <div style="font-size: 20px; font-weight: 600; margin-bottom: 8px;" data-i18n="welcomeTitle">欢迎使用 PyClaw</div>
                <div style="color: #8b949e; margin-bottom: 16px;" data-i18n="welcomeSub">从零构建的 AI 助手框架</div>
                <div class="examples">
                    <div class="example" onclick="send('看看当前目录有什么')">📁 <span data-i18n="example1">列出目录内容</span></div>
                    <div class="example" onclick="send('读取 README.md 文件')">📄 <span data-i18n="example2">读取文件</span></div>
                    <div class="example" onclick="send('执行 pwd 命令')">💻 <span data-i18n="example3">执行命令</span></div>
                    <div class="example" onclick="send('现在北京时间几点了')">⏰ <span data-i18n="example4">查询时间</span></div>
                </div>
            </div>
        </div>
        <div class="settings-panel" id="settings-panel">
            <div class="card">
                <div class="card-title" data-i18n="cardChatManage">🧹 对话管理</div>
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 13px; color: #8b949e; margin-bottom: 8px;"><span data-i18n="curSessionLabel">当前会话ID:</span> <code id="session-id-display" style="background: #0d1117; padding: 2px 6px; border-radius: 4px;">-</code></div>
                    <button onclick="newSession()" id="btn-new-session" style="width: 100%; max-width: 200px; background: #238636; color: white; border: none; border-radius: 6px; padding: 8px 14px; cursor: pointer; font-size: 13px;">➕ 开启新会话</button>
                </div>
                <div>
                    <div style="font-size: 13px; color: #8b949e; margin-bottom: 10px;" data-i18n="sessionListLabel">会话列表</div>
                    <div id="session-list" style="max-height: 300px; overflow-y: auto;"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">🔧 <span data-i18n="cardModel">模型设置</span></div>
                <div style="font-size: 14px; color: #8b949e; line-height: 1.8;">
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #e6edf3;" data-i18n="providerLabel">供应商:</strong>
                        <select id="provider-select" onchange="onProviderChange()" style="width: 100%; margin-top: 8px; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px;">
                            <option value="deepseek">DeepSeek</option>
                            <option value="other">🌐 其他供应商</option>
                        </select>
                    </div>
                    <div id="model-select-block" style="margin-bottom: 12px;">
                        <strong style="color: #e6edf3;" data-i18n="modelLabel">模型:</strong>
                        <select id="model-select" onchange="saveModelSetting()" style="width: 100%; margin-top: 8px; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px;">
                            <option value="deepseek-v4-flash">DeepSeek V4 Flash (推荐)</option>
                            <option value="deepseek-chat">DeepSeek Chat V3.2</option>
                            <option value="deepseek-reasoner">DeepSeek R1 (推理模型)</option>
                        </select>
                    </div>
                    <div id="model-input-block" style="margin-bottom: 12px; display: none;">
                        <strong style="color: #e6edf3;" data-i18n="customModelLabel">模型名称:</strong>
                        <input id="custom-model-input" type="text" placeholder="gpt-4o, claude-3-opus, qwen-max..." oninput="saveCustomModel()" style="width: 100%; margin-top: 8px; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px;">
                    </div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #e6edf3;" data-i18n="apiKeyLabel">API Key</strong>
                        <input id="settings-api-key" type="password" placeholder="sk-..." oninput="saveSettingsApiKey()" style="width: 100%; margin-top: 8px; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px;">
                    </div>
                    <div>
                        <strong style="color: #e6edf3;" data-i18n="endpointLabel">Endpoint:</strong>
                        <input id="custom-endpoint" type="text" value="https://api.deepseek.com/v1" oninput="saveEndpoint()" style="width: 100%; margin-top: 8px; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px;">
                    </div>
                    <div id="model-status" style="margin-top: 8px; color: #238636; font-size: 12px; display: none;">✅ <span data-i18n="configUpdated">配置已更新</span></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title" data-i18n="cardAbout">📦 关于</div>
                <div style="font-size: 14px; color: #8b949e; line-height: 1.8;">
                    <div>🦞 <strong style="color: #e6edf3;">PyClaw</strong></div>
                    <div><span data-i18n="versionLabel">版本:</span> 0.6.2</div>
                    <div id="author-name"><span data-i18n="authorLabel">作者:</span> 骆戡</div>
                    <div style="margin-top: 12px;" data-i18n="aboutDesc">参考 OpenClaw 设计理念，从零构建的 AI 助手框架</div>
                </div>
            </div>
        </div>
        <div class="input-area" id="input-area">
            <div class="input-wrap">
                <input id="input" placeholder="输入消息..." autocomplete="off">
                <button onclick="sendMsg()" id="send-btn" data-i18n="sendBtn">发送</button>
            </div>
        </div>
    </div>
    <script>
        // ==========================================
        // 🌐 中英文翻译系统
        // ==========================================
        const translations = {
            zh: {
                langBtn: '🌐 EN',
                sidebarTitle: '🦞 PyClaw',
                navChat: '聊天',
                navSettings: '设置',
                toolsTitle: '工具列表',
                tool1: '目录浏览',
                tool2: '文件读取',
                tool3: '命令执行',
                tool4: '时间查询',
                headerChat: '🧠 Agent Chat',
                headerSettings: '⚙️ 设置',
                welcomeTitle: '欢迎使用 PyClaw',
                welcomeSub: '从零构建的 AI 助手框架',
                example1: '列出目录内容',
                example2: '读取文件',
                example3: '执行命令',
                example4: '查询时间',
                inputPlaceholder: '输入消息...',
                sendBtn: '发送',
                userLabel: '你',
                aiLabel: 'PyClaw AI',
                thinkingLabel: '🤔 思考中...',
                toolCallLabel: '🔧 调用工具',
                toolResultLabel: '✅ 工具结果',
                cardChatManage: '🧹 对话管理',
                curSessionLabel: '当前会话ID:',
                newSessionBtn: '➕ 开启新会话',
                sessionListLabel: '会话列表',
                noSessionsLabel: '暂无会话',
                msgCountLabel: '条消息',
                deleteConfirmLabel: '确定要删除会话吗？',
                deleteAllConfirmLabel: '确定要删除所有会话吗？',
                deleteAllBtn: '🗑️ 删除所有会话',
                cardModel: '🔧 模型设置',
                modelLabel: '模型:',
                providerLabel: '供应商:',
                customModelLabel: '模型名称:',
                endpointLabel: 'Endpoint:',
                configUpdated: '配置已更新',
                apiKeyLabel: 'API Key',
                endpointHint: '完整的 Base URL，例如 https://api.deepseek.com/v1',
                modelHint: '输入你使用的模型名称',
                useFileApiKey: '将使用 API.txt 中的配置',
                cardAbout: '📦 关于',
                versionLabel: '版本:',
                authorLabel: '作者:',
                aboutDesc: '参考 OpenClaw 设计理念，从零构建的 AI 助手框架',
                wizTitle1: '🚀 选择 AI 供应商',
                wizDesc1: '选择一个供应商来开始对话。DeepSeek 推荐，其他供应商需自行配置 API Key。',
                wizTitle2: '🔑 API 配置',
                wizDesc2: '填写 API Key 和端点地址。',
                wizNext: '下一步 →',
                wizFinish: '✅ 开始对话',
            },
            en: {
                langBtn: '🌐 中文',
                sidebarTitle: '🦞 PyClaw',
                navChat: 'Chat',
                navSettings: 'Settings',
                toolsTitle: 'Available Tools',
                tool1: 'List Directory',
                tool2: 'Read File',
                tool3: 'Execute Command',
                tool4: 'Time Query',
                headerChat: '🧠 Agent Chat',
                headerSettings: '⚙️ Settings',
                welcomeTitle: 'Welcome to PyClaw',
                welcomeSub: 'AI assistant framework built from scratch',
                example1: 'List directory contents',
                example2: 'Read README file',
                example3: 'Execute a command',
                example4: 'What time is it?',
                inputPlaceholder: 'Type your message...',
                sendBtn: 'Send',
                userLabel: 'You',
                aiLabel: 'PyClaw AI',
                thinkingLabel: '🤔 Thinking...',
                toolCallLabel: '🔧 Tool Call',
                toolResultLabel: '✅ Tool Result',
                cardChatManage: '🧹 Chat Management',
                curSessionLabel: 'Current Session ID:',
                newSessionBtn: '➕ New Session',
                sessionListLabel: 'Session List',
                noSessionsLabel: 'No sessions yet',
                msgCountLabel: 'messages',
                deleteConfirmLabel: 'Are you sure to delete this session?',
                deleteAllConfirmLabel: 'Are you sure to delete all sessions?',
                deleteAllBtn: '🗑️ Delete All Sessions',
                cardModel: '🔧 Model Settings',
                modelLabel: 'Model:',
                providerLabel: 'Provider:',
                customModelLabel: 'Model Name:',
                endpointLabel: 'Endpoint:',
                configUpdated: 'Config updated',
                apiKeyLabel: 'API Key',
                endpointHint: 'Full Base URL, e.g. https://api.deepseek.com/v1',
                modelHint: 'Enter the model name you use',
                useFileApiKey: 'Will use API.txt config',
                cardAbout: '📦 About',
                versionLabel: 'Version:',
                authorLabel: 'Author:',
                aboutDesc: 'AI assistant framework built from scratch, inspired by OpenClaw',
                wizTitle1: '🚀 Choose AI Provider',
                wizDesc1: 'Select a provider. DeepSeek recommended. Other providers need your own API Key.',
                wizTitle2: '🔑 API Configuration',
                wizDesc2: 'Enter your API Key and endpoint.',
                wizNext: 'Next →',
                wizFinish: '✅ Start Chat',
            }
        };

        let currentLang = localStorage.getItem('pyclaw_lang') || 'zh';

        function applyTranslation() {
            const t = translations[currentLang];
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (t[key]) el.textContent = t[key];
            });
            document.getElementById('lang-btn').textContent = t.langBtn;
            document.getElementById('send-btn').textContent = t.sendBtn;
            document.getElementById('btn-new-session').textContent = t.newSessionBtn;
            document.getElementById('input').placeholder = t.inputPlaceholder;
            document.getElementById('author-name').innerHTML = '<span data-i18n="authorLabel">' + t.authorLabel + '</span> ' + (currentLang === 'zh' ? '骆戡' : 'Campus');
            localStorage.setItem('pyclaw_lang', currentLang);
            // 重新渲染会话列表以更新翻译
            renderSessionList();
        }

        function toggleLang() {
            currentLang = currentLang === 'zh' ? 'en' : 'zh';
            applyTranslation();
        }

        const msgs = document.getElementById('messages');
        const input = document.getElementById('input');
        
        // 从 localStorage 读取会话ID，没有则创建新的
        let sessionId = localStorage.getItem('pyclaw_session_id');
        if (!sessionId) {
            sessionId = 'web_' + Math.random().toString(36).slice(2, 10);
            localStorage.setItem('pyclaw_session_id', sessionId);
        }
        console.log('当前会话ID:', sessionId);
        
        let ws = null;
        let wsReconnectAttempts = 0;
        const WS_MAX_RECONNECT = 20;
        
        function connectWebSocket() {
            if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
            
            // 保存当前会话到列表
            saveSessionToList(sessionId);

            ws.onopen = () => {
                wsReconnectAttempts = 0;
                console.log('WebSocket 已连接');
                document.getElementById('session-id-display').textContent = sessionId;
                // 移除断连提示（如果有）
                const disconnected = document.querySelector('.msg.disconnected');
                if (disconnected) disconnected.remove();
                restoreHistory();
                renderSessionList();
                applyTranslation();
                
                const savedModel = localStorage.getItem('pyclaw_model');
                if (savedModel) {
                    ws.send(JSON.stringify({
                        type: 'set_model',
                        model: savedModel
                    }));
                }
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const t = translations[currentLang];
                if (data.type === 'thinking') addStep('thinking', '🤔 ' + data.content, '');
                else if (data.type === 'tool_call') addStep('tool', '🔧 ' + t.toolCallLabel + ': ' + data.tool, data.params);
                else if (data.type === 'tool_result') addStep('result', '✅ ' + t.toolResultLabel + ': ' + data.tool, data.content);
                else if (data.type === 'final') addMsg(data.content, false);
            };

            ws.onclose = () => {
                console.log('WebSocket 已断开，', wsReconnectAttempts, '次重连尝试');
                
                if (wsReconnectAttempts < WS_MAX_RECONNECT) {
                    wsReconnectAttempts++;
                    
                    const disconnectMsg = currentLang === 'zh' 
                        ? '⚠️ 连接已断开，正在自动重连... (' + wsReconnectAttempts + '/' + WS_MAX_RECONNECT + ')'
                        : '⚠️ Connection lost, reconnecting... (' + wsReconnectAttempts + '/' + WS_MAX_RECONNECT + ')';
                    
                    let discEl = document.querySelector('.msg.disconnected');
                    if (!discEl) {
                        discEl = document.createElement('div');
                        discEl.className = 'msg-wrap disconnected';
                        discEl.innerHTML = '<div class="msg" style="background:#262110;border-color:#d29922;text-align:center;font-size:13px;">' + disconnectMsg + '</div>';
                        const messages = document.querySelector('.messages');
                        messages.insertBefore(discEl, messages.firstChild);
                    } else {
                        discEl.querySelector('.msg').textContent = disconnectMsg;
                    }
                    
                    const delay = Math.min(1000 * Math.pow(1.5, wsReconnectAttempts - 1), 10000);
                    setTimeout(connectWebSocket, delay);
                } else {
                    const failMsg = currentLang === 'zh' 
                        ? '❌ 无法连接到服务器，请刷新页面重试。'
                        : '❌ Cannot connect to server, please refresh the page.';
                    addMsg(failMsg, false);
                }
            };
            
            ws.onerror = () => {
                console.log('WebSocket 错误');
            };
        }

        function switchTab(tab) {
            const t = translations[currentLang];
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById('nav-' + tab).classList.add('active');
            if (tab === 'chat') {
                document.getElementById('header-title').textContent = t.headerChat;
                document.getElementById('lang-btn').textContent = t.langBtn;
                msgs.style.display = 'block';
                document.getElementById('input-area').style.display = 'block';
                document.getElementById('settings-panel').style.display = 'none';
            } else {
                document.getElementById('header-title').textContent = t.headerSettings;
                document.getElementById('lang-btn').textContent = t.langBtn;
                msgs.style.display = 'none';
                document.getElementById('input-area').style.display = 'none';
                document.getElementById('settings-panel').style.display = 'block';
            }
        }

        // 侧栏切换（移动端）
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }
        // 点击消息区自动收起侧栏（移动端）
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && !e.target.closest('.sidebar') && !e.target.closest('#hamburgerBtn')) {
                document.getElementById('sidebar').classList.remove('open');
                document.getElementById('sidebarOverlay').classList.remove('show');
            }
        });

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
            
            // 先清空消息区，防止重复渲染
            msgs.innerHTML = '';
            
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
            const name = isUser ? translations[currentLang].userLabel : translations[currentLang].aiLabel;
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
            
            // 检查 WebSocket 状态，断开则尝试重连
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                wsReconnectAttempts = 0;
                connectWebSocket();
                const waitMsg = currentLang === 'zh' 
                    ? '🔄 正在重新连接...，请稍后再发送。'
                    : '🔄 Reconnecting... Please try again in a moment.';
                addMsg(waitMsg, false);
                return;
            }
            
            addMsg(text, true); input.value = '';
            ws.send(JSON.stringify({ content: text, session_id: sessionId }));
        }

        // ==========================================
        // 🔧 配置向导 & 供应商管理
        // ==========================================

        // 检查是否首次使用，启动向导
        function checkWizard() {
            if (!localStorage.getItem('pyclaw_configured')) {
                document.getElementById('wizardOverlay').classList.add('show');
            }
        }

        function onWizProviderChange() {
            const provider = document.getElementById('wizProvider').value;
            const dsBlocks = document.getElementById('wizModelSelectBlock');
            const customBlock = document.getElementById('wizModelInputBlock');
            const endpointInput = document.getElementById('wizEndpoint');
            const apiKeyInput = document.getElementById('wizApiKey');
            const apiKeyHint = document.getElementById('wizApiKeyHint');
            if (provider === 'deepseek') {
                dsBlocks.style.display = 'block';
                customBlock.style.display = 'none';
                endpointInput.value = 'https://api.deepseek.com/v1';
                apiKeyInput.disabled = true;
                apiKeyInput.placeholder = '✔️ ' + translations[currentLang].useFileApiKey;
                apiKeyHint.style.display = 'block';
            } else {
                dsBlocks.style.display = 'none';
                customBlock.style.display = 'block';
                endpointInput.value = '';
                apiKeyInput.disabled = false;
                apiKeyInput.placeholder = 'sk-...';
                apiKeyHint.style.display = 'none';
            }
        }

        function wizardNext() {
            document.getElementById('wizardStep1').classList.remove('active');
            document.getElementById('wizardStep2').classList.add('active');
            document.getElementById('dot1').className = 'dot done';
            document.getElementById('dot2').className = 'dot current';
            // 根据向导的选择同步设置面板
            const wizProvider = document.getElementById('wizProvider').value;
            document.getElementById('provider-select').value = wizProvider;
            onProviderChange();
        }

        function wizardFinish() {
            const provider = document.getElementById('wizProvider').value;
            const apiKey = document.getElementById('wizApiKey').value.trim();
            let model, endpoint;

            if (provider === 'deepseek') {
                model = document.getElementById('wizModelSelect').value;
                endpoint = document.getElementById('wizEndpoint').value.trim() || 'https://api.deepseek.com/v1';
            } else {
                model = document.getElementById('wizModelInput').value.trim();
                endpoint = document.getElementById('wizEndpoint').value.trim();
                if (!apiKey) {
                    alert(currentLang === 'zh' ? '请填写 API Key' : 'Please enter API Key');
                    return;
                }
            }

            // 保存到 localStorage
            localStorage.setItem('pyclaw_provider', provider);
            localStorage.setItem('pyclaw_model', model);
            localStorage.setItem('pyclaw_endpoint', endpoint);
            localStorage.setItem('pyclaw_configured', 'true');
            if (apiKey) localStorage.setItem('pyclaw_api_key', apiKey);

            // 同步设置面板
            document.getElementById('provider-select').value = provider;
            onProviderChange();
            document.getElementById('custom-endpoint').value = endpoint;
            if (provider === 'deepseek') {
                document.getElementById('model-select').value = model;
            } else {
                document.getElementById('custom-model-input').value = model;
            }

            // 发送配置到后端
            sendConfigToBackend(provider, apiKey, model, endpoint);

            document.getElementById('wizardOverlay').classList.remove('show');
        }

        // 设置面板的供应商切换
        function onProviderChange() {
            const provider = document.getElementById('provider-select').value;
            const modelSelectBlock = document.getElementById('model-select-block');
            const modelInputBlock = document.getElementById('model-input-block');
            const endpointInput = document.getElementById('custom-endpoint');

            if (provider === 'deepseek') {
                modelSelectBlock.style.display = 'block';
                modelInputBlock.style.display = 'none';
                if (!endpointInput.value) endpointInput.value = 'https://api.deepseek.com/v1';
            } else {
                modelSelectBlock.style.display = 'none';
                modelInputBlock.style.display = 'block';
            }
            saveProviderSetting();
        }

        function saveProviderSetting() {
            const provider = document.getElementById('provider-select').value;
            localStorage.setItem('pyclaw_provider', provider);
            // 发送更新
            const model = provider === 'deepseek' 
                ? document.getElementById('model-select').value 
                : document.getElementById('custom-model-input').value;
            const endpoint = document.getElementById('custom-endpoint').value;
            const apiKey = provider === 'other' ? (localStorage.getItem('pyclaw_api_key') || '') : '';
            sendConfigToBackend(provider, apiKey, model, endpoint);
        }

        function saveCustomModel() {
            const model = document.getElementById('custom-model-input').value.trim();
            localStorage.setItem('pyclaw_model', model);
            const provider = document.getElementById('provider-select').value;
            const endpoint = document.getElementById('custom-endpoint').value;
            const apiKey = provider === 'other' ? (localStorage.getItem('pyclaw_api_key') || '') : '';
            sendConfigToBackend(provider, apiKey, model, endpoint);
        }

        function saveEndpoint() {
            const endpoint = document.getElementById('custom-endpoint').value;
            localStorage.setItem('pyclaw_endpoint', endpoint);
            const provider = document.getElementById('provider-select').value;
            const model = provider === 'deepseek'
                ? document.getElementById('model-select').value
                : document.getElementById('custom-model-input').value;
            const apiKey = provider === 'other' ? (localStorage.getItem('pyclaw_api_key') || '') : '';
            sendConfigToBackend(provider, apiKey, model, endpoint);
        }

        function saveSettingsApiKey() {
            const apiKey = document.getElementById('settings-api-key').value.trim();
            localStorage.setItem('pyclaw_api_key', apiKey);
            const provider = document.getElementById('provider-select').value;
            const model = provider === 'deepseek'
                ? document.getElementById('model-select').value
                : document.getElementById('custom-model-input').value;
            const endpoint = document.getElementById('custom-endpoint').value;
            sendConfigToBackend(provider, apiKey, model, endpoint);
        }

        function sendConfigToBackend(provider, apiKey, model, endpoint) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                // 等连接后再发送
                const checkConn = setInterval(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        clearInterval(checkConn);
                        ws.send(JSON.stringify({
                            type: 'set_config',
                            provider: provider,
                            api_key: apiKey,
                            model: model,
                            base_url: endpoint
                        }));
                    }
                }, 500);
                return;
            }
            ws.send(JSON.stringify({
                type: 'set_config',
                provider: provider,
                api_key: apiKey,
                model: model,
                base_url: endpoint
            }));
        }

        // 加载已保存的配置
        function loadSavedConfig() {
            const provider = localStorage.getItem('pyclaw_provider');
            const model = localStorage.getItem('pyclaw_model');
            const endpoint = localStorage.getItem('pyclaw_endpoint');
            const apiKey = localStorage.getItem('pyclaw_api_key');
            const configured = localStorage.getItem('pyclaw_configured');
            
            if (provider) document.getElementById('provider-select').value = provider;
            if (endpoint) document.getElementById('custom-endpoint').value = endpoint;
            if (apiKey) document.getElementById('settings-api-key').value = apiKey;
            
            if (configured) {
                onProviderChange();
                if (provider === 'deepseek' && model) {
                    document.getElementById('model-select').value = model;
                } else if (provider === 'other' && model) {
                    document.getElementById('custom-model-input').value = model;
                }
            }
        }

        // 初始化连接
        loadSavedConfig();
        checkWizard();
        connectWebSocket();

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
                container.innerHTML = '<div style="color: #8b949e; font-size: 12px;" data-i18n="noSessionsLabel">暂无会话</div>';
                return;
            }
            
            const t = translations[currentLang];
            sessions.forEach((sid, index) => {
                const history = JSON.parse(localStorage.getItem('pyclaw_history_' + sid) || '[]');
                const msgCount = history.filter(m => m.type === 'user' || m.type === 'assistant').length;
                const isCurrent = sid === sessionId;
                
                const div = document.createElement('div');
                const borderColor = isCurrent ? '#58a6ff' : '#30363d';
                const bgColor = isCurrent ? '#1f6feb22' : '#0d1117';
                const leftBorder = isCurrent ? '3px solid #58a6ff' : '3px solid transparent';
                div.style.cssText = 'padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; font-size: 12px; background: ' + bgColor + '; border-top: 1px solid ' + borderColor + '; border-right: 1px solid ' + borderColor + '; border-bottom: 1px solid ' + borderColor + '; border-left: ' + leftBorder + '; cursor: pointer; position: relative; padding-right: 36px;';
                
                const currentText = isCurrent ? '<span style="color: #58a6ff; font-weight: 600; margin-left: 8px;">● ' + (currentLang === 'zh' ? '当前' : 'Current') + '</span>' : '';
                
                div.innerHTML = '<span>' + sid.substring(0, 12) + '...</span>' +
                    '<span style="color: #8b949e; margin-left: 6px;">' + msgCount + ' ' + t.msgCountLabel + '</span>' +
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
            const t = translations[currentLang];
            if (!confirm(t.deleteConfirmLabel)) return;
            
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

        // 加载模型设置
        function loadModelSetting() {
            const select = document.getElementById('model-select');
            const savedModel = localStorage.getItem('pyclaw_model');
            if (savedModel) {
                select.value = savedModel;
            } else {
                // 第一次使用，默认选中第一个（V4 Flash）
                select.value = 'deepseek-v4-flash';
            }
        }

        // 保存模型设置（实时生效）
        function saveModelSetting() {
            const provider = document.getElementById('provider-select').value;
            let model;
            if (provider === 'deepseek') {
                model = document.getElementById('model-select').value;
            } else {
                model = document.getElementById('custom-model-input').value.trim();
            }
            localStorage.setItem('pyclaw_model', model);
            
            const endpoint = document.getElementById('custom-endpoint').value;
            const apiKey = localStorage.getItem('pyclaw_api_key') || '';
            
            // 通过 WebSocket 发送到后端，实时更新
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'set_config',
                    provider: provider,
                    api_key: apiKey,
                    model: model,
                    base_url: endpoint
                }));
            }
            
            // 显示保存成功提示
            const status = document.getElementById('model-status');
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 2000);
        }

        // 页面加载时恢复模型设置
        loadModelSetting();

        // 注册 Service Worker（PWA）
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }


    </script>
</body>
</html>
    """)

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
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False)
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
    parser.add_argument("--host", type=str, default="::", help="监听地址")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["PYCLAW_DATA_DIR"] = args.data_dir

    uvicorn.run(app, host=args.host, port=args.port)
