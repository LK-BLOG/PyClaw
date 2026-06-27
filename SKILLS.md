# PyClaw Skill 开发手册 / PyClaw Skill Development Guide

---

## 📖 目录 / Table of Contents

- [中文版本](#-中文版本)
- [English Version](#-english-version)

---

## 🇨🇳 中文版本

### 1. 什么是 Skill？

Skill 是 PyClaw 的扩展插件系统，允许你轻松添加新功能和工具。每个 Skill 都是一个独立的 Python 模块，可以：
- 注册新的工具函数供 AI 调用
- 访问 Gateway、Agent、会话管理等核心 API
- 与其他 Skill 交互

### 2. Skill 基本结构

每个 Skill 存放在 `skills/` 目录下的独立文件夹中：

```
skills/
├── weather/               # Skill 目录
│   ├── __init__.py        # 主入口文件（必须）
│   ├── requirements.txt   # 依赖包（可选）
│   └── config.json        # 配置文件（可选）
└── bilibili/
    └── __init__.py
```

### 3. 创建你的第一个 Skill

#### 3.1 基础模板

```python
from typing import List, Dict, Any
from pyclaw.gateway import Gateway

# Skill 元数据
SKILL_METADATA = {
    "name": "HelloWorld",
    "version": "1.0.0",
    "description": "我的第一个 PyClaw Skill",
    "author": "你的名字",
    "tags": ["示例", "入门"],
}

class HelloWorldSkill:
    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        self.logger = gateway.logger
    
    async def initialize(self):
        """Skill 初始化时调用"""
        self.logger.info(f"[{SKILL_METADATA['name']}] 初始化完成!")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """返回 Skill 提供的工具列表"""
        return [
            {
                "name": "say_hello",
                "description": "向用户打招呼",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "用户名字"
                        }
                    },
                    "required": ["name"]
                },
                "execute": self.say_hello
            }
        ]
    
    def say_hello(self, name: str) -> str:
        """工具实现函数"""
        return f"你好，{name}！欢迎使用 PyClaw Skill 系统 🦞"

# 导出 Skill 类（必须）
SKILL_CLASS = HelloWorldSkill
```

#### 3.2 必须的导出

每个 Skill 的 `__init__.py` 必须导出：
- `SKILL_METADATA`: Skill 元数据字典
- `SKILL_CLASS`: Skill 类本身

### 4. Skill 生命周期

```
Skill 发现 → 实例化 → initialize() → 注册工具 → 运行中 → shutdown()
```

| 阶段 | 说明 |
|------|------|
| 发现 | Gateway 启动时扫描 `skills/` 目录 |
| 实例化 | 调用构造函数，传入 gateway 实例 |
| 初始化 | 调用 `initialize()` 异步方法 |
| 注册工具 | 调用 `get_tools()` 注册所有工具 |
| 运行中 | 工具可被 AI 调用 |
| 关闭 | Gateway 关闭时调用 `shutdown()`（如有） |

### 5. 工具定义详解

工具定义遵循 **OpenAI Function Calling** 格式：

```python
{
    "name": "工具名称",           # 必须：英文，下划线分隔
    "description": "工具描述",     # 必须：清晰说明用途
    "parameters": {               # 必须：参数定义
        "type": "object",
        "properties": {           # 参数列表
            "param1": {
                "type": "string",
                "description": "参数1说明"
            }
        },
        "required": ["param1"]    # 必填参数列表
    },
    "execute": self.my_function   # 必须：执行函数
}
```

### 6. 访问核心 API

在 Skill 中你可以通过 `self.gateway` 访问所有核心功能：

```python
# 获取当前会话
session = self.gateway.session_manager.get_session(session_id)

# 发送消息给用户
await session.send_message("Hello from Skill!")

# 访问 Agent
response = self.gateway.agent.chat("你好", session_id)

# 记录日志
self.gateway.logger.info("日志信息")

# 访问其他 Skill
other_skill = self.gateway.skill_manager.get_skill("OtherSkill")
```

### 7. Skill 间通信

Skill 之间可以互相调用：

```python
# 在 Skill A 中
class SkillA:
    def get_public_methods(self):
        """暴露给其他 Skill 调用的方法"""
        return {
            "get_data": self.get_data
        }
    
    def get_data(self) -> dict:
        return {"key": "value"}

# 在 Skill B 中
skill_a = self.gateway.skill_manager.get_skill("SkillA")
data = skill_a.get_data()  # 调用公开方法
```

### 8. 最佳实践

#### ✅ 推荐做法
1. **异步优先**：IO 操作使用 `async def`
2. **错误处理**：使用 try/except 捕获异常
3. **日志记录**：使用 `self.logger` 记录关键信息
4. **类型注解**：给函数添加类型注解
5. **文档字符串**：每个公共方法添加 docstring
6. **配置分离**：配置文件放在 `config.json` 中

#### ❌ 避免做法
1. 不要阻塞事件循环
2. 不要直接修改其他 Skill 的内部状态
3. 不要硬编码敏感信息
4. 不要抛出未捕获的异常

### 9. 完整示例 - 天气查询 Skill

```python
import httpx
from typing import List, Dict, Any
from pyclaw.gateway import Gateway

SKILL_METADATA = {
    "name": "Weather",
    "version": "1.0.0",
    "description": "查询全球天气信息",
    "author": "PyClaw Team",
    "tags": ["天气", "实用工具"],
}

class WeatherSkill:
    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        self.logger = gateway.logger
        self.base_url = "https://wttr.in"
    
    async def initialize(self):
        self.logger.info("[Weather] Skill 已加载")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_weather",
                "description": "查询指定城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，例如：Beijing、London"
                        },
                        "format": {
                            "type": "string",
                            "description": "输出格式：text(文本)、json(结构化)",
                            "default": "text"
                        }
                    },
                    "required": ["city"]
                },
                "execute": self.get_weather
            }
        ]
    
    async def get_weather(self, city: str, format: str = "text") -> str:
        """查询天气"""
        try:
            async with httpx.AsyncClient() as client:
                if format == "json":
                    response = await client.get(f"{self.base_url}/{city}?format=j1")
                    return f"天气数据（JSON）：{response.json()}"
                else:
                    response = await client.get(f"{self.base_url}/{city}?format=3")
                    return response.text
        except Exception as e:
            self.logger.error(f"查询天气失败: {e}")
            return f"查询天气失败：{str(e)}"

SKILL_CLASS = WeatherSkill
```

### 10. 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Skill 不加载 | 目录名不含 `__init__.py` | 检查文件结构 |
| 工具不显示 | `get_tools()` 返回空列表 | 检查工具定义格式 |
| 初始化失败 | `initialize()` 抛出异常 | 查看日志 |
| 调用无响应 | 执行函数是同步但耗时太长 | 改成 async |

---

## 🇬🇧 English Version

### 1. What is a Skill?

A Skill is PyClaw's extension plugin system that allows you to easily add new features and tools. Each Skill is an independent Python module that can:
- Register new tool functions for the AI to call
- Access core APIs like Gateway, Agent, and session management
- Interact with other Skills

### 2. Basic Skill Structure

Each Skill is stored in a separate folder under the `skills/` directory:

```
skills/
├── weather/               # Skill directory
│   ├── __init__.py        # Main entry file (required)
│   ├── requirements.txt   # Dependencies (optional)
│   └── config.json        # Configuration file (optional)
└── bilibili/
    └── __init__.py
```

### 3. Create Your First Skill

#### 3.1 Basic Template

```python
from typing import List, Dict, Any
from pyclaw.gateway import Gateway

# Skill metadata
SKILL_METADATA = {
    "name": "HelloWorld",
    "version": "1.0.0",
    "description": "My first PyClaw Skill",
    "author": "Your Name",
    "tags": ["Example", "Getting Started"],
}

class HelloWorldSkill:
    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        self.logger = gateway.logger
    
    async def initialize(self):
        """Called when Skill initializes"""
        self.logger.info(f"[{SKILL_METADATA['name']}] Initialized!")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of tools provided by this Skill"""
        return [
            {
                "name": "say_hello",
                "description": "Greet the user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "User name"
                        }
                    },
                    "required": ["name"]
                },
                "execute": self.say_hello
            }
        ]
    
    def say_hello(self, name: str) -> str:
        """Tool implementation function"""
        return f"Hello, {name}! Welcome to PyClaw Skill system 🦞"

# Export Skill class (required)
SKILL_CLASS = HelloWorldSkill
```

#### 3.2 Required Exports

Each Skill's `__init__.py` must export:
- `SKILL_METADATA`: Skill metadata dictionary
- `SKILL_CLASS`: The Skill class itself

### 4. Skill Lifecycle

```
Skill Discovery → Instantiation → initialize() → Register Tools → Running → shutdown()
```

| Stage | Description |
|-------|-------------|
| Discovery | Gateway scans `skills/` directory on startup |
| Instantiation | Constructor called with gateway instance |
| Initialization | `initialize()` async method called |
| Register Tools | `get_tools()` called to register all tools |
| Running | Tools available for AI calls |
| Shutdown | `shutdown()` called when Gateway closes (if available) |

### 5. Tool Definition Explained

Tool definitions follow the **OpenAI Function Calling** format:

```python
{
    "name": "tool_name",          # Required: English, snake_case
    "description": "Tool desc",    # Required: Clear explanation of purpose
    "parameters": {               # Required: Parameter definition
        "type": "object",
        "properties": {           # Parameter list
            "param1": {
                "type": "string",
                "description": "Param 1 description"
            }
        },
        "required": ["param1"]    # Required parameter list
    },
    "execute": self.my_function   # Required: Execution function
}
```

### 6. Accessing Core APIs

In your Skill, you can access all core features via `self.gateway`:

```python
# Get current session
session = self.gateway.session_manager.get_session(session_id)

# Send message to user
await session.send_message("Hello from Skill!")

# Access Agent
response = self.gateway.agent.chat("Hello", session_id)

# Logging
self.gateway.logger.info("Log message")

# Access other Skill
other_skill = self.gateway.skill_manager.get_skill("OtherSkill")
```

### 7. Inter-Skill Communication

Skills can call each other:

```python
# In Skill A
class SkillA:
    def get_public_methods(self):
        """Methods exposed to other Skills"""
        return {
            "get_data": self.get_data
        }
    
    def get_data(self) -> dict:
        return {"key": "value"}

# In Skill B
skill_a = self.gateway.skill_manager.get_skill("SkillA")
data = skill_a.get_data()  # Call public method
```

### 8. Best Practices

#### ✅ Recommended
1. **Async First**: Use `async def` for IO operations
2. **Error Handling**: Use try/except to catch exceptions
3. **Logging**: Use `self.logger` for key information
4. **Type Annotations**: Add type hints to functions
5. **Docstrings**: Add docstrings to every public method
6. **Config Separation**: Store config in `config.json`

#### ❌ Avoid
1. Don't block the event loop
2. Don't directly modify internal state of other Skills
3. Don't hardcode sensitive information
4. Don't throw uncaught exceptions

### 9. Complete Example - Weather Query Skill

```python
import httpx
from typing import List, Dict, Any
from pyclaw.gateway import Gateway

SKILL_METADATA = {
    "name": "Weather",
    "version": "1.0.0",
    "description": "Query global weather information",
    "author": "PyClaw Team",
    "tags": ["Weather", "Utility"],
}

class WeatherSkill:
    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        self.logger = gateway.logger
        self.base_url = "https://wttr.in"
    
    async def initialize(self):
        self.logger.info("[Weather] Skill loaded")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_weather",
                "description": "Query weather for specified city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name, e.g.: Beijing, London"
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format: text, json",
                            "default": "text"
                        }
                    },
                    "required": ["city"]
                },
                "execute": self.get_weather
            }
        ]
    
    async def get_weather(self, city: str, format: str = "text") -> str:
        """Query weather"""
        try:
            async with httpx.AsyncClient() as client:
                if format == "json":
                    response = await client.get(f"{self.base_url}/{city}?format=j1")
                    return f"Weather data (JSON): {response.json()}"
                else:
                    response = await client.get(f"{self.base_url}/{city}?format=3")
                    return response.text
        except Exception as e:
            self.logger.error(f"Weather query failed: {e}")
            return f"Weather query failed: {str(e)}"

SKILL_CLASS = WeatherSkill
```

### 10. Troubleshooting

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Skill not loading | Missing `__init__.py` in directory | Check file structure |
| Tools not showing | `get_tools()` returns empty list | Check tool definition format |
| Initialization failed | `initialize()` throws exception | Check logs |
| No response on call | Execution function is sync but slow | Change to async |

---

## 📚 更多资源 / More Resources

- GitHub: https://github.com/LK-BLOG/PyClaw
- 示例 Skills: `skills/` 目录中的预装 Skill
- API 文档: 查看 `pyclaw/gateway.py`