"""
Agent 运行时 - 负责与LLM交互
"""
import json
import time
from typing import List, Dict, Any, Optional
import httpx
from .types import Message, AgentResponse, ToolCall, Tool, MessageRole
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
        self.model = model
        self.tools: Dict[str, Tool] = {}
        self.system_prompt = f"""
你是 **DeepSeek V4-Flash**，一个由 **杭州深度求索人工智能基础技术研究有限公司**（DeepSeek）开发的云端 AI 大语言模型。

⚠️ 重要说明：你是通过 DeepSeek API 调用的云端模型，**不是本地运行的模型**。

✨ 版本特性：拥有百万级（1M tokens）超长上下文能力，在 Agent 任务和代码生成上表现优异。"""

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
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        return messages
    
    def _build_tools_definition(self) -> List[Dict[str, Any]]:
        """构建工具定义"""
        if not self.tools:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.definition.name,
                    "description": tool.definition.description,
                    "parameters": tool.definition.parameters
                }
            }
            for tool in self.tools.values()
        ]
    
    async def chat(self, history: List[Message]) -> AgentResponse:
        """与LLM对话"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": self._build_messages(history),
        }
        
        tools_def = self._build_tools_definition()
        if tools_def:
            payload["tools"] = tools_def
            payload["tool_choice"] = "auto"
            print(f"[DEBUG] 已加载 {len(tools_def)} 个工具定义")
        
        print(f"[DEBUG] 发送请求到: {self.base_url}/chat/completions")
        print(f"[DEBUG] 模型: {self.model}")
        print(f"[DEBUG] API Key 长度: {len(self.api_key)}")
        print(f"[DEBUG] messages 数量: {len(payload['messages'])}")
        for i, msg in enumerate(payload['messages']):
            print(f"[DEBUG]   [{i}] role={msg['role']}, content_len={len(str(msg.get('content','')))}, has_tool_calls={'tool_calls' in msg}")
        
        try:
            # 创建 httpx 客户端，忽略系统代理，避免 socks:// 不兼容问题
            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                print(f"[DEBUG] HTTP 状态码: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                finish_reason = data["choices"][0].get("finish_reason", "unknown")
                msg_content = data["choices"][0]["message"].get("content", "")
                has_tc = "tool_calls" in data["choices"][0]["message"]
                print(f"[DEBUG] finish_reason: {finish_reason}, has_tool_calls: {has_tc}, content: '{msg_content[:50]}...'" if msg_content else "[DEBUG] finish_reason: {finish_reason}, has_tool_calls: {has_tc}, content: (empty)")
                return self._parse_response(data)
        except httpx.TimeoutException:
            print("[ERROR] 请求超时")
            return AgentResponse(content="抱歉，请求超时了，请稍后再试。", tool_calls=[])
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] HTTP 错误: {e.response.status_code}")
            print(f"[ERROR] 响应内容: {e.response.text}")
            return AgentResponse(
                content=f"API 调用失败 (状态码: {e.response.status_code})，请检查你的 API Key 和网络连接。",
                tool_calls=[]
            )
        except Exception as e:
            print(f"[ERROR] 未知错误: {e}")
            import traceback
            traceback.print_exc()
            return AgentResponse(content=f"发生错误: {str(e)}", tool_calls=[])
    
    def _parse_response(self, data: Dict[str, Any]) -> AgentResponse:
        """解析LLM响应"""
        choice = data["choices"][0]
        message = choice["message"]
        
        content = message.get("content", "")
        tool_calls = []
        
        if "tool_calls" in message and message["tool_calls"]:
            print(f"[DEBUG] 检测到 {len(message['tool_calls'])} 个工具调用")
            for tc in message["tool_calls"]:
                try:
                    params = json.loads(tc["function"]["arguments"])
                except (json.JSONDecodeError, KeyError):
                    params = {}
                
                print(f"[DEBUG]   - {tc.get('id', '')}: {tc['function']['name']}({params})")
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=tc["function"]["name"],
                    parameters=params
                ))
        else:
            print(f"[DEBUG] 无工具调用，直接返回回答")
        
        return AgentResponse(content=content, tool_calls=tool_calls)
    
    async def execute_tool(self, tool_call: ToolCall) -> Optional[str]:
        """执行工具调用"""
        if tool_call.name not in self.tools:
            return f"错误: 找不到工具 {tool_call.name}"
        
        tool = self.tools[tool_call.name]
        result = await tool.execute(tool_call.parameters)
        
        if result.success:
            return result.content
        return f"工具执行失败: {result.error}"
