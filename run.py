#!/usr/bin/env python3
"""
PyClaw 智能启动脚本 - 自动检测系统，全平台通用
U盘兼容模式：直接用系统 Python 运行，不使用 venv
"""
import os
import sys
import subprocess
from pathlib import Path

# 修复 Windows CMD 中文/emoji 编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

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
        [sys.executable, '-m', 'pip', 'install', *core_pkgs, *mirror],  # 官方源镜像
    ]
    # Python 3.11+ 系统包管理器可能要求 --break-system-packages
    # 仅在前面都失败时才作为最后手段尝试
    if sys.version_info >= (3, 11):
        install_attempts.append(
            [sys.executable, '-m', 'pip', 'install', *core_pkgs, '--break-system-packages', *mirror]
        )
    
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
    # 自动清除代理（避免干扰国内 API 直连）
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']
    if any(os.environ.get(v) for v in proxy_vars):
        for var in proxy_vars:
            os.environ.pop(var, None)
        print("  ✅ 已自动清除代理变量")
    
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
    
    # 外网访问：默认仅本机，加 --allow-external 或 -e 参数开启
    allow_external = '--allow-external' in sys.argv or '-e' in sys.argv
    if allow_external:
        os.environ['PYCLAW_ALLOW_EXTERNAL'] = '1'
        print("✅ 已允许外网访问")
    else:
        os.environ['PYCLAW_ALLOW_EXTERNAL'] = '0'
        print("✅ 仅本机访问（加 --allow-external 开放局域网）")
    
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
        except OSError:
            pass
    
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    print()
    
    # 启动服务（非阻塞，以便自动打开浏览器）
    proc = subprocess.Popen([sys.executable, 'webapp.py'])
    
    # 自动打开浏览器
    import webbrowser, time
    time.sleep(1.5)  # 等服务器启动
    url = f"http://localhost:2469"
    try:
        webbrowser.open(url)
        print(f"🌐 已自动打开浏览器: {url}")
    except Exception:
        pass
    
    # 等待服务进程结束
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("👋 再见！")
