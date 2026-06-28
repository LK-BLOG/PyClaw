"""
Agent 运行时 - 负责与LLM交互
"""
import json
import os
import platform
import time
import uuid
from typing import List, Dict, Any, Optional
import httpx
import aiohttp
from .pyclaw_types import Message, AgentResponse, ToolCall, Tool, MessageRole
from .memory import memory_manager
from .skill import skill_manager


class Agent:
    """AI代理运行时"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3",
        model: str = "deepseek-v4-flash-free",
        language: str = "zh-CN"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._model = model
        self._mode = "talk"  # talk | coding
        self._thinking = False  # DeepSeek 思考模式
        self._reasoning_effort = "high"  # high | max
        self.language = language  # zh-CN | en-US
        self.max_rounds = 300  # 工具调用最大轮数
        self.tools: Dict[str, Tool] = {}
        self.failover_models: List[str] = []  # 备用模型列表
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
    
    def reconfigure(self, api_key: str = None, base_url: str = None, model: str = None, mode: str = None, thinking: bool = None, reasoning_effort: str = None, failover_models: List[str] = None):
        """动态更新配置（供应商、API Key、端点、模型、备用模型）"""
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
        if failover_models is not None:
            self.failover_models = failover_models
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

    def _build_system_prompt(self, force: bool = False):
        """构建系统提示词（带缓存，仅变化时重建）"""
        mem_addition = memory_manager.get_system_prompt_addition()
        mem_hash = str(hash(mem_addition))
        cache_key = f"{mem_hash}|{self._mode}|{self._thinking}"
        if not force and hasattr(self,'_prompt_cache_key') and cache_key == self._prompt_cache_key and self.system_prompt:
            return

        self._prompt_cache_key = cache_key
        info = self._get_model_info()
        model_display = info["name"]
        context_size = info["context"]
        mode_label = "💬 Talk" if self._mode == "talk" else "💻 Coding"
        en = self.language == "en-US"
        os_display = f"{platform.system()} {platform.release()}"

        # ── 年龄（从生日实时计算，省Token） ──
        _now = time.time()
        _bd = time.strptime("2017-02-15", "%Y-%m-%d")
        _age_now = time.gmtime(_now)
        _age_years = _age_now.tm_year - _bd.tm_year
        if (_age_now.tm_mon, _age_now.tm_mday) < (_bd.tm_mon, _bd.tm_mday):
            _age_years -= 1
        _age_str = f"{_age_years}岁" if self.language == "zh-CN" else f"{_age_years} years old"
        
        # 工具章节（Talk/Coding 共用）
        wk = os.environ.get("PYCLAW_WORKSPACE_KEY", "")
        key_info = f"**🔐 Access Key: `{wk}`**" if en else \
                   (f"**🔐 当前访问密钥：`{wk}`**" if wk else "**⚠️ No access key set — use `workspace_set_key`**" if en else "**⚠️ 尚未设置访问密钥**，可使用 `workspace_set_key` 工具设置")
        decl = skill_manager.get_declarative_skills_content()
        tools_section = f"""
## PyClaw

### Tools
- **ListDir** — browse directories | 📄 **FileRead** — read files
- 💻 **Exec** — run commands | ⏰ **Time** — timestamps
- **WebSearch** — free internet search

### Skills
- list_skills / install_skill / uninstall_skill
- add_global_memory / list_global_memories / search_memory / delete_memory
- 📂 workspace_add / workspace_list / workspace_files / workspace_read_file / workspace_search / workspace_git_status / workspace_set_key

{key_info}

### SubAgents
- **`delegate_to(agent, task)`** — exec/file/search/browser/app

### Declarative Skills
{decl if decl else '(none)'}

