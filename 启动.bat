@echo off
chcp 65001 >nul

:: 自动取消所有代理（DeepSeek API 国内可直接访问）
set http_proxy=
set https_proxy=
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set all_proxy=

:: 优先试 py launcher（Windows 官方多版本管理器）
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 run.py
    goto end
)

:: 试 python3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 run.py
    goto end
)

:: 最后试 python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python run.py
    goto end
)

echo ❌ 未找到 Python3！
echo 请先安装 Python3 后重试。
pause

:end
