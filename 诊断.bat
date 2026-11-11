@echo off
chcp 65001 >nul
title PyClaw 环境诊断
cd /d "%~dp0"

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
    echo [错误] 找不到 Python，请先安装 Python 3.9 以上版本
    pause
    exit /b 1
)

"%PYTHON%" check_env.py
pause
