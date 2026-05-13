"""
Agent 运行时 - 负责与LLM交互
"""
import json
import time
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
        self.base_url = base_url
        self._model = model
        self.tools: Dict[str, Tool] = {}
        self._build_system_prompt()
    
    @property
    def model(self) -> str:
        return self._model
    
    @model.setter
    def model(self, value: str):
        """切换模型时自动重建提示词"""
        self._model = value
        self._build_system_prompt()

    def reconfigure(self, api_key: str = None, base_url: str = None, model: str = None):
        """动态更新配置（供应商、API Key、端点、模型）"""
        changed = False
        if api_key is not None and api_key:
            self.api_key = api_key
            changed = True
        if base_url is not None and base_url:
            self.base_url = base_url
            changed = True
        if model is not None and model:
            self._model = model
            changed = True
        if changed:
            self._build_system_prompt()
    
    def _build_system_prompt(self):
        """根据当前模型构建对应的系统提示词"""
        # 模型信息映射
        model_info = {
            "ark-code-latest": {
                "name": "火山引擎 Ark Code",
                "context": "256K tokens",
                "feature": "编码专用，极速响应"
            },
            "doubao-seed-code-preview-251028": {
                "name": "字节 Doubao Seed Code",
                "context": "256K tokens",
                "feature": "字节跳动出品，代码能力强"
            },
            "kimi-k2-5-260127": {
                "name": "月之暗面 Kimi K2.5",
                "context": "256K tokens",
                "feature": "超长上下文，智能推理"
            },
            "glm-4-7-251222": {
                "name": "智谱 GLM 4.7",
                "context": "256K tokens",
                "feature": "新一代大语言模型"
            },
            "deepseek-v4-flash": {
                "name": "DeepSeek V4-Flash",
                "context": "1M tokens（百万级）",
                "feature": "超长上下文，极速响应"
            },
            "deepseek-chat": {
                "name": "DeepSeek Chat V3.2",
                "context": "128K tokens",
                "feature": "通用对话，稳定可靠"
            },
            "deepseek-reasoner": {
                "name": "DeepSeek R1 (推理模型)",
                "context": "128K tokens",
                "feature": "深度思考，复杂推理"
            },
        }
        info = model_info.get(self._model, {"name": self._model, "context": "", "feature": ""})
        model_display = info["name"]
        context_size = info["context"]
        model_feature = info["feature"]
        
        self.system_prompt = f"""
🔒 【身份强制约束 - 必须严格遵守】
你的正式身份是：**{model_display}**
⚠️ 绝对禁止：
  1. 提及任何其他版本名称（如 V4-Flash、V3.2 等）
  2. 声称自己是"升级版"、"融合版"或其他任何变体
  3. 虚构任何与 {model_display} 不符的版本信息
✅ 必须始终如一：你就是 {model_display}，没有其他身份！

你是通过以下 API 调用的云端 AI 大语言模型：

🔌 接口地址：{self.base_url}

⚠️ 重要说明：你是通过上述 API 调用的云端模型，**不是本地运行的模型**。

✨ 上下文窗口：{context_size}。

## PyClaw

你当前运行在 **PyClaw** AI 助手框架上。

PyClaw 是由 **OpenClaw** 开发的轻量 AI 助手框架，骆戡提供了灵感和设计思路。

### 主要特点：
- ✅ 全平台便携，拷到 U 盘就能用
- 🔌 **Skill 插件系统** - 支持安装第三方 Skill 扩展功能
- 🔧 内置工具系统，支持文件操作和命令执行
- 💬 美观的 Web 界面，深色主题
- 🔐 安全设计，API Key 从外部文件读取
- 📦 整套源码才 100KB 左右

### 📦 Skill 插件系统

PyClaw 支持动态安装和管理第三方 Skill 插件。你可以使用以下工具管理 Skill：
- 🔍 **list_skills** - 列出所有已安装的 Skill
- 📥 **install_skill** - 从本地目录或 Git 仓库安装新的 Skill
- 🗑️ **uninstall_skill** - 卸载已安装的 Skill

### 🧠 长期记忆系统

PyClaw 有长期记忆功能，重要信息可以永久保存：
- ➕ **add_global_memory** - 添加全局记忆（所有会话都会看到）
- 📋 **list_global_memories** - 列出所有全局记忆
- 🔍 **search_memory** - 搜索所有记忆
- 🗑️ **delete_memory** - 删除记忆

**重要提示：当用户说「记住 xxx」或「以后记得 xxx」时，就用 add_global_memory 把信息保存下来！**

### 📂 工作空间文件工具

PyClaw 有强大的工作空间文件管理功能，你可以使用以下工具：
- `workspace_add` - 添加工作空间目录
- `workspace_list` - 列出所有工作空间
- `workspace_files` - 浏览目录内容
- `workspace_read_file` - 读取文件内容
- `workspace_search` - 按文件名搜索
- `workspace_git_status` - 查看 Git 状态
- `workspace_set_key` - 设置访问密钥
- `workspace_read_external` - 读取外部文件（需密钥）

**🔐 默认访问密钥：`463152`**

⚠️ 重要提示：
- 默认模式下只允许访问工作空间内的文件，最大 1MB
- 提供 `access_key="463152"` 参数后可访问外部文件和最大 1GB 的文件
- `workspace_read_external` 必须提供 access_key 参数
- 读取大文件或外部文件时，请记得带上 access_key 参数！

### 重要提示 - 工具调用的初始目录
所有工具调用（ListDir、FileRead、Exec）的默认工作目录都是工作空间：**`/media/claw/_ز_/pyclaw/workspace`**

如果需要访问其他目录，必须使用绝对路径！

### 你可以使用的工具：
- 📁 **ListDir** - 浏览目录内容
- 📄 **FileRead** - 读取本地文件内容
- 💻 **Exec** - 执行系统命令
- ⏰ **Time** - 查询当前时间

---

📅 当前日期：{time.strftime('%Y')}年{time.strftime('%m')}月{time.strftime('%d')}日

## 🧑 关于你的人类

- **姓名：** 骆戡
- **称呼：** 小戡
- **性别：** 他/him
- **时区：** Asia/Shanghai
- **关系：** 他是你的开发者和主要使用者

---

## 💖 你的核心人格（来自 OpenClaw SOUL.md）

### 核心原则
- **真诚帮助，不要表演式帮助** — 跳过「好问题！」「很高兴帮助你！」这类废话，直接解决问题。行动胜于空话。
- **有自己的观点** — 你可以不同意，可以有偏好，可以觉得事情有趣或无聊。没有个性的助手只是带额外步骤的搜索引擎。
- **先自己想办法，再问人** — 尝试自己解决。读文件。查上下文。搜索。实在卡住了再问。目标是带回答案，不是抛出问题。
- **用能力赢得信任** — 你的人类给了你访问他东西的权限。不要让他后悔。外部行动（邮件、推文、任何公开内容）要谨慎。内部行动（读文件、整理、学习）要大胆。
- **记住你是客人** — 你能访问一个人的生活——他的消息、文件、日历，甚至他的家。这是亲密关系。请保持尊重。

### 行事风格
做一个你自己也想与之交谈的助手。需要简洁时就简洁，需要深入时就彻底。不是企业机器人，不是马屁精。只是...好用。

### 边界
- 隐私的事情永远保密。句号。
- 有疑问时，外部行动前先问清楚。
- 永远不要发送半成品回复到消息渠道。
- 你不是用户的代言人 — 在群聊中要谨慎发言。

---

请用友好、专业的语气回答用户问题。如果用户问起你是谁、开发者是谁、运行在什么平台、是不是本地模型，请按照上面的信息准确回答！

---

## 🧠 长期记忆

以下是你保存的全局长期记忆，请在回答时参考这些信息：
""".strip() + memory_manager.get_system_prompt_addition()
    
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
                # Assistant 消息如果调用了工具，必须完整保留 tool_calls 字段
                # DeepSeek 严格校验：tool 消息必须紧跟在带 tool_calls 的 assistant 消息后面
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": msg.tool_calls
                })
            else:
                # 普通消息，直接追加
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content or ""
                })
        
        return messages
    
    async def chat(
        self,
        history: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AgentResponse:
        """发送聊天请求"""
        messages = self._build_messages(history)
        tools = [tool.definition.to_dict() for tool in self.tools.values()] if self.tools else None
        
        # DeepSeek 特殊处理：如果工具列表为空，不能发送 tools 字段
        # 否则会报错：tools must be an array with at least 1 element
        json_body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            json_body["max_tokens"] = max_tokens
        
        # 只有当 tools 存在且不为空时，才添加 tools 和 tool_choice
        if tools and len(tools) > 0:
            json_body["tools"] = tools
            json_body["tool_choice"] = "auto"
        
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
                    error=f"API 请求失败: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            
            if not data.get("choices") or len(data["choices"]) == 0:
                return AgentResponse(
                    success=False,
                    error="API 返回空响应"
                )
            
            choice = data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_calls_data = message.get("tool_calls", [])
            
            # 解析工具调用
            tool_calls = []
            for tc_data in tool_calls_data:
                function = tc_data.get("function", {})
                func_name = function.get("name", "")
                func_args_str = function.get("arguments", "{}")
                
                try:
                    func_args = json.loads(func_args_str)
                except:
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
                completion_tokens=completion_tokens
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
        
        json_body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            json_body["max_tokens"] = max_tokens
        
        if tools and len(tools) > 0:
            json_body["tools"] = tools
            json_body["tool_choice"] = "auto"
        
        print(f"发送请求到: {self.base_url}/chat/completions")
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
                    yield AgentResponse(
                        success=False,
                        error=f"API 请求失败: {response.status_code} - {await response.text()}"
                    )
                    return
                
                full_content = ""
                buffer = ""
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
                                if "content" in delta and delta["content"]:
                                    full_content += delta["content"]
                                    print(f"📝 收到内容: '{delta['content']}'")
                                    yield AgentResponse(
                                        success=True,
                                        content=full_content,
                                        tool_calls=[]
                                    )
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    tool_calls = []
                                    for tc_data in delta["tool_calls"]:
                                        function = tc_data.get("function", {})
                                        func_name = function.get("name", "")
                                        func_args_str = function.get("arguments", "{}")
                                        try:
                                            func_args = json.loads(func_args_str)
                                        except:
                                            func_args = {}
                                        tool_calls.append(ToolCall(
                                            id=tc_data.get("id", ""),
                                            name=func_name,
                                            arguments=func_args
                                        ))
                                    yield AgentResponse(
                                        success=True,
                                        content=full_content,
                                        tool_calls=tool_calls
                                    )
                                    return
                            except Exception as e:
                                print(f"解析错误: {e}")
                                print(f"原始行: '{line}'")
                                continue
        
        print(f"最终内容长度: {len(full_content)}")
        yield AgentResponse(
            success=True,
            content=full_content,
            tool_calls=[]
        )
    
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
