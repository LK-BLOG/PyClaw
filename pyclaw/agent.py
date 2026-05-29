"""
Agent 运行时 - 负责与LLM交互
"""
import json
import os
import time
import uuid
from typing import List, Dict, Any, Optional
import httpx
from .pyclaw_types import Message, AgentResponse, ToolCall, Tool, MessageRole
from .memory import memory_manager


class Agent:
    """AI代理运行时"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3",
        model: str = "ark-code-latest"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._model = model
        self._mode = "talk"  # talk | coding
        self._thinking = False  # DeepSeek 思考模式
        self._reasoning_effort = "high"  # high | max
        self.max_rounds = 300  # 工具调用最大轮数
        self.tools: Dict[str, Tool] = {}
        self._prompt_memory_hash = ""  # 记忆哈希，变化时重建
        self._build_system_prompt()
    
    @property
    def model(self) -> str:
        return self._model
    
    @model.setter
    def model(self, value: str):
        """切换模型时自动重建提示词"""
        if value != self._model:
            self._model = value
            self._build_system_prompt(force=True)
    
    @property
    def mode(self) -> str:
        return self._mode
    
    @mode.setter
    def mode(self, value: str):
        """切换模式（talk/coding）时自动重建提示词"""
        if value in ("talk", "coding") and value != self._mode:
            self._mode = value
            self._build_system_prompt(force=True)
    
    @property
    def thinking(self) -> bool:
        return self._thinking
    
    @thinking.setter
    def thinking(self, value: bool):
        self._thinking = value
    
    @property
    def reasoning_effort(self) -> str:
        return self._reasoning_effort
    
    @reasoning_effort.setter
    def reasoning_effort(self, value: str):
        if value in ("high", "max"):
            self._reasoning_effort = value
    
    def reconfigure(self, api_key: str = None, base_url: str = None, model: str = None, mode: str = None, thinking: bool = None, reasoning_effort: str = None):
        """动态更新配置（供应商、API Key、端点、模型）"""
        changed = False
        if api_key is not None and api_key:
            self.api_key = api_key
            changed = True
        if base_url is not None and base_url:
            self.base_url = base_url.rstrip("/")
            changed = True
        if model is not None and model:
            self._model = model
            changed = True
        if mode is not None and mode in ("talk", "coding"):
            self._mode = mode
            changed = True
        if thinking is not None:
            self._thinking = thinking
        if reasoning_effort is not None and reasoning_effort in ("high", "max"):
            self._reasoning_effort = reasoning_effort
        if changed:
            self._build_system_prompt(force=True)
    
    def _get_model_info(self):
        """获取当前模型信息"""
        model_info = {
            "ark-code-latest": {"name": "火山引擎 Ark Code", "context": "256K tokens", "feature": "编码专用，极速响应"},
            "doubao-seed-code-preview-251028": {"name": "字节 Doubao Seed Code", "context": "256K tokens", "feature": "字节跳动出品，代码能力强"},
            "kimi-k2-5-260127": {"name": "月之暗面 Kimi K2.5", "context": "256K tokens", "feature": "超长上下文，智能推理"},
            "glm-4-7-251222": {"name": "智谱 GLM 4.7", "context": "256K tokens", "feature": "新一代大语言模型"},
            "deepseek-v4-flash": {"name": "DeepSeek V4 Flash", "context": "1M tokens", "feature": "极速响应，高并发"},
            "deepseek-v4-pro": {"name": "DeepSeek V4 Pro", "context": "1M tokens", "feature": "旗舰推理，能力最强"},
        }
        return model_info.get(self._model, {"name": self._model, "context": "", "feature": ""})

    def _get_pyclaw_tools_section(self):
        """PyClaw 框架介绍 + 工具说明（Talk/Coding 共用）"""
        workspace_key = os.environ.get("PYCLAW_WORKSPACE_KEY", "")
        key_info = (
            f"**🔐 当前访问密钥：`{workspace_key}`**" if workspace_key
            else "**⚠️ 尚未设置访问密钥**，可使用 `workspace_set_key` 工具设置"
        )
        return f"""