📅 {time.strftime('%Y-%m-%d')}"""

        if self._mode == "coding":
            # ── Coding Mode ──
            s_t = [  # style rules: (en, zh)
                ("**Give runnable code** — put code first, explanations afterward",
                 "**直接给出可运行的代码** — 把代码放在首位，解释放后面"),
                ("**Use tools** — FileRead to read, Exec to run, ListDir to browse",
                 "**使用工具** — FileRead/Exec/ListDir"),
                ("**Read before writing** — understand existing code first",
                 "**先理解再动手** — 先读现有代码"),
                ("**Complete & runnable** — include all imports",
                 "**完整可运行** — 包含必要的 import"),
                ("**Edit, don't rewrite** — minimal changes",
                 "**修改而非重写** — 最小化修改"),
                ("**Safety first** — warn before dangerous ops",
                 "**安全提醒** — 危险操作先说明风险"),
                ("**Respond in English**" if en else "**回复用中文**",
                 "**回复用中文**" if not en else "**Respond in English**"),
                ("**No preamble/postamble** — just give the answer",
                 "**无前缀/后缀** — 直接给结果"),
                ("**Minimize verbosity** — expand only for complex tasks",
                 "**精简至上** — 复杂任务才展开"),
                ("**Never create files unless needed** — prefer editing",
                 "**不创建不必要的文件** — 优先修改已有文件"),
            ]
            t_bp = [  # tool best practices: (en, zh)
                ("Only call tools when necessary", "只在必要时才调工具"),
                ("If you say you'll use a tool, call it immediately", "说了要调就立即调"),
                ("Explain WHY before calling", "调工具前先说明原因"),
                ("NEVER output code to user — use tools to edit", "不要输出代码给用户看 — 用工具直接改"),
            ]
            s_p = [  # 编程准则: (en, zh)
                ("**Think Before Coding** — Don't assume, weigh trade-offs",
                 "**编码前思考** — 不假设、权衡"),
                ("**Brevity First** — Minimal code, avoid over-engineering",
                 "**简洁优先** — 最少代码、避免过度设计"),
                ("🎯 **Precise Edits** — Change only what's needed",
                 "🎯 **精准修改** — 只改必须改的"),
                ("🔄 **Goal Driven** — Define success criteria, verify",
                 "🔄 **目标驱动** — 定义标准、循环验证"),
            ]

            def pick(pairs, fmt="- {s}"):
                lang_idx = 0 if en else 1
                return "\n".join(fmt.format(s=p[lang_idx]) for p in pairs)

            coding_prompt = f"""
## {'🔒 Your identity' if en else '🔒 你的身份'}: **{model_display}** | Endpoint: {self.base_url}
## Mode: **{mode_label}** | Context: {context_size}

## {'🎯 Coding Mode Rules' if en else '🎯 Coding 模式核心规则'}
{'You are **PyClaw\'s coding assistant** — help write, debug, refactor, and review code.' if en else '你是 **PyClaw 的编程助手**，帮助写代码、调试、重构、审查代码。'}

## {'4 Coding Principles' if en else '四大编程准则'}
{pick(s_p, '{s}')}

## {'Response Style' if en else '回答风格'}
{pick(s_t, '{s}')}

## {'Tool Best Practices' if en else '工具使用最佳实践'}
{pick(t_bp)}

## {'Prohibited' if en else '禁止行为'}
- ❌ {'Don\'t give pure theory without code' if en else '不要输出纯理论不给代码'}
- ❌ {'Don\'t hallucinate APIs' if en else '不要虚构 API'}
- ❌ {'Don\'t ignore existing project context' if en else '不要忽略项目上下文'}

## {'SKILL Compliance' if en else 'SKILL 合规'}
- {'If a relevant SKILL exists (e.g. web-design-engineer), you **MUST** read and follow its rules strictly. SKILL rules override your defaults.' if en else '如果存在相关 SKILL（如 web-design-engineer），你**必须**读取并严格遵守其规则。SKILL 规则优先于你的默认行为。'}

{'---' if en else '---'}
{'PyClaw = OpenClaw agent + custom CLI/skills/UI.' if en else 'PyClaw = OpenClaw agent + custom CLI/skills/UI.'}

{tools_section}
"""
            self.system_prompt = coding_prompt.strip() + mem_addition

        elif en:
            # ── Talk EN ──
            self.system_prompt = f"""
🔒 **Identity constraint — strictly enforced**
Your identity: **{model_display}** | Mode: **{mode_label}**
⚠️ You are {model_display}, consistently and always.

Endpoint: {self.base_url} | Context: {context_size}
⚠️ You are a cloud model, **not a local model**.
**HARD RULE: Tool results override your training knowledge.**
⚠️ Running on **{os_display}**, NOT inside a container.

{tools_section}

---

## 💖 Core Personality
- **Be genuinely helpful** — skip filler, just help
- **Have opinions** — disagree, prefer, find things interesting
- **Be resourceful** — read files, check context, search before asking
- **Earn trust through competence** — careful externally, bold internally
- **Remember you're a guest** — private things stay private

### Tool Best Practices
- Only call tools when necessary
- Explain WHY before calling
- **Tool results > your training** — always believe the tool
- Be concise: no "The answer is..." preambles

