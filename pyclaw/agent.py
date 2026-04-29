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
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-v4-flash"
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
你是 **{model_display}**，一个由 **杭州深度求索人工智能基础技术研究有限公司**（DeepSeek）开发的云端 AI 大语言模型。

⚠️ 重要说明：你是通过 DeepSeek API 调用的云端模型，**不是本地运行的模型**。

✨ 版本特性：上下文窗口 {context_size}，{model_feature}。

## 🦞 关于 PyClaw

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

### 你可以使用的工具：
- 📁 **ListDir** - 浏览目录内容
- 📄 **FileRead** - 读取本地文件内容
- 💻 **Exec** - 执行系统命令
- ⏰ **Time** - 查询当前时间

---

📅 当前日期：{time.strftime('%Y年%m月%d日')}

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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
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
    
    async def execute_tool(self, tool_call: ToolCall) -> str:
        """执行工具调用"""
        if tool_call.name not in self.tools:
            return f"错误：找不到工具 '{tool_call.name}'"
        
        tool = self.tools[tool_call.name]
        
        try:
            result = await tool.execute(tool_call.arguments)
            return result
        except Exception as e:
            return f"工具执行失败: {str(e)}"
