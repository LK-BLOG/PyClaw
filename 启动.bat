@echo off
title PyClaw AI Assistant

cd /d "%~dp0"

echo ==================================================
echo   PyClaw AI Assistant
echo ==================================================
echo.

rem Clear all proxies
set http_proxy=
set https_proxy=
set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=
set all_proxy=

rem PRIORITY 1: Use portable Python (USB version)
if exist "python_portable\python.exe" (
    echo [OK] Using portable Python
    python_portable\python.exe --version
    echo.
    python_portable\python.exe run.py
    goto end
)

rem PRIORITY 2: Try system python
where python >nul 2>&1
if not errorlevel 1 (
    echo [OK] Found system python
    python --version
    echo.
    python run.py
    goto end
)

rem PRIORITY 3: Try python3
where python3 >nul 2>&1
if not errorlevel 1 (
    echo [OK] Found python3
    python3 --version
    echo.
    python3 run.py
    goto end
)

echo [ERROR] No Python found!
echo.
echo Options:
echo   1. Run "配置便携版Python.bat" to setup portable Python
echo   2. Or install Python 3.11/3.12 from python.org
echo      and check "Add Python to PATH"
echo.

:end
echo.
echo ==================================================
echo  Program exited. Press any key to close.
echo ==================================================
pause >nul
