#!/usr/bin/env python3
"""
PyClaw 智能启动脚本 - 自动检测系统，全平台通用
U盘兼容模式：直接用系统 Python 运行，不使用 venv
"""
import os
import sys
import subprocess
from pathlib import Path

def get_platform():
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    return 'unknown'

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import fastapi
        import httpx
        import uvicorn
        return True
    except ImportError:
        return False

def install_dependencies():
    """安装依赖"""
    print()
    print("[1/2] 正在安装依赖...")
    print()
    
    # 尝试多种安装方式
    install_args = [
        [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--break-system-packages'],
    ]
    
    for i, args in enumerate(install_args, 1):
        try:
            subprocess.run(args, check=True, capture_output=True)
            return True
        except:
            continue
    
    print("⚠️  自动安装失败，请手动安装依赖:")
    print(f"   {sys.executable} -m pip install fastapi httpx uvicorn python-multipart --break-system-packages")
    return False

def main():
    os.chdir(Path(__file__).parent)
    
    print()
    print("=" * 50)
    print("     🦞 PyClaw AI 助手")
    print("=" * 50)
    print()
    
    platform = get_platform()
    print(f"检测到系统: {platform}")
    print(f"Python 路径: {sys.executable}")
    
    # 检查依赖
    if not check_dependencies():
        if not install_dependencies():
            print("\n❌ 依赖安装失败，请手动安装后重试")
            input("按回车退出...")
            return
    
    # 启动服务
    print()
    print("[2/2] 正在启动 PyClaw 服务...")
    print()
    print("✅ 启动成功！")
    print("🌐 访问地址: http://localhost:2469")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    print()
    
    # 直接用当前 Python 运行
    subprocess.run([sys.executable, 'webapp.py'])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("👋 再见！")
