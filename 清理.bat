@echo off
chcp 65001 >nul

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3 -c "import shutil, os, glob; [shutil.rmtree(d, ignore_errors=True) for d in ['__pycache__', 'pyclaw/__pycache__', 'venv']]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]; print('✅ 清理完成！'); print('现在可以复制整个文件夹了，到新电脑双击「启动.bat」自动重建')"
    goto end
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 -c "import shutil, os, glob; [shutil.rmtree(d, ignore_errors=True) for d in ['__pycache__', 'pyclaw/__pycache__', 'venv']]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]; print('✅ 清理完成！'); print('现在可以复制整个文件夹了，到新电脑双击「启动.bat」自动重建')"
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -c "import shutil, os, glob; [shutil.rmtree(d, ignore_errors=True) for d in ['__pycache__', 'pyclaw/__pycache__', 'venv']]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]; print('✅ 清理完成！'); print('现在可以复制整个文件夹了，到新电脑双击「启动.bat」自动重建')"
    goto end
)

echo ❌ 未找到 Python3！
echo 请先安装 Python3 后重试。
pause

:end
