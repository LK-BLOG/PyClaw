# PyClaw（Web 版）

> 纯 Python 的本地 AI 助手：Claude 风格的 WebUI + pyclaw-lite 内核（插件 / 权限 / 上下文压缩 / MCP / hooks）。

## 怎么跑

```powershell
cd D:\PyClaw-For-win
python -m pip install -r requirements.txt   # 第一次
python webapp.py --port 2469
```

或者直接双击 / 执行 `start.sh`（Git Bash）或 `start.bat`，它们会等服务真正能应答了再开浏览器。

**启动页**：`webapp.py` 在 import 依赖**之前**就用标准库把端口占住，先回一个纯黑的启动页，
再慢慢加载 fastapi / pyclaw。加载完关掉占位服务，把端口交给 uvicorn。
所以不管浏览器多早打开，都不会再看到 ERR_CONNECTION_REFUSED 或者 Edge 的 offline 页。
启动页会自己轮询 `/api/boot`，真应用一应答就跳过去。

启动后控制台会打印 `ACCESS_TOKEN=...`（首次运行自动生成并写回 `pyclaw.json` 的 `WEBUI_TOKEN`）。
浏览器打开 `http://127.0.0.1:2469/`，把令牌填进去；或者直接访问：

```
http://127.0.0.1:2469/?token=<你的令牌>
```

`?token=` 会顺手写进 localStorage，之后不用再带。

## 界面

- **启动层**：纯黑背景，PyClaw logo 描边动画；进度跟真实加载走，动画结束直接进入有内容的界面。
- **会话列表**：按最后活跃时间倒序，每行右侧显示“刚刚 / 47分钟 / 11月10日”。
  顶部有搜索框，`✎` 改名，`×` 删除（会二次确认）。
- **设置**：双栏导航（常规 / 外观 / 模型 / 能力 / 连接 / 技能 / 工具 / 插件 / 数据 / 关于）
  - 外观：主题三态（跟随系统 / 浅色 / 深色）、字体（无衬线 / 衬线 / 等宽）、动效（完整 / 减弱）
  - 模型：供应商目录、Key（密码框）、接口地址、模型（可拉取真实列表）、连通性测试、余额
  - 能力：权限模式（帮我批准 / 自动批准 / 完全访问）、思考强度（off → ultra）、助手名称
  - 数据：导出全部会话、清理空会话、清空会话、恢复默认
- **渲染**：完整 markdown（标题、列表、任务列表、引用、表格、代码块、链接、图片、删除线）+ **IUI 智能组件**。

## IUI（智能 UI）

模型在回答里写一个 ` ```iui ` 代码块（内容为 JSON），前端就把它渲染成可交互组件：

```iui
{"type":"card","icon":"🦞","title":"PyClaw 体检","body":"三个模块正常。","stats":[{"label":"提交","value":"248"}],"actions":[{"label":"看详情","send":"列出模块清单","style":"primary"}]}
```

支持的组件：`card` / `list` / `table` / `buttons` / `form` / `chart` / `callout` / `progress` / `carousel` / `image`。
按钮的 `send` 会当作一条用户消息发回模型，`href` 打开链接，`copy` 复制文本。

## 插件

`plugins/` 下自带六个：

| 插件 | 工具 | 说明 |
|---|---|---|
| file | read_file / write_file / list_dir / grep_files | 文件读写与检索 |
| web | fetch_url / web_search | 抓网页正文、搜索 |
| time | now / from_timestamp | 时间与时区 |
| memory | memory_write / memory_read | 长期记忆，写进 `memory/` |
| process | list_processes / port_check / kill_process | 进程与端口 |
| ppt | make_ppt | 用 python-pptx 生成 PPTX |

插件契约：`plugins/<name>/plugin.json` + `tools.py`（`register(ctx)` 里 `ctx.add_tool(...)`）。
`~/.pyclaw/plugins` 与 `~/.codex/plugins` 里的插件也会被发现（在设置 → 插件里显示启用状态）。

## 配置

`pyclaw.json`（lite 键位）：

```json
{
  "PROVIDER": "deepseek",
  "ENDPOINT": "https://api.deepseek.com/v1",
  "API_KEY": "sk-...",
  "MODEL": "deepseek-flash",
  "WEBUI_TOKEN": "...",
  "APPROVAL_MODE": "auto",
  "REASONING_EFFORT": "high",
  "AGENT_NAME": "PyClaw",
  "PLUGIN_DIRS": ["plugins"]
}
```

## 旧版兼容

- `API.txt` / `volc_api.txt` 里的 Key 会在启动时自动读进 `API_KEY`
- 旧的 `ACCESS_TOKEN` 自动映射为 `WEBUI_TOKEN`
- `ENDPOINT` 缺 `/v1` 会自动补
- 旧内核与旧前端保留为 `pyclaw_legacy/`、`webapp_legacy.py`、`index.html.bak-before-boot`、`index.html.v1-claude`，随时可以回滚
- `/api/info` 的 `legacy` 字段会报告旧数据情况（`api_txt` / `token` / `old_sessions`）

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/boot | 启动进度（启动层用） |
| GET | /api/info | 运行时信息、插件清单、权限与强度、旧版状态 |
| GET | /api/providers | 供应商目录 |
| GET | /api/models | 后端代拉模型列表 |
| GET | /api/keycheck | Key 连通性探测 |
| GET | /api/balance | 余额（DeepSeek / OpenRouter） |
| GET | /api/plugins | 插件列表 |
| POST | /api/config | 保存权限模式 / 思考强度 / 助手名称 |
| WS | /ws | 对话协议（chat / history / list_sessions / set_config ...） |

## 启动性能

`webapp.py` 一进来先抢端口（0.1s 内启动页可用），之后才是那 1.9s 的依赖 import。
所以“浏览器打开时服务还没好”这件事从根上没了：最坏情况也是先看到启动页，再自动跳转。

真正的应用加载（读配置、打开会话库）实测 **0.5~0.7s**；供应商探测、插件扫描、会话预热全部丢到后台任务。

## 旧会话迁移

启动时自动把 `pyclaw_data/pyclaw_sessions.json` 里的会话转成 lite 的 `history/sessions/*.jsonl`，迁移完成后写 `pyclaw_data/.migrated_to_lite`，不会重复迁移。也可以手动触发：

```powershell
curl -X POST http://127.0.0.1:2469/api/migrate
```

实测迁入 83 个会话，原文件不动。

## 测试

```powershell
cd D:\PyClaw-For-win
python -m pytest tests/test_webui.py -q
```

覆盖：供应商目录、模型回退、插件发现与工具签名、`/api/info` 结构、`/api/config` 落盘、WS 令牌校验、WS 会话列表、时间插件真实执行、旧会话迁移。当前 **10 passed**。

## 配置热更新

WS 的 `set_config` 现在也接受 `approval` / `effort` / `agent_name`，保存后清空 agent 与插件缓存并回报 `config_saved`。
