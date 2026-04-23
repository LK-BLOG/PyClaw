# 🔌 PyClaw Skill 插件开发指南

本文档详细介绍如何为 PyClaw 开发 Skill 插件。

---

## 📋 目录

- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [工具定义](#工具定义)
- [Skill 元数据](#skill-元数据)
- [生命周期](#生命周期)
- [最佳实践](#最佳实践)
- [发布分享](#发布分享)

---

## 快速开始

### 步骤 1：创建 Skill 目录

在 `skills/` 下创建你的 Skill 目录：

```bash
mkdir -p skills/hello_skill
```

### 步骤 2：创建 `__init__.py`

```python
# skills/hello_skill/__init__.py
from dataclasses import dataclass
from typing import Dict, Any

from pyclaw.skill import SkillMetadata
from pyclaw.types import ToolDefinition, ToolResult

# 必须定义！告诉 PyClaw 用哪个类
SKILL_CLASS = "HelloSkill"


@dataclass
class HelloTool:
    """一个简单的问候工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="hello_world",
            description="向用户打招呼，支持指定姓名和语言",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "用户姓名",
                        "default": "朋友"
                    },
                    "language": {
                        "type": "string",
                        "description": "语言：zh 中文 / en 英文",
                        "default": "zh"
                    }
                }
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        name = params.get("name", "朋友")
        language = params.get("language", "zh")
        
        if language == "en":
            greeting = f"Hello, {name}!"
        else:
            greeting = f"你好，{name}！"
        
        return ToolResult(
            success=True,
            content=f"{greeting}\n\n来自 Hello Skill!"
        )


class HelloSkill:
    """我的第一个 PyClaw Skill"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Hello Skill",
            description="一个简单的问候 Skill 示例",
            author="你的名字",
            version="1.0.0",
            tags=["hello", "示例", "教程"],
            website="https://github.com/yourname/hello-skill"
        )
    
    def get_tools(self):
        return [HelloTool()]
    
    async def initialize(self) -> bool:
        print("[Hello Skill] 初始化完成！")
        return True
    
    async def cleanup(self) -> None:
        print("[Hello Skill] 已卸载")
```

### 步骤 3：重启 PyClaw

重启服务，你会看到：

```
[OK] 已加载 Skill: Hello Skill v1.0.0 by 你的名字
```

### 步骤 4：测试

在聊天界面输入：
```
用 Hello Skill 向小明打招呼，用中文
```

AI 会自动调用 `hello_world` 工具！

---

## 核心概念

### 什么是 Skill？

Skill 是 PyClaw 的功能扩展单元，一个 Skill 可以提供 **1 个或多个工具**。

### Skill 的组成

每个 Skill 包含：

| 部分 | 作用 | 必填 |
|------|------|------|
| `SKILL_CLASS` 常量 | 指定 Skill 主类名 | ✅ |
| Skill 主类 | Skill 的入口点 | ✅ |
| `metadata` 属性 | Skill 元数据（名称、作者、版本等） | ✅ |
| `get_tools()` 方法 | 返回所有工具 | ✅ |
| `initialize()` 方法 | 初始化逻辑 | ❌ |
| `cleanup()` 方法 | 清理逻辑 | ❌ |
| 工具类 | 实现具体功能 | ✅ |

---

## 工具定义

### ToolDefinition 详解

```python
ToolDefinition(
    name="tool_name",           # 工具名称（唯一）
    description="工具描述",      # 非常重要！AI 靠这个决定何时调用
    parameters={...}            # 参数定义
)
```

### 参数定义

使用 [JSON Schema](https://json-schema.org/) 格式定义参数：

```python
parameters={
    "type": "object",
    "properties": {
        "param1": {
            "type": "string",           # 类型：string, integer, boolean, number, array, object
            "description": "参数描述",   # 必填！AI 靠这个理解参数含义
            "default": "默认值"          # 可选
        },
        "param2": {
            "type": "integer",
            "description": "数字参数",
            "enum": [1, 2, 3]           # 可选：限制取值范围
        }
    },
    "required": ["param1"]           # 必填参数列表
}
```

### 支持的参数类型

| 类型 | 示例 |
|------|------|
| `string` | 字符串、文本 |
| `integer` | 整数 |
| `number` | 数字（整数或浮点数） |
| `boolean` | true / false |
| `array` | 数组（嵌套 `items` 定义） |
| `object` | 对象（嵌套 `properties`） |

### ToolResult 返回值

```python
# 成功返回
return ToolResult(
    success=True,
    content="执行结果内容"
)

# 失败返回
return ToolResult(
    success=False,
    content="",
    error="错误描述信息"
)
```

---

## Skill 元数据

### SkillMetadata 完整字段

```python
SkillMetadata(
    name="Skill 名称",
    description="详细描述，告诉用户这个 Skill 能做什么",
    author="作者名",
    version="1.0.0",
    tags=["标签1", "标签2"],  # 用于分类和搜索
    website="https://..."      # 项目主页或仓库地址
)
```

### 版本号规范

建议使用 [语义化版本](https://semver.org/lang/zh-CN/)：

```
主版本号.次版本号.修订号
例如：1.2.3
```

- **主版本号**：不兼容的 API 变更
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

---

## 生命周期

### 启动阶段

1. PyClaw 启动时扫描 `skills/` 目录
2. 找到每个 Skill 的 `SKILL_CLASS`
3. 实例化 Skill 对象
4. 调用 `skill.initialize()`
5. 调用 `skill.get_tools()` 注册所有工具
6. 输出 `[OK] 已加载 Skill: xxx`

### 运行阶段

- AI 根据用户输入决定调用哪个工具
- 调用工具的 `execute()` 方法
- 返回结果给 AI 处理

### 卸载阶段

1. 调用 `skill.cleanup()`
2. 卸载所有工具
3. 输出 `[xxx Skill] 已卸载`

---

## 最佳实践

### ✅ 1. 工具描述要详细

```python
# ❌ 不好
description="发送消息"

# ✅ 好
description="发送消息到指定频道，支持文本、图片、文件。\
成功返回消息 ID，失败返回错误信息。"
```

**描述越详细，AI 越知道什么时候调用这个工具！**

### ✅ 2. 参数描述不能省

```python
# ❌ 不好
"user_id": {"type": "string"}

# ✅ 好
"user_id": {
    "type": "string",
    "description": "目标用户的 ID，格式为 U开头 + 数字，例如 U123456"
}
```

### ✅ 3. 检查依赖

在 `initialize()` 中检查依赖库，缺失时提示用户安装：

```python
async def initialize(self) -> bool:
    try:
        import requests
        return True
    except ImportError:
        print("[MySkill] ⚠️  缺少依赖：pip install requests")
        # 也可以选择自动安装
        # subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
        return False
```

### ✅ 4. 处理异常

```python
async def execute(self, params: Dict[str, Any]) -> ToolResult:
    try:
        # 你的逻辑
        result = do_something()
        return ToolResult(success=True, content=result)
    except Exception as e:
        return ToolResult(
            success=False,
            content="",
            error=f"操作失败: {str(e)}"
        )
```

### ✅ 5. Skill 之间相互独立

- 不要依赖其他 Skill 的内部实现
- 如果需要共享功能，考虑做成单独的库

### ✅ 6. 工具命名规范

```
skillname_action
例如：
weather_get_current
bilibili_post_dynamic
system_list_processes
```

---

## 高级技巧

### 多个工具

一个 Skill 可以提供多个工具：

```python
class WeatherSkill:
    def get_tools(self):
        return [
            CurrentWeatherTool(),
            ForecastTool(),
            WeatherAlertTool(),
        ]
```

### Skill 内共享状态

```python
class MySkill:
    def __init__(self):
        self.cache = {}  # Skill 内的共享状态
    
    async def initialize(self) -> bool:
        self.cache["last_update"] = time.time()
        return True
```

### 配置文件

Skill 可以有自己的配置文件：

```python
class MySkill:
    async def initialize(self) -> bool:
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                self.config = json.load(f)
        return True
```

---

## 发布分享

### 发布到 GitHub

1. 创建公开仓库
2. 你的 Skill 就是一个 Python package 目录
3. 在 README 中写清楚：
   - 功能介绍
   - 安装方法
   - 依赖说明
   - 配置步骤

### 安装他人的 Skill

```python
# 方法一：从 Git 安装
install_skill(source="https://github.com/user/awesome-skill.git")

# 方法二：从本地目录安装
install_skill(source="/path/to/downloaded/skill")
```

---

## 📝 开发清单

发布前检查：

- [ ] `SKILL_CLASS` 常量已定义
- [ ] 所有工具都有详细的 `description`
- [ ] 所有参数都有清晰的 `description`
- [ ] `initialize()` 方法处理了异常
- [ ] 依赖库在 README 中说明
- [ ] 有 `version` 版本号
- [ ] `metadata` 信息完整
- [ ] 有详细的工具返回值说明

---

## 🎯 灵感

你可以开发的 Skill 类型：

- 🤖 各种平台机器人：微信、钉钉、飞书...
- 📁 文件处理：PDF、图片、视频处理...
- 📊 数据查询：数据库、API 调用...
- 🔔 通知推送：ServerChan、Bark、邮件...
- 🎮 娱乐功能：抽奖、笑话、抽签...
- 🛠️ 开发工具：Git、Docker、SSH...
- 📦 办公自动化：Excel、PPT、文档生成...

**发挥你的想象力！** 🚀🦞
