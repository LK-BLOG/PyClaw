# PyClaw 项目约定

给后面接手的人（或者 AI）看的。踩过的坑都记在这里，别再踩一遍。

## 版本号

发版要同时改三处，漏一个就出现版本不一致：

- `pyproject.toml` 的 `version`
- `pyclaw/__init__.py` 的 `VERSION`
- `index.html` 左上角 `<b>PyClaw</b><span>vX.Y.Z</span>`

## 发版流程

1. 跑测试：`python -m pytest tests/test_webui.py -q`，应该是 11 passed
2. 改版本号，`git commit -m "release: X.Y.Z"`
3. 更新 `RELEASE_NOTES.md`，release 正文就是它
4. `git tag -a vX.Y.Z -m "..."`，然后 `git push origin vX.Y.Z`
5. GitHub Actions（`.github/workflows/release.yml`）自动构建 NSIS 安装包，挂到 release

## 打包

- `installer.nsi` + `build_installer.py` 是构建脚本，**必须提交**。
  它们曾经被 `.gitignore` 排除，CI 里直接 `can't open file 'build_installer.py'`，构建挂掉。
- 本地构建：`python build_installer.py --makensis "C:\Program Files (x86)\NSIS\makensis.exe"`
- 产物 `PyClaw-for-Windows-Setup.exe` 不入库
- `installer.nsi` 里 `File /r` 会整包拷贝，靠 `/x` 排除敏感文件（`pyclaw.json`、`API.txt`、`*.key` 等）。加新文件类型时记得同步排除。

## 别提交的东西

`_w.log`、`_w.err`、`_webui.*`、`__pycache__/`、`history/`、`pyclaw_data/`、`pyclaw.json`。

测试跑出来的会话会堆在 `history/sessions`，收工前自己清（设置 → 数据 → 清理空会话，或者直接删）。

## WebUI 约定

- 固定端口 **2469**，不要换来换去。
- `webapp.py` 在 import fastapi **之前**先用标准库占住端口、返回 `splash.html`，
  加载完再交给 uvicorn。这段顺序不能动——它就是用来解决
  “浏览器打开时服务还没起来 → ERR_CONNECTION_REFUSED / Edge 停在 offline 页”的。
- 前端是单文件 `index.html`，没有构建步骤，改完刷新即可。
- 思考档位：前端存 localStorage 的 `pyclaw_effort`，后端读 `REASONING_EFFORT`。
  改档位时必须同时更新 `_BASE_AGENT["agent"].session.effort`，
  否则界面显示“关”、实际还在按旧档跑（`session.effort` 优先级高于全局配置）。
- 思考块要插在回答气泡**之前**。reasoning 有可能晚于正文到达，`append` 会让它跑到回答下面。
- 工具调用之后必须把 `S.aiEl` 置空，不然新回答会写进工具块上面那个元素。

## 编码（Windows 上最容易翻车的地方）

- `.bat` 必须是 **CRLF 换行**。LF 换行 cmd 会把命令行拆碎，报 `'mport' 不是内部命令` 这种鬼东西。
- `.bat` 内容有中文就配 `chcp 65001 >nul`，放在 `@echo off` 后面。
- `installer.nsi` 必须是 **UTF-8 with BOM**。makensis 靠 BOM 判断源文件编码，
  没有 BOM 就按 ANSI(GBK) 解，中文全变 `åŠ©æ‰‹`，开始菜单路径非法、快捷方式创建失败。
  用编辑器改完记得确认 BOM 还在（文件头是 `ef bb bf`）。
- 被 NSIS `nsExec` 调起的 Python 脚本，**不要**把 stdout 强改成 UTF-8，
  父窗口按 GBK 解码就是 `瀹夎鍚庡紩瀵`。按 `GetConsoleOutputCP()` 决定编码。
- `webapp.py` / `desktop.py` / `check_env.py` 是纯前台运行，启动时
  `SetConsoleOutputCP(65001)` 然后把 stdout 切 UTF-8，这样中文才正常。

## 测试

- 后端：`python -m pytest tests/test_webui.py -q`
- 前端：Playwright 脚本在 `D:\D老师的WorkSpace\_gh_audit\`
- 真实对话测试会花钱，先看余额
