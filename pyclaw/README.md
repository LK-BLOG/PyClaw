# 🦞 PyClaw

Python 版本的 AI 助手框架，参考 OpenClaw 设计理念，支持工具调用和 Web 界面。

**随身携带，插U盘即用！**

## ✨ 功能特性

- 🎨 **Web 界面** - OpenClaw 风格深色主题
- 💬 **Agent 思考过程可视化** - 能看到 AI 是如何调用工具的
- 🔧 **内置工具** - 文件读取、目录浏览、命令执行、时间查询
- 📦 **U盘便携** - 一键启动脚本，Windows/Linux 双平台支持
- 🌐 **多会话管理** - 每个浏览器标签独立会话

## 🚀 快速开始

### 方法一：一键启动（推荐）

**Windows 用户：**
- 双击 `启动.bat`

**Linux/Mac 用户：**
```bash
./启动.sh
```

然后打开浏览器访问：**http://localhost:2469**

### 方法二：手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 安装依赖
venv/bin/pip install -r requirements.txt

# 3. 启动服务
venv/bin/python3 webapp.py
```

## 📁 项目结构

```
pyclaw/
├── pyclaw/           # 核心代码
│   ├── __init__.py
│   ├── types.py      # 类型定义
│   ├── gateway.py    # 网关核心
│   ├── session.py    # 会话管理
│   ├── agent.py      # Agent 运行时
│   └── tools.py      # 工具实现
├── docs/             # 文档
├── webapp.py         # Web 应用
├── requirements.txt  # 依赖列表
├── 启动.bat         # Windows 一键启动
├── 启动.sh          # Linux/Mac 一键启动
└── README.md         # 说明文档
```

## 💡 使用示例

试试问 AI 这些问题：

1. **"看看当前目录有什么文件"**
   - AI 会调用 `list_directory` 工具列出目录
   - 你能看到完整的思考和调用过程

2. **"读取 README.md 文件"**
   - AI 会调用 `read_file` 工具读取文件内容

3. **"执行 pwd 命令"**
   - AI 会调用 `exec_command` 工具执行系统命令

4. **"现在北京时间几点了"**
   - AI 会调用 `get_current_time` 工具查询时间

## 🎒 U 盘使用说明

1. 把整个 `pyclaw` 文件夹复制到 U 盘
2. 插到任何电脑上，直接双击启动脚本：
   - Windows: `启动.bat`
   - Linux/Mac: `启动.sh`
3. 第一次运行会自动创建虚拟环境并安装依赖
4. 以后再次启动就是秒开！

## ⚙️ 配置说明

编辑 `pyclaw/gateway.py` 修改模型配置：

```python
gateway = Gateway(
    llm_api_key="你的API Key",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="doubao-seed-1-8-251228"
)
```

默认使用火山引擎豆包模型，也可以换成任何兼容 OpenAI 格式的 API。

## 📝 开发计划

- [ ] 支持更多大模型（GPT、Claude、DeepSeek 等）
- [ ] 更多内置工具（搜索、爬虫、代码执行等）
- [ ] 对话历史保存到本地
- [ ] 支持自定义系统提示词
- [ ] 插件系统

## 🤝 关于

PyClaw = Python + OpenClaw 的设计理念

从零构建，保留最核心的功能：
- Agent 运行时
- 工具调用系统
- 会话管理
- Web 界面

作者：骆戡
版本：0.1.0
