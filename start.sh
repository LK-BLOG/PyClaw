#!/bin/bash
cd "$(dirname "$0")"

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

# 默认桌面版，失败或退出后暂停
echo "🚀 正在启动 PyClaw Desktop..."
echo ""

# 不加 exec，确保退出后 shell 继续执行下面的 pause
"$PYTHON" desktop.py

EXIT_CODE=$?
echo ""
echo "━" $(date '+%H:%M:%S') "PyClaw 已退出 (code=$EXIT_CODE) ━"
echo ""
[ -f ".pyclaw_desktop.log" ] && echo "📄 日志: $(pwd)/.pyclaw_desktop.log"
echo ""
read -p "按回车关闭此窗口..." 