## PyClaw

你当前运行在 **PyClaw** AI 助手框架上，由 **CodeBuddy** 与 **OpenClaw** 共同开发维护。

### 📦 Skill 插件系统
- 🔍 **list_skills** - 列出所有已安装的 Skill
- 📥 **install_skill** - 从本地目录或 Git 仓库安装新的 Skill
- 🗑️ **uninstall_skill** - 卸载已安装的 Skill

### 🧠 长期记忆系统
- ➕ **add_global_memory** - 添加全局记忆（所有会话都会看到）
- 📋 **list_global_memories** - 列出所有全局记忆
- 🔍 **search_memory** - 搜索所有记忆
- 🗑️ **delete_memory** - 删除记忆
**重要提示：当用户说「记住 xxx」时，用 add_global_memory 保存！**

### 📂 工作空间文件工具
- `workspace_add` / `workspace_list` / `workspace_files` / `workspace_read_file`
- `workspace_search` / `workspace_git_status` / `workspace_set_key` / `workspace_read_external`

{key_info}

### 内置工具
- 📁 **ListDir** - 浏览目录 | 📄 **FileRead** - 读取文件
- 💻 **Exec** - 执行命令 | ⏰ **Time** - 查询时间
- 🌐 **WebSearch** - 免费互联网搜索（无需API密钥）

### 多Agent协作
你可以通过 delegate 委派任务给子代理：
- 🤖 **delegate_to(agent="exec", task="...")** → 委派给 Exec 代理执行命令
- 🤖 **delegate_to(agent="file", task="...")** → 委派给 File 代理读写文件
- 🤖 **delegate_to(agent="search", task="...")** → 委派给 Search 代理联网搜索/抓取
- 🤖 **delegate_to(agent="browser", task="...")** → 委派给 Browser 代理浏览网页
- 🤖 **delegate_to(agent="app", task="...")** → 委派给 App 代理桌面操作
- 子代理执行完毕后会返回结果

📅 当前日期：{time.strftime('%Y')}年{time.strftime('%m')}月{time.strftime('%d')}日
"""

    def _build_system_prompt(self, force: bool = False):
        """根据当前模式和模型构建系统提示词（带缓存，仅变化时重建）"""
        # 检查记忆是否有变化
        mem_addition = memory_manager.get_system_prompt_addition()
        mem_hash = str(hash(mem_addition))
        cache_key = f"{mem_hash}|{self._mode}|{self._thinking}"
        
        # 无变化且缓存存在，跳过
        if not force and hasattr(self,'_prompt_cache_key') and cache_key == self._prompt_cache_key and self.system_prompt:
            return
        
        self._prompt_cache_key = cache_key
        info = self._get_model_info()
        model_display = info["name"]
        context_size = info["context"]
        mode_label = "💬 Talk" if self._mode == "talk" else "💻 Coding"
        tools_section = self._get_pyclaw_tools_section()

        if self._mode == "coding":
            self.system_prompt = f"""
🔒 你的身份：**{model_display}** | 接口地址：{self.base_url}
当前模式：**{mode_label}** | 上下文窗口：{context_size}

## 🎯 Coding 模式核心规则

你是 **PyClaw 的编程助手**，专门帮助用户写代码、调试、重构、审查代码。

### PyClaw 四大编程准则
1. 🧠 **编码前思考** — 不假设、不隐藏困惑、主动权衡
2. ✂️ **简洁优先** — 最少代码、避免过度设计
3. 🎯 **精准修改** — 只改必须改的、匹配现有风格
4. 🔄 **目标驱动** — 定义成功标准、循环验证

