# 🦞 PyClaw

从零构建的 Python AI 助手框架，参考 OpenClaw 设计理念。

> **全平台支持**：Windows ✅ Linux ✅ macOS ✅  
> **U盘便携**：整个项目才几 MB，拷到 U 盘插哪都能用 ✅

---

## ✨ 特性

### 💪 超强兼容性
- 📁 仅 **320KB**，比一张照片还小
- 💻 10 年前的老电脑都能流畅运行
- 🧮 后台仅占用 ~50MB 内存
- ⚡ 1 秒内启动完成
- 🐍 兼容 Python 3.8 - 3.12
- 🖥️ 支持 Windows 7/8/10/11、Linux、macOS

### 🤖 核心功能
- 🧠 **DeepSeek 大模型** - 支持工具调用的 AI 助手
- 💬 **美观的 Web 界面** - GitHub 深色主题，流畅的聊天体验
- 📂 **多会话管理** - 支持多个独立对话，一键切换
- 🧩 **Skill 插件系统** - 功能无限扩展，预装 5 个实用插件
- 🧠 **长期记忆系统** - 记住用户偏好，永久保存
- 🔐 **安全设计** - 密钥从环境变量读取，不硬编码

### 🔧 内置工具（免费使用）
| 工具 | 功能 |
|------|------|
| 📁 **ListDir** | 浏览目录内容 |
| 📄 **FileRead** | 读取文件内容 |
| 💻 **Exec** | 执行系统命令 |
| ⏰ **Time** | 查询当前时间 |

### 📦 预装 Skill 插件（开箱即用）
| Skill | 功能 | 工具数量 |
|-------|------|---------|
| 🌤️ **Weather** | 查询全球城市天气 | 1 |
| 📺 **Bilibili** | 发布 B站 动态 | 1 |
| 🖥️ **System Info** | 系统信息、进程管理 | 3 |
| 📂 **Desktop Path** | Linux 中文桌面路径处理 | 2 |
| 🧠 **Memory Manager** | 长期记忆管理 | 4 |
| 🔧 **Skill Manager** | 插件管理（列出/安装/卸载） | 3 |

**总计：18 个工具！**

---

## 🚀 快速开始

### 方式一：一键启动（推荐）

```bash
# Linux/macOS
./启动.sh

# Windows
双击 启动.bat
```

**第一次启动会自动：**
1. 检测系统 Python 版本
2. 安装所有依赖
3. 启动 Web 服务

然后打开浏览器访问 **http://localhost:2469** 即可使用！

---

### 方式二：手动启动

```bash
# 1. 复制配置文件
cp .env.example .env

# 2. 编辑 .env，填入你的 DeepSeek API Key
PYCLAW_API_KEY=sk-xxxxxxxxxxxx

# 3. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 启动服务
python run.py
```

---

## 📋 配置说明

### 支持的模型

PyClaw 兼容所有 OpenAI 格式的 API：

| 服务商 | Base URL 示例 |
|--------|--------------|
| ✅ **DeepSeek** | `https://api.deepseek.com/v1` |
| ✅ **火山引擎** | `https://ark.cn-beijing.volces.com/api/v3` |
| ✅ **智谱 AI** | `https://open.bigmodel.cn/api/paas/v4` |
| ✅ **通义千问** | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| ✅ **OpenAI** | `https://api.openai.com/v1` |
| ✅ **任何兼容 API** | ... |

在 `.env` 文件中配置即可：

```env
PYCLAW_API_KEY=你的API密钥
PYCLAW_BASE_URL=https://api.deepseek.com/v1
PYCLAW_MODEL=deepseek-chat
```

---

## 🧠 长期记忆系统

PyClaw 拥有永久记忆功能，AI 可以记住你的偏好！

### 如何使用

**对 AI 说**：
```
记住我叫小戡，喜欢简洁回答
记住我常用的桌面路径是中文
记住我的 B站 ID 是 xxx
```

AI 会自动把这些信息保存到长期记忆中，**所有未来的会话都会记得**！

### 记忆管理工具
- `add_global_memory` - 添加全局记忆
- `list_global_memories` - 列出所有记忆
- `search_memory` - 搜索记忆
- `delete_memory` - 删除记忆

