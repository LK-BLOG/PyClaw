@echo off
cd /d "%~dp0"

rem 停止多会话服务器进程
echo 正在停止PyClaw多会话服务器...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

rem 清理临时文件和日志
echo 正在清理临时文件和日志...
if exist "logs\*.log" (
    del /q "logs\*.log"
)
if exist "pyclaw\__pycache__" (
    rmdir /s /q "pyclaw\__pycache__"
)

echo 清理完成！