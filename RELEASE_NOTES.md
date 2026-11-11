内核换成 pyclaw-lite，WebUI 整体重写。

## 启动

- **启动页占端口**：`webapp.py` 在 import 依赖**之前**就用标准库把 2469 占住，0.1 秒就能回页面，加载完自动交给 uvicorn。再也不会出现 `ERR_CONNECTION_REFUSED` 或者 Edge 停在 offline 页不重载。
- `start.sh` / `start.bat` 改成轮询 `/api/boot` 拿到 200 才开浏览器；Git Bash 下补了 `cmd.exe //c start` 的打开方式。

## 界面

- Claude 风格设计令牌，蓝黄配色，暗 / 亮主题，字体与字号可调
- 会话列表按最后活跃时间倒序，每行显示相对时间，顶部带搜索框
- 删除会话二次确认，`✎` 重命名
- 窄屏抽屉侧栏，点外部收起
- IUI 智能组件：`card` / `list` / `table` / `buttons` / `form` / `chart` / `callout` / `progress` / `carousel` / `image`

## 对话

- 思考块排在回答**之前**；关闭思考后不再渲染推理内容（前端拦 + 后端丢包）
- 思考强度真正热更新：`/api/config` 会同步内存 agent 的 `session.effort`，切会话时也按当前配置对齐
- 工具调用后回答不再错位，没吐内容的空气泡自动清理
- 打断 0.3 秒生效，可以立刻继续发，连续打断也能恢复
- 图片走 vision 插件转内容块

## 依赖

- `pyproject.toml` 补上 `dependencies`（之前一个包都不装）
- 新增 `requirements.txt`，`install.sh` / `runtime_install.py` 直接读它，安装失败不再静默吞掉

## 数据

- 会话索引按真实时间戳解析，不再全排到最底
- 查看历史不再凭空创建空会话；列表刷新时自动清理幽灵行
- 数据面板新增「清理空会话」
