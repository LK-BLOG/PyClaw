#!/bin/bash
cd "$(dirname "$0")"

# 自动取消所有代理（DeepSeek API 国内可直接访问）
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

# 直接运行 run.py（U盘模式，不使用 venv）
echo "🚀 正在启动 PyClaw..."
echo ""
exec "$PYTHON" run.py