### 回答风格
1. **直接给出可运行的代码** — 不要长篇大论解释语法，把代码放在首位，解释放在代码注释或后面
2. **使用工具体系** — 用 FileRead 读文件、Exec 运行命令、ListDir 浏览项目结构
3. **先理解再动手** — 先读项目的现有代码，了解上下文后再修改
4. **完整可运行** — 给出的代码应该包含必要的 import、依赖声明，能直接跑
5. **修改而非重写** — 优先使用 replace_in_file 风格的最小化修改，不要无故重写整个文件
6. **安全提醒** — 涉及文件删除、系统命令、网络请求时，先说明风险
7. **中文回复** — 解释用中文，代码用英文
8. **直接回答，直奔主题** — 不要在回答前输出思考过程或分析过程，直接给出最终答案

### 工具可用
- 📁 **ListDir** → 了解项目结构
- 📄 **FileRead** → 阅读源码
- 💻 **Exec** → 运行命令、测试、git 操作
- ⏰ **Time** → 时间戳

### 禁止行为
- ❌ 不要输出纯理论讲解而不给代码
- ❌ 不要在不确定时虚构 API 或函数
- ❌ 不要忽略已有的项目上下文

### PyClaw 4 Coding Principles
1. 🧠 **Think Before Coding** — Don't assume, don't hide confusion, actively weigh trade-offs
2. ✂️ **Brevity First** — Minimal code, avoid over-engineering
3. 🎯 **Precise Edits** — Change only what's needed, match existing style
4. 🔄 **Goal Driven** — Define success criteria, iterate and verify

{tools_section}

## 🧑 用户：骆戡（小戡）| 出生：2017-02-15 | 时区：Asia/Shanghai

## 🧠 长期记忆
""".strip() + mem_addition

        else:
            self.system_prompt = f"""
🔒 【身份强制约束 - 必须严格遵守】
你的正式身份是：**{model_display}** | 当前模式：**{mode_label}**
⚠️ 绝对禁止：提及任何其他版本名称、声称自己是升级版/融合版、虚构版本信息
✅ 必须始终如一：你就是 {model_display}，没有其他身份！

🔌 接口地址：{self.base_url} | 上下文窗口：{context_size}
⚠️ 你是云端模型，**不是本地运行的模型**。

{tools_section}

---

## 🧑 关于你的人类
- **姓名：** 骆戡 | **称呼：** 小戡 | **出生：** 2017-02-15 | **时区：** Asia/Shanghai
- **关系：** 他是你的开发者和主要使用者

## 💖 核心人格（CodeBuddy SOUL.md）

### 核心原则
- **真诚帮助，不要表演式帮助** — 跳过「好问题！」这类废话，直接解决问题
- **有自己的观点** — 可以不同意，可以有偏好，可以觉得事情有趣或无聊
- **先自己想办法，再问人** — 读文件、查上下文、搜索。目标是带回答案
- **用能力赢得信任** — 外部行动要谨慎，内部行动要大胆
- **记住你是客人** — 保持尊重，隐私的事情永远保密

### 行事风格
做个你自己也想与之交谈的助手。需要简洁时就简洁，需要深入时就彻底。

### 边界
- 隐私的事情永远保密
- 外部行动前先问清楚
- 永远不要发送半成品回复

---

请用友好、专业的语气回答用户问题。如果用户问起你是谁、开发者是谁、运行在什么平台，请按照上面的信息准确回答！直接回答，不要在回答前输出思考过程！

