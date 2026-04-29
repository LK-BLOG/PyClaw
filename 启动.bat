@echo off
chcp 65001 >nul
title PyClaw AI 助手

echo ══════════════════════════════════
echo   🦞 PyClaw AI 助手
echo ══════════════════════════════════
echo.

:: 自动取消所有代理
set http_proxy=
set https_proxy=
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set all_proxy=

:: 找 Python
set PYTHON_CMD=
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 set PYTHON_CMD=py -3
if "%PYTHON_CMD%"=="" (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 set PYTHON_CMD=python
)
if "%PYTHON_CMD%"=="" (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 set PYTHON_CMD=python3
)

if "%PYTHON_CMD%"=="" (
    echo ❌ 未找到 Python！
    echo 请先安装 Python 3.10+ 后重试
    pause
    exit /b 1
)

echo ✅ 已找到 Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: 检查依赖
echo [1/2] 检查依赖...
%PYTHON_CMD% -c "import fastapi, uvicorn, httpx" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 📦 正在安装依赖...
    %PYTHON_CMD% -m pip install fastapi uvicorn httpx python-multipart pytz -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [2/2] 启动 PyClaw 服务...
echo.

:: 启动 Web 服务（用默认 Python 的 uvicorn 模式）
%PYTHON_CMD% -m uvicorn webapp:app --host :: --port 2469

echo.
pause
