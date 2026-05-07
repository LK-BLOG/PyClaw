@echo off
cd /d "%~dp0"

rem 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 未找到Python，请确保已安装Python并添加到系统PATH中
    pause
    exit /b 1
)

rem 检查端口是否被占用
netstat -an | findstr /c:":8000 " >nul
if not errorlevel 1 (
    echo 端口8000已被占用，请先运行清理脚本
    pause
    exit /b 1
)

rem 启动多会话服务器
echo 正在启动PyClaw多会话服务器...
python -m uvicorn server_multisession:app --host 0.0.0.0 --port 8000 --reload