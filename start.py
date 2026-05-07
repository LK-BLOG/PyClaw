#!/usr/bin/env python3
"""PyClaw 启动脚本

提供多种启动选项，包括单会话服务器、多会话服务器、Web应用等。
支持命令行参数配置和错误处理。
"""

import os
import sys
import subprocess
import time
import argparse
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/startup.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
PYCLAW_PUBLIC_DIR = PROJECT_ROOT / "pyclaw-public"
PYCLAW_CORE_DIR = PROJECT_ROOT

def check_environment():
    """检查运行环境"""
    logger.info("检查运行环境")
    
    # 检查 Python 版本
    if sys.version_info < (3, 8):
        logger.error("需要 Python 3.8 或更高版本")
        return False
    
    # 检查项目目录
    if not PYCLAW_PUBLIC_DIR.exists():
        logger.error(f"找不到 pyclaw-public 目录: {PYCLAW_PUBLIC_DIR}")
        return False
    
    if not PYCLAW_CORE_DIR.exists():
        logger.error(f"找不到项目根目录: {PYCLAW_CORE_DIR}")
        return False
    
    logger.info("环境检查通过")
    return True

def wait_for_port(port: int, timeout: int = 30):
    """等待端口释放"""
    import socket
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('localhost', port))
                return False
        except:
            return True
            
        time.sleep(1)
    
    logger.error(f"端口 {port} 未在 {timeout} 秒内释放")
    return False

def start_webapp(host: str = '0.0.0.0', port: int = 5000):
    """启动 pyclaw-public/webapp.py"""
    logger.info(f"正在启动 Web 应用服务器 (http://{host}:{port})")
    
    # 检查端口是否被占用
    if not wait_for_port(port):
        logger.error(f"端口 {port} 已被占用")
        return False
    
    # 切换到 pyclaw-public 目录
    original_dir = Path.cwd()
    try:
        os.chdir(PYCLAW_PUBLIC_DIR)
        
        # 启动服务器
        cmd = [
            sys.executable,
            'webapp.py',
            '--host', host,
            '--port', str(port)
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动失败: {e}")
        return False
    except Exception as e:
        logger.error(f"启动过程中出现错误: {e}")
        return False
    finally:
        os.chdir(original_dir)

def start_single_session_server(host: str = '0.0.0.0', port: int = 8000):
    """启动单会话服务器 (server.py)"""
    logger.info(f"正在启动单会话服务器 (http://{host}:{port})")
    
    if not wait_for_port(port):
        logger.error(f"端口 {port} 已被占用")
        return False
    
    server_file = PROJECT_ROOT / "server.py"
    
    if not server_file.exists():
        logger.error(f"找不到服务器文件: {server_file}")
        return False
    
    cmd = [
        sys.executable,
        str(server_file),
        '--host', host,
        '--port', str(port)
    ]
    
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动失败: {e}")
        return False
    except Exception as e:
        logger.error(f"启动过程中出现错误: {e}")
        return False

def start_multi_session_server(host: str = '0.0.0.0', port: int = 8000):
    """启动多会话服务器 (server_multisession.py)"""
    logger.info(f"正在启动多会话服务器 (http://{host}:{port})")
    
    if not wait_for_port(port):
        logger.error(f"端口 {port} 已被占用")
        return False
    
    server_file = PROJECT_ROOT / "server_multisession.py"
    
    if not server_file.exists():
        logger.error(f"找不到服务器文件: {server_file}")
        return False
    
    cmd = [
        sys.executable,
        str(server_file),
        '--host', host,
        '--port', str(port)
    ]
    
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动失败: {e}")
        return False
    except Exception as e:
        logger.error(f"启动过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PyClaw 启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
启动选项:
  webapp              启动 pyclaw-public/webapp.py (Web 应用)
  single-session      启动单会话服务器 (server.py)
  multi-session       启动多会话服务器 (server_multisession.py)
  
示例:
  python start.py webapp --port 5001
  python start.py single-session --host 127.0.0.1 --port 8080
  python start.py multi-session --port 8001
        """.strip()
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='启动命令',
        required=True
    )
    
    # Web 应用选项
    webapp_parser = subparsers.add_parser('webapp', help='启动 pyclaw-public/webapp.py')
    webapp_parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    webapp_parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    
    # 单会话服务器选项
    single_parser = subparsers.add_parser('single-session', help='启动单会话服务器')
    single_parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    single_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    
    # 多会话服务器选项
    multi_parser = subparsers.add_parser('multi-session', help='启动多会话服务器')
    multi_parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    multi_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    
    args = parser.parse_args()
    
    logger.info("🚀 PyClaw 启动脚本")
    logger.info(f"项目根目录: {PROJECT_ROOT}")
    
    # 检查运行环境
    if not check_environment():
        sys.exit(1)
    
    # 执行启动命令
    if args.command == 'webapp':
        success = start_webapp(args.host, args.port)
    elif args.command == 'single-session':
        success = start_single_session_server(args.host, args.port)
    elif args.command == 'multi-session':
        success = start_multi_session_server(args.host, args.port)
    else:
        logger.error(f"未知命令: {args.command}")
        sys.exit(1)
    
    if not success:
        logger.error("启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
