#!/bin/bash
cd "$(dirname "$0")"

# 确保 Python 能找到用户 site-packages（root 环境兼容）
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}/home/claw/.local/lib/python3.12/site-packages"

# 自动取消所有代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

echo ""
echo "╔══════════════════════════════════╗"
echo "║     🦞 PyClaw AI 助手            ║"
echo "╚══════════════════════════════════╝"
echo ""

# 智能查找 Python3
find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            version=$("$cmd" --version 2>&1 | head -1)
            if echo "$version" | grep -q "Python 3"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python)

# 打开浏览器：Linux / macOS / Windows(Git Bash) 都兜住
open_url() {
    xdg-open "$1" >/dev/null 2>&1 && return 0
    open "$1" >/dev/null 2>&1 && return 0
    if command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe //c start "" "$1" >/dev/null 2>&1 && return 0
    fi
    if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Start-Process '$1'" >/dev/null 2>&1 && return 0
    fi
    return 1
}


if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python3！"
    echo "请先安装 Python 3.7+"
    echo ""
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "macOS:        brew install python3"
    echo ""
    [ -t 0 ] && read -p "按回车退出..."
    exit 1
fi

echo "✅ 已找到 Python: $PYTHON"
echo ""
echo "请选择启动模式："
echo "  1) 🖥️  Desktop  — 桌面窗口模式"
echo "  2) 🌐  Browser  — 浏览器模式（启动后手动打开 http://localhost:2469）"
echo "  3) 🔧  仅启动服务（无窗口，适合后台运行）"
echo ""
read -p "请输入 (1/2/3，默认 1): " choice
choice=${choice:-1}
echo ""

if [ "$choice" = "2" ] || [ "$choice" = "3" ]; then
    echo "🚀 正在启动 PyClaw Web 服务 (端口 2469)..."
    echo ""
    if [ "$choice" = "2" ]; then
        echo "🌐 浏览器模式：等服务真正能应答再打开浏览器"
        echo ""
        "$PYTHON" webapp.py &
        SERVER_PID=$!
        # 只等端口没用：TCP 通了但 HTTP 不回，浏览器会卡在 offline 页且不会自动重载
        i=0
        while [ $i -lt 60 ]; do
            if "$PYTHON" -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:2469/api/boot',timeout=2).read()" >/dev/null 2>&1; then
                break
            fi
            i=$((i+1))
            sleep 0.5
        done
        open_url "http://localhost:2469" || echo "请在浏览器打开 http://localhost:2469"
        echo ""
        echo "📌 按 Ctrl+C 停止服务"
        wait $SERVER_PID
    else
        echo "🔧 后台模式，服务运行在 http://localhost:2469"
        echo ""
        exec "$PYTHON" webapp.py
    fi
else
    echo "🚀 正在启动 PyClaw Desktop..."
    echo ""
    "$PYTHON" desktop.py
    
    EXIT_CODE=$?
    echo ""
    echo "━" $(date '+%H:%M:%S') "PyClaw 已退出 (code=$EXIT_CODE) ━"
    echo ""
    [ -f ".pyclaw_desktop.log" ] && echo "📄 日志: $(pwd)/.pyclaw_desktop.log"
    echo ""
    read -p "按回车关闭此窗口..." 
fi
