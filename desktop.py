#!/usr/bin/env python3
"""
PyClaw Desktop — 原生桌面窗口版
在线程中启动 uvicorn，不用子进程，避免 pid/端口/编码问题
"""
import os, sys, time, threading, socket, urllib.request, subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, '.pyclaw_desktop.log')

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{time.strftime("%H:%M:%S")}] {msg}\n')
    print(msg)

def port_free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', port)); s.close()
        return True
    except OSError:
        return False

def fallback_browser():
    log("🌐 回退到浏览器模式...")
    os.chdir(BASE)
    subprocess.Popen([sys.executable, 'run.py'])

def main():
    os.chdir(BASE)
    open(LOG, 'w').close()

    # ── 设置 IBus 输入法（中文输入法兼容）──
    if sys.platform == 'linux':
        os.environ.setdefault('GTK_IM_MODULE', 'ibus')
        os.environ.setdefault('QT_IM_MODULE', 'ibus')
        os.environ.setdefault('XMODIFIERS', '@im=ibus')

    # ── Linux 系统包自动安装 ──
    if sys.platform == 'linux':
        deps = []
        try: import gi
        except ImportError: deps.extend(['python3-gi', 'python3-gi-cairo', 'gir1.2-gtk-3.0', 'gir1.2-webkit2-4.0'])
        try: import gi.repository.WebKit2
        except ImportError: deps.extend(['gir1.2-webkit2-4.0'])
        if deps:
            log(f"📦 安装 Linux 桌面依赖 (输入 sudo 密码)...")
            r = subprocess.run(['sudo', 'apt-get', 'install', '-y'] + deps, timeout=120)
            if r.returncode != 0:
                log("⚠️ 安装失败，回退浏览器模式")
                fallback_browser(); return

    # ── pywebview ──
    try:
        import webview as wv
    except ImportError:
        log("📦 安装 pywebview...")
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pywebview', '-i',
                           'https://pypi.tuna.tsinghua.edu.cn/simple'], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log(f"❌ pywebview 安装失败: {r.stderr[-200:]}")
            fallback_browser(); return
        import webview as wv

    # ── 固定用户数据目录（保持 localStorage 持久化，不随项目路径变化） ──
    if sys.platform == 'win32':
        wv_data = os.path.join(os.environ.get('APPDATA', BASE), 'PyClaw', 'webview')
        os.environ['WEBVIEW2_USER_DATA_FOLDER'] = wv_data
    else:
        wv_data = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), 'pyclaw', 'webview')
    os.makedirs(wv_data, exist_ok=True)

    # ── 端口 ──
    port = 2469
    if not port_free(port):
        log(f"⚠️ 端口 {port} 被占用")
        for p in range(2469, 2500):
            if port_free(p): port = p; break
        else:
            log("❌ 无可用端口"); fallback_browser(); return

    # ── 在后台线程启动 uvicorn ──
    log(f"🦞 PyClaw Desktop 启动中 (端口 {port})...")
    os.environ['PYCLAW_ALLOW_EXTERNAL'] = '0'
    os.environ['PYTHONUNBUFFERED'] = '1'

    import uvicorn
    from webapp import app

    def run_server():
        uvicorn.run(app, host='127.0.0.1', port=port,
                    log_level='info', access_log=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # ── 等待就绪 ──
    for i in range(40):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=0.5)
            log("✅ 服务就绪")
            break
        except Exception:
            if i % 8 == 0:
                log(f"  等待中 ({i//2}s)...")
            time.sleep(0.5)
    else:
        log("❌ 服务启动超时")
        fallback_browser(); return

    # ── 窗口 ──
    log("🪟 打开桌面窗口...")
    try:
        window = wv.create_window(
            title='PyClaw',
            url=f'http://127.0.0.1:{port}',
            width=1100, height=760, min_size=(800, 520),
            resizable=True, text_select=True,
            background_color='#080b16',
        )
        wv.start(private_mode=False)
    except Exception as e:
        log(f"❌ 窗口失败: {e}")
        fallback_browser(); return

    log("👋 已关闭")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 再见！")