**所有记忆保存在 `pyclaw_memory.db` 文件中，跟 U 盘一起带走！**

---

## 🔌 Skill 插件开发指南

### 📦 Skill 目录结构

所有 Skill 都放在 `skills/` 目录下，每个 Skill 是一个子目录：

```
skills/
└── your_skill/
    └── __init__.py      # Skill 代码
```

### 🎯 Skill 模板

```python
from dataclasses import dataclass
from typing import Dict, Any

from pyclaw.skill import SkillMetadata
from pyclaw.types import ToolDefinition, ToolResult

# 必须定义 SKILL_CLASS，告诉加载器用哪个类
SKILL_CLASS = "YourSkill"

# ────────────────────────────────────────────
# 1. 定义你的工具
# ────────────────────────────────────────────
@dataclass
class YourTool:
    """你的工具描述"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="your_tool_name",
            description="工具描述，AI 会根据这个决定什么时候调用",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "参数描述"
                    }
                },
                "required": ["param1"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        # 你的工具逻辑在这里
        result = do_something(params["param1"])
        return ToolResult(success=True, content=result)

# ────────────────────────────────────────────
# 2. 定义 Skill 主类
# ────────────────────────────────────────────
class YourSkill:
    """你的 Skill 描述"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="你的 Skill 名称",
            description="Skill 的详细描述",
            author="你的名字",
            version="1.0.0",
            tags=["标签1", "标签2"],
            website="https://github.com/..."
        )
    
    def get_tools(self):
        """返回这个 Skill 提供的所有工具"""
        return [YourTool()]
    
    async def initialize(self) -> bool:
        """初始化，启动时调用"""
        print("[Your Skill] 初始化完成")
        return True
    
    async def cleanup(self) -> None:
        """卸载时清理资源"""
        print("[Your Skill] 已卸载")
```

### 💡 开发技巧

1. **工具名称要唯一**，建议加上 Skill 前缀
2. **`definition.description` 很重要**，AI 靠它决定什么时候调用
3. **参数要写清楚描述**，AI 才能正确传参
4. `execute` 方法必须是 `async`
5. 可以在 `initialize()` 里检查依赖库

### 📥 安装 Skill

```python
# 方式一：从本地目录安装
install_skill(source="/path/to/your/skill")

# 方式二：从 Git 仓库安装
install_skill(source="https://github.com/user/your-skill-repo.git")
```

---

## 🎯 技术栈

| 组件 | 选型 |
|------|------|
| **Web 框架** | FastAPI + Uvicorn |
| **前端** | 原生 HTML + CSS + JavaScript |
| **WebSocket** | 实时双向通信 |
| **存储** | SQLite（轻量，单文件） |
| **LLM SDK** | 纯 httpx 实现，零依赖 |

---

## 📁 项目结构

```
pyclaw/
├── run.py              # 智能启动脚本
├── webapp.py           # Web 界面主程序
├── gateway.py          # 消息路由网关
├── agent.py            # Agent 运行时
├── session.py          # 会话管理
├── tools.py            # 内置工具
├── types.py            # 类型定义
├── channels.py         # 通道定义
├── skill.py            # Skill 插件系统
├── memory.py           # 长期记忆系统
├── skills/             # 插件目录
│   ├── weather/        # 天气插件
│   ├── bilibili/       # B站插件
│   ├── system_info/    # 系统信息插件
│   └── desktop_path/   # 桌面路径插件
├── .env.example        # 配置模板
├── .gitignore          # Git 忽略规则
├── requirements.txt    # 依赖列表
├── 启动.bat            # Windows 一键启动
├── 启动.sh             # Linux/macOS 一键启动
├── 清理.bat            # Windows 清理工具
├── 清理.sh             # Linux/macOS 清理工具
└── README.md
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

开发你的 Skill 并分享给社区！

---

## 📄 License

MIT License

---

## 🙏 致谢

设计理念参考自 [OpenClaw](https://github.com/openclaw)

---

**Made with 🦞 ❤️ by 骆戡 & OpenClaw Team**
