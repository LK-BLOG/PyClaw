@echo off
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

rem ----- 3. Wait a moment then open browser -----
timeout /t 3 /nobreak >nul
start http://localhost:2469

echo.
echo [OK] PyClaw is running!
echo      Close this window to stop the server.
echo.
pause