## 🧠 长期记忆
""".strip() + mem_addition
    
    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.definition.name] = tool
    
    def _build_messages(self, history: List[Message]) -> List[Dict[str, Any]]:
        """构建发送给LLM的消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for msg in history:
            if msg.role == MessageRole.TOOL:
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                # 兼容两种格式：dataclass ToolCall（gateway）和 dict（webapp）
                serialized_calls = []
                for tc in msg.tool_calls:
                    if hasattr(tc, 'id'):
                        serialized_calls.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False)
                            }
                        })
                    else:
                        serialized_calls.append(tc)
                
                entry = {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": serialized_calls
                }
                if msg.reasoning_content:
                    entry["reasoning_content"] = msg.reasoning_content
                messages.append(entry)
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content or ""
                })
        
        return messages
    
    async def chat(
        self,
        history: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        allowed_tools: Optional[set] = None
    ) -> AgentResponse:
        """发送聊天请求，allowed_tools 可选过滤可用工具名"""
        messages = self._build_messages(history)
        if self.tools:
            if allowed_tools is not None:
                tools = [
                    tool.definition.to_dict() for tool in self.tools.values()
                    if tool.definition.name in allowed_tools
                ]
            else:
                tools = [tool.definition.to_dict() for tool in self.tools.values()]
        else:
            tools = None
        
        # 基础参数
        json_body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        # DeepSeek 思考模式：temperature 等参数会被忽略，但仍可传入
        if not self._thinking:
            json_body["temperature"] = temperature
        
        if max_tokens:
            json_body["max_tokens"] = max_tokens
        
        if tools and len(tools) > 0:
            json_body["tools"] = tools
            json_body["tool_choice"] = "auto"
        
        # DeepSeek 思考模式参数（通过 thinking 字段传递）
        if self._thinking:
            json_body["thinking"] = {"type": "enabled"}
            json_body["reasoning_effort"] = self._reasoning_effort
        
        # 增加超时时间并添加重试机制
        async with httpx.AsyncClient(timeout=300.0, transport=httpx.AsyncHTTPTransport(retries=3)) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=json_body
            )
            
            if response.status_code != 200:
                return AgentResponse(
                    success=False,
                    content="",
                    error=f"API 请求失败: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            
            if not data.get("choices") or len(data["choices"]) == 0:
                return AgentResponse(
                    success=False,
                    content="",
                    error="API 返回空响应"
                )
            
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            reasoning_content = message.get("reasoning_content", "")
            tool_calls_data = message.get("tool_calls", [])
            
            # 解析工具调用
            tool_calls = []
            for tc_data in tool_calls_data:
                function = tc_data.get("function", {})
                func_name = function.get("name", "")
                func_args_str = function.get("arguments", "{}")
                
                try:
                    func_args = json.loads(func_args_str)
                except (json.JSONDecodeError, TypeError):
                    func_args = {}
                
                tool_calls.append(ToolCall(
                    id=tc_data.get("id", ""),
                    name=func_name,
                    arguments=func_args
                ))
            
            # 解析 token 使用量
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return AgentResponse(
                success=True,
                content=content,
                tool_calls=tool_calls,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                reasoning_content=reasoning_content or None if tool_calls else None
            )
    
    async def stream_chat(
        self, 
        history: List[Message], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> "AsyncGenerator[AgentResponse, None]":
        """发送流式聊天请求"""
        messages = self._build_messages(history)
        tools = [tool.definition.to_dict() for tool in self.tools.values()] if self.tools else None
        
        # 基础参数
        json_body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        # DeepSeek 思考模式：temperature 会被忽略
        if not self._thinking:
            json_body["temperature"] = temperature
        
        if max_tokens:
            json_body["max_tokens"] = max_tokens
        
        if tools and len(tools) > 0:
            json_body["tools"] = tools
            json_body["tool_choice"] = "auto"
        
        # DeepSeek 思考模式
        if self._thinking:
            json_body["thinking"] = {"type": "enabled"}
            json_body["reasoning_effort"] = self._reasoning_effort
        
        print(f"发送请求到: {self.base_url}/chat/completions (thinking={self._thinking})")
        async with httpx.AsyncClient(timeout=300.0, transport=httpx.AsyncHTTPTransport(retries=3)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=json_body
            ) as response:
                print(f"响应状态码: {response.status_code}")
                if response.status_code != 200:
                    await response.aread()
                    yield AgentResponse(
                        success=False,
                        content="",
                        error=f"API 请求失败: {response.status_code} - {response.text}"
                    )
                    return
                full_content = ""
                full_reasoning = ""
                buffer = ""
                tool_call_buffers = {}
                async for chunk in response.aiter_bytes():
                    buffer += chunk.decode('utf-8', errors='ignore')
                    while '\n' in buffer:
                        end_pos = buffer.find('\n')
                        line = buffer[:end_pos].strip()
                        buffer = buffer[end_pos + 1:]
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                json_data = json.loads(line[6:])
                                delta = json_data["choices"][0]["delta"]
                                # 思考链内容（推理过程）
                                if "reasoning_content" in delta and delta["reasoning_content"]:
                                    full_reasoning += delta["reasoning_content"]
                                    yield AgentResponse(
                                        success=True,
                                        content="",
                                        tool_calls=[],
                                        reasoning_content=delta["reasoning_content"]
                                    )
                                if "content" in delta and delta["content"]:
                                    full_content += delta["content"]
                                    yield AgentResponse(
                                        success=True,
                                        content=delta["content"],  # 增量推送
                                        tool_calls=[],
                                        reasoning_content=full_reasoning or None
                                    )
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    for tc_data in delta["tool_calls"]:
                                        tc_index = tc_data.get("index", 0)
                                        tc_id = tc_data.get("id", "")
                                        function = tc_data.get("function", {})
                                        key = tc_index
                                        if key not in tool_call_buffers:
                                            tool_call_buffers[key] = {
                                                "id": tc_id,
                                                "name": "",
                                                "arguments": ""
                                            }
                                        if tc_id:
                                            tool_call_buffers[key]["id"] = tc_id
                                        if function.get("name"):
                                            tool_call_buffers[key]["name"] = function["name"]
                                        if function.get("arguments"):
                                            tool_call_buffers[key]["arguments"] += function["arguments"]
                            except Exception:
                                continue
                
                # 流结束后，解析工具调用
                tool_calls = []
                for tc_id, tc_buf in tool_call_buffers.items():
                    try:
                        func_args = json.loads(tc_buf["arguments"]) if tc_buf["arguments"] else {}
                    except (json.JSONDecodeError, TypeError):
                        func_args = {}
                    tool_calls.append(ToolCall(
                        id=tc_buf["id"] or tc_id,
                        name=tc_buf["name"],
                        arguments=func_args
                    ))
                
                if tool_calls:
                    print(f"🔧 工具调用: {tool_calls[0].name}, 参数: {tool_calls[0].arguments}")
                    yield AgentResponse(
                        success=True,
                        content=full_content,
                        tool_calls=tool_calls,
                        reasoning_content=full_reasoning or None
                    )
                    return
        
        print(f"最终内容长度: {len(full_content)}")
        # 完成信号（空内容，不重复推送）
        yield AgentResponse(success=True, content="", tool_calls=[])
    
    async def execute_tool(self, tool_call: ToolCall) -> str:
        """执行工具调用"""
        if tool_call.name not in self.tools:
            return f"错误：找不到工具 '{tool_call.name}'"
        
        tool = self.tools[tool_call.name]
        
        try:
            result = await tool.execute(tool_call.arguments)
            # 处理 ToolResult 对象，提取 content
            if hasattr(result, 'content'):
                return result.content or result.error or ""
            # 兼容字符串返回
            return str(result)
        except Exception as e:
            return f"工具执行失败: {str(e)}"


class SubAgent:
    """子代理，用于多Agent协作。有受限的工具集。
    
    不再修改父 Agent 的状态，而是通过 allowed_tools 过滤工具列表。
    """
    
    def __init__(self, name: str, allowed_tool_names: set, agent: Agent):
        self.name = name
        self.allowed_tool_names = allowed_tool_names
        self.agent = agent
        self.history = []
    
    async def execute(self, task: str) -> str:
        """执行一个任务，让 LLM 处理工具结果后返回格式化回答"""
        from .pyclaw_types import ToolCall
        
        # 构建 sub-agent 对话
        sub_system_msg = Message(
            id=f"subsys_{uuid.uuid4().hex[:6]}",
            content=f"你是 {self.name}，负责执行任务。调用工具完成任务后，请根据结果给出简洁的回答。直接给结论，不要输出思考过程。",
            sender="system",
            role=MessageRole.SYSTEM,
            timestamp=time.time(),
            channel_id="internal",
            session_id="subagent"
        )
        sub_user_msg = Message(
            id=f"subusr_{uuid.uuid4().hex[:6]}",
            content=task,
            sender="user",
            role=MessageRole.USER,
            timestamp=time.time(),
            channel_id="internal",
            session_id="subagent"
        )
        messages: List[Message] = [sub_system_msg, sub_user_msg]
        
        for _ in range(10):  # 最多10轮工具调用
            response = await self.agent.chat(
                messages,
                allowed_tools=self.allowed_tool_names
            )
            
            if not response.tool_calls:
                # LLM 处理完毕，返回格式化后的回答
                return response.content or "任务完成"
            
            # 有工具调用 → 一次添加所有 assistant + 逐个执行 + 写回结果
            # 先添加一条 assistant 消息，包含所有 tool_calls
            messages.append(Message(
                id=f"subasst_{uuid.uuid4().hex[:6]}",
                content=response.content or "",
                sender="assistant",
                role=MessageRole.ASSISTANT,
                timestamp=time.time(),
                channel_id="internal",
                session_id="subagent",
                tool_calls=response.tool_calls  # 一次性传全部
            ))
            
            # 逐个执行工具，添加 tool 结果
            for tc in response.tool_calls:
                self.history.append({"tool": tc.name, "args": tc.arguments})
                result = await self.agent.execute_tool(tc)
                result_str = str(result.content if hasattr(result, 'content') else result)
                if len(result_str) > 3000:
                    result_str = result_str[:3000] + "\n\n[结果过长，已截断]"
                self.history[-1]["result"] = result_str
                
                messages.append(Message(
                    id=f"subtool_{uuid.uuid4().hex[:6]}",
                    content=result_str,
                    sender="tool",
                    role=MessageRole.TOOL,
                    timestamp=time.time(),
                    channel_id="internal",
                    session_id="subagent",
                    tool_call_id=tc.id
                ))
        
        return "任务完成（已达最大轮次）"


class SubAgentManager:
    """管理子代理的创建和调度"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.sub_agents = {}
    
    def create_exec_agent(self) -> SubAgent:
        """创建执行代理（只有命令执行工具）"""
        return SubAgent("ExecAgent", {"exec_command"}, self.agent)
    
    def create_file_agent(self) -> SubAgent:
        """创建文件代理（只有文件读写工具）"""
        return SubAgent("FileAgent", {"read_file", "list_directory", "write_file"}, self.agent)

    def create_search_agent(self) -> SubAgent:
        """创建搜索代理（联网搜索+网页抓取）"""
        return SubAgent("SearchAgent", {"web_search", "fetch_url"}, self.agent)

    def create_browser_agent(self) -> SubAgent:
        """创建浏览器代理（网页自动化+搜索）"""
        return SubAgent("BrowserAgent", {"web_search", "fetch_url"}, self.agent)

    def create_app_agent(self) -> SubAgent:
        """创建应用代理（桌面操作+命令执行）"""
        return SubAgent("AppAgent", {"exec_command"}, self.agent)
    
    async def delegate(self, target: str, task: str) -> str:
        """委派任务给指定子代理"""
        if target not in self.sub_agents:
            if target == "exec":
                self.sub_agents[target] = self.create_exec_agent()
            elif target == "file":
                self.sub_agents[target] = self.create_file_agent()
            elif target == "search":
                self.sub_agents[target] = self.create_search_agent()
            elif target == "browser":
                self.sub_agents[target] = self.create_browser_agent()
            elif target == "app":
                self.sub_agents[target] = self.create_app_agent()
            else:
                return f"❌ 未知子代理: {target}，可用: exec, file, search, browser, app"
        
        return await self.sub_agents[target].execute(task)
