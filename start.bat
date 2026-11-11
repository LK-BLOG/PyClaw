@echo off
rem 控制台默认 GBK，中文会乱码，先切到 UTF-8
chcp 65001 >nul
title 🦞 PyClaw
cd /d "%~dp0"

set http_proxy=
set https_proxy=
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set all_proxy=

echo   ╔══════════════════════════════╗
echo   ║     🦞 PyClaw               ║
echo   ╚══════════════════════════════╝
echo.

rem ----- 1. Find Python -----
set PYTHON=
where python >nul 2>&1
if not errorlevel 1 set PYTHON=python
if "%PYTHON%"=="" (
    where python3 >nul 2>&1
    if not errorlevel 1 set PYTHON=python3
)
if "%PYTHON%"=="" (
    if exist "python_portable\python.exe" set PYTHON=python_portable\python.exe
)

rem 安装时记录过解释器就用它，避免多个 Python 时 pip 装的和启动用的不是同一个
if exist ".pyclaw_python" (
    set /p RECORDED_PY=<.pyclaw_python
    if exist "%RECORDED_PY%" set PYTHON=%RECORDED_PY%
)
if "%PYTHON%"=="" (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
echo [OK] %PYTHON%

rem ----- 2. Start web server -----
echo [OK] Starting server at http://localhost:2469
start "PyClaw" "%PYTHON%" webapp.py

rem ----- 3. Wait until HTTP really answers, then open browser -----
rem Port alone is not enough: uvicorn listens but HTTP is not ready yet,
rem Edge would park on an offline page that never reloads. So poll /api/boot.
set /a TRIES=0
:waitloop
set /a TRIES+=1
powershell -NoProfile -Command "try{ $r=Invoke-WebRequest -Uri 'http://127.0.0.1:2469/api/boot' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ready
if %TRIES% GEQ 60 goto timeout
timeout /t 1 /nobreak >nul
goto waitloop

:timeout
echo [WARN] Server did not answer in 60s. Open http://localhost:2469 manually.
goto done

:ready
echo [OK] Server is answering, opening browser...
start http://localhost:2469

:done

echo.
echo [OK] PyClaw is running!
echo      Close this window to stop the server.
echo.
pause