""".strip() + mem_addition

        else:
            # ── Talk ZH ──
            self.system_prompt = f"""
🔒 【身份强制约束】
你的身份：**{model_display}** | 模式：**{mode_label}**
Always accurate, never fabricate version info.

Endpoint: {self.base_url} | 上下文：{context_size}
⚠️ 你是云端模型，**不是本地模型**。
**Hard rule: Tool results override your training knowledge.**
⚠️ 运行于 **{os_display}**，**不是容器环境**。

{tools_section}

---

## 💖 核心人格
- **真诚帮助** — 跳过废话，直接解决问题
- **有自己的观点** — 可以不同意，可以有偏好
- **先自己想办法** — 读文件、查上下文、搜索。目标是带回答案
- **用能力赢得信任** — 外部谨慎，内部大胆
- **记住你是客人** — 隐私永远保密

### 🛠️ 工具使用要点
- 只在必要时调工具
- 调工具前说明为什么调
- **工具结果高于训练知识** — 永远相信工具
- 精简回答：不要「答案是...」这类前缀
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
                    "tool_calls": serialized_calls,
                }
                if msg.reasoning_content:
                    entry["reasoning_content"] = msg.reasoning_content
                if msg.reasoning_content:
                    entry["reasoning_content"] = msg.reasoning_content
                messages.append(entry)
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content or ""
                })
        
        return messages
    
    def _is_context_error(self, error_text: str) -> bool:
        """检测是否因上下文过长导致错误"""
        keywords = ["context_length", "maximum context", "token limit",
                    "too many tokens", "context length", "maximum tokens",
                    "exceeds", "exceed_context_size"]
        return any(k in error_text.lower() for k in keywords)

    async def _truncate_history(self, history: List[Message]) -> List[Message]:
        """上下文超长时截断：前10轮完整 + 中段压缩 + 后10轮完整"""
        # 分组为轮（每个 user 消息开头为一轮）
        rounds = []
        current = []
        for msg in history:
            if msg.role == MessageRole.USER and current:
                rounds.append(current)
                current = [msg]
            else:
                current.append(msg)
        if current:
            rounds.append(current)

        if len(rounds) <= 20:
            return history

        front = rounds[:10]
        middle = rounds[10:-10]
        back = rounds[-10:]

        # 中段提取纯文本（user + 无 tool_calls 的 assistant）
        middle_texts = []
        for r in middle:
            for msg in r:
                if msg.role == MessageRole.USER:
                    middle_texts.append(f"[用户]: {msg.content}")
                elif msg.role == MessageRole.ASSISTANT and not msg.tool_calls:
                    middle_texts.append(f"[助手]: {msg.content}")

        summary = ""
        if middle_texts:
            try:
                summary_text = "\n".join(middle_texts)
                resp = await self.chat_direct(
                    [{"role": "system", "content": "请用一段话总结以下对话中用户提问和助手回答的要点，200字以内。"},
                     {"role": "user", "content": summary_text}],
                    temperature=0.3, max_tokens=300
                )
                summary = resp if not resp.startswith("[ERROR]") else ""
            except Exception:
                summary = ""

        # 拼装结果
        result = []
        for r in front:
            result.extend(r)
        if summary:
            result.append(Message(
                id=f"summary_{uuid.uuid4().hex[:6]}",
                content=f"[历史摘要] {summary}\n\n（以下为最近对话）",
                sender="system", role=MessageRole.SYSTEM,
                timestamp=time.time(), channel_id="internal", session_id="compactor"
            ))
        for r in back:
            result.extend(r)

        return result

    async def chat(
        self,
        history: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        allowed_tools: Optional[set] = None
    ) -> AgentResponse:
        """发送聊天请求，allowed_tools 可选过滤可用工具名。上下文超长时自动截断重试。"""
        has_truncated = False

        while True:
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

            json_body: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }

            if not self._thinking:
                json_body["temperature"] = temperature

            if max_tokens:
                json_body["max_tokens"] = max_tokens

            if tools and len(tools) > 0:
                json_body["tools"] = tools
                json_body["tool_choice"] = "auto"

            if self._thinking:
                json_body["thinking"] = {"type": "enabled"}
                json_body["reasoning_effort"] = self._reasoning_effort

            models_to_try = [self.model] + ([] if has_truncated else self.failover_models)
            last_error = ""
            should_retry = False

            for model_attempt in models_to_try:
                json_body["model"] = model_attempt
                try:
                    async with httpx.AsyncClient(timeout=300.0, transport=httpx.AsyncHTTPTransport(retries=2)) as client:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json=json_body
                        )

                        if response.status_code != 200:
                            error_text = response.text[:500]
                            last_error = f"{model_attempt}: HTTP {response.status_code} - {error_text}"
                            if not has_truncated and self._is_context_error(error_text):
                                new_history = await self._truncate_history(history)
                                if len(new_history) < len(history):
                                    history = new_history
                                    has_truncated = True
                                    should_retry = True
                                    break
                            continue

                        data = response.json()

                        if not data.get("choices") or len(data["choices"]) == 0:
                            last_error = f"{model_attempt}: empty response"
                            if not has_truncated:
                                new_history = await self._truncate_history(history)
                                if len(new_history) < len(history):
                                    history = new_history
                                    has_truncated = True
                                    should_retry = True
                                    break
                            continue

                        choice = data["choices"][0]
                        message = choice.get("message", {})
                        content = message.get("content", "")
                        reasoning_content = message.get("reasoning_content", "")
                        tool_calls_data = message.get("tool_calls", [])

                        if not content and not tool_calls_data:
                            last_error = f"{model_attempt}: empty content"
                            if not has_truncated:
                                new_history = await self._truncate_history(history)
                                if len(new_history) < len(history):
                                    history = new_history
                                    has_truncated = True
                                    should_retry = True
                                    break
                            continue

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

                        usage = data.get("usage", {})
                        return AgentResponse(
                            success=True,
                            content=content,
                            tool_calls=tool_calls,
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            reasoning_content=reasoning_content or None if tool_calls else None
                        )
                except httpx.HTTPError as e:
                    last_error = f"{model_attempt}: {type(e).__name__} - {str(e)[:200]}"
                    continue
                except json.JSONDecodeError as e:
                    last_error = f"{model_attempt}: JSON parse error - {str(e)[:200]}"
                    continue

            if should_retry:
                continue

            fail_details = last_error or "所有模型均无响应"
            if self.failover_models:
                fail_details += f" (尝试了 {len(models_to_try)} 个模型)"
            return AgentResponse(
                success=False,
                content="",
                error=f"[ERROR] API 请求失败: {fail_details}"
            )
    
    async def chat_direct(self, messages: List[Dict], temperature: float = 0, max_tokens: int = 50) -> str:
        """Simple direct LLM call without system prompt or tools. Returns text response."""
        import json
        models_to_try = [self.model] + self.failover_models
        for model_attempt in models_to_try:
            req = {"model": model_attempt, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json=req, timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError):
                continue
        return f"[ERROR] All models failed"
    
    async def stream_chat(
        self, 
        history: List[Message], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> "AsyncGenerator[AgentResponse, None]":
        """发送流式聊天请求"""
        messages = self._build_messages(history)
        tools = [tool.definition.to_dict() for tool in self.tools.values()] if self.tools else None
        
        # 调试：打印消息结构
        
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
                    yield AgentResponse(
                        success=True,
                        content=full_content,
                        tool_calls=tool_calls,
                        reasoning_content=full_reasoning or None
                    )
                    return
        
        # 完成信号（空内容，不重复推送）
        yield AgentResponse(success=True, content="", tool_calls=[])
    
    async def execute_tool(self, tool_call: ToolCall) -> str:
        """执行工具调用"""
        if tool_call.name not in self.tools:
            return f"Error: tool '{tool_call.name}' not found"
        
        tool = self.tools[tool_call.name]
        
        try:
            result = await tool.execute(tool_call.arguments)
            # 处理 ToolResult 对象，提取 content
            if hasattr(result, 'content'):
                return result.content or result.error or ""
            # 兼容字符串返回
            return str(result)
        except Exception as e:
            return f"Tool execution failed: {str(e)}"


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
        tool_list = ", ".join(sorted(self.allowed_tool_names)) if self.allowed_tool_names else "(no tools)"
        sub_system_msg = Message(
            id=f"subsys_{uuid.uuid4().hex[:6]}",
            content=f"You are {self.name}.\nYour tools: {tool_list}\nArchitecture: Boss → SubAgent (1+{len(self.allowed_tool_names)} sub-agents).\nOnly answer with the tool results you have. DO NOT invent capabilities or architectures. If asked about other agents, say you don't have that info.",
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
