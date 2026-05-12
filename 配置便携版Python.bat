@echo off
title PyClaw Portable Python Setup

cd /d "%~dp0"

echo.
echo ============================================
echo    PyClaw Portable Python Setup
echo ============================================
echo.

if not exist "python_portable\python.exe" (
    echo [ERROR] Portable Python not found at python_portable\python.exe
    echo Please make sure the python_portable folder exists.
    echo.
    pause
    goto end
)

cd python_portable

rem Check if pip already installed
echo [1/3] Checking pip...
python.exe -m pip --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] pip already installed
    python.exe -m pip --version
    goto deps
)

rem Try to install pip from get-pip.py
if exist "get-pip.py" (
    echo Installing pip from get-pip.py...
    python.exe get-pip.py
    if errorlevel 1 (
        echo [ERROR] pip installation failed!
        pause
        cd ..
        goto end
    )
    goto deps
)

rem Try ensurepip as fallback
echo Installing pip via ensurepip...
python.exe -m ensurepip --default-pip
if errorlevel 1 (
    echo [ERROR] No pip and no get-pip.py found!
    echo Please download get-pip.py to python_portable folder:
    echo   https://bootstrap.pypa.io/get-pip.py
    pause
    cd ..
    goto end
)
echo [OK] pip installed via ensurepip

:deps
echo.
echo [2/3] Installing PyClaw dependencies...

rem Prefer local wheels if available
if exist "wheels" (
    echo Using local wheels folder for offline install...
    python.exe -m pip install --no-index --find-links wheels httpx fastapi uvicorn websockets pytz python-multipart --no-warn-script-location
    if not errorlevel 1 (
        echo [OK] Dependencies installed from local wheels!
        goto cleanup
    )
    echo [WARN] Local wheels install failed, trying online...
)

rem Fallback to online install
python.exe -m pip install httpx fastapi uvicorn websockets pytz python-multipart --no-warn-script-location -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [ERROR] Dependency installation failed!
    pause
    cd ..
    goto end
)
echo [OK] Dependencies installed!

:cleanup
echo.
echo [3/3] Cleaning up...
if exist "get-pip.py" del get-pip.py
cd ..
echo.

echo ============================================
echo   [OK] Portable Python setup complete!
echo ============================================
echo.
echo Now you can run PyClaw on ANY Windows computer:
echo   * Just plug in the USB drive
echo   * Double-click: 启动.bat
echo   * No installation required!
echo.

:end
pause
