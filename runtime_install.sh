#!/bin/bash
# PyClaw 安装后引导：装依赖 + 注册 CLI + 生成 pyclaw 命令
cd "$(dirname "$0")"

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
    echo "[ERROR] Python 3.8+ not found."
    echo "        Download: https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] Using Python: $PYTHON"
echo
"$PYTHON" runtime_install.py
