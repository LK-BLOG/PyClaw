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
    """安装依赖 - 仅安装核心包，跳过可能在新 Python 上失败的可选依赖"""
    print()
    print("[1/2] 正在安装依赖...")
    print()
    
    # 只装运行必需的核心包
    core_pkgs = ['fastapi', 'httpx', 'uvicorn', 'python-multipart', 'websockets', 'pytz']
    
    # 多种安装方式按顺序尝试，使用清华镜像加速国内用户
    mirror = ['-i', 'https://pypi.tuna.tsinghua.edu.cn/simple']
    install_attempts = [
        [sys.executable, '-m', 'pip', 'install', *core_pkgs, *mirror],
        [sys.executable, '-m', 'pip', 'install', *core_pkgs, '--user', *mirror],
        [sys.executable, '-m', 'pip', 'install', *core_pkgs, '--break-system-packages', *mirror],
        [sys.executable, '-m', 'pip', 'install', *core_pkgs],  # 最后试官方源
    ]
    
    last_err = ''
    for i, args in enumerate(install_attempts, 1):
        method = '默认' if i == 1 else ('--user' if i == 2 else ('--break-system-packages' if i == 3 else '官方源'))
        print(f"   尝试 {i}/{len(install_attempts)}: {method}...")
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("✅ 依赖安装成功！")
                return True
            last_err = (result.stderr or result.stdout or '')[-800:]
        except subprocess.TimeoutExpired:
            last_err = "安装超时（5分钟）"
        except Exception as e:
            last_err = str(e)
    
    print()
    print("⚠️  自动安装失败！最后错误信息:")
    print("-" * 50)
    print(last_err)
    print("-" * 50)
    print()
    print("请手动安装依赖:")
    print(f"   {sys.executable} -m pip install fastapi httpx uvicorn python-multipart websockets pytz -i https://pypi.tuna.tsinghua.edu.cn/simple --user")
    print()
    print("💡 提示：如果你的 Python 是 3.14（很新），建议改用 Python 3.11 或 3.12")
    print("   下载: https://www.python.org/downloads/release/python-3127/")
    return False

def main():
    # 自动取消所有代理（DeepSeek API 国内可直接访问）
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']
    for var in proxy_vars:
        os.environ.pop(var, None)
    
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
    
    # 询问是否允许外网访问
    print()
    print("[网络设置]")
    print("  Y = 允许内外网访问（同一局域网可访问，公网暴露有风险）")
    print("  N = 仅本机访问（最安全，默认）")
    print()
    
    while True:
        allow_external = input("⚠️  允许外网访问吗？(Y/N，默认 N): ").strip().upper()
        if not allow_external:
            allow_external = 'N'
            break
        if allow_external in ['Y', 'N']:
            break
        print("  请输入 Y 或 N")
    
    # 设置环境变量传递给 webapp.py
    if allow_external == 'Y':
        os.environ['PYCLAW_ALLOW_EXTERNAL'] = '1'
        host = '0.0.0.0'
        print(f"✅ 已允许外网访问，监听地址: {host}")
    else:
        os.environ['PYCLAW_ALLOW_EXTERNAL'] = '0'
        host = '127.0.0.1'
        print(f"✅ 仅本机访问，监听地址: {host}")
    
    # 启动服务
    print()
    print("[2/2] 正在启动 PyClaw 服务...")
    print()
    print("✅ 启动成功！")
    print(f"🌐 本机访问: http://localhost:2469")
    
    if allow_external == 'Y':
        # 尝试获取本机 IP 地址
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"🌐 局域网访问: http://{local_ip}:2469")
        except:
            pass
    
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
