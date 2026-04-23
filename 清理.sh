#!/bin/bash
cd "$(dirname "$0")"

find_python3() {
    for cmd in python3 python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            version="$("$cmd" --version 2>&1 | head -1)"
            if echo "$version" | grep -q "Python 3"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    if [ -f "/usr/local/bin/python3" ]; then
        echo "/usr/local/bin/python3"
        return 0
    fi
    if [ -f "/opt/homebrew/bin/python3" ]; then
        echo "/opt/homebrew/bin/python3"
        return 0
    fi
    return 1
}

PYTHON="$(find_python3)"

if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python3！请先安装后重试。"
    exit 1
fi

$PYTHON -c "
import shutil, os, glob
[shutil.rmtree(d, ignore_errors=True) for d in ['__pycache__', 'pyclaw/__pycache__', 'venv']]
[os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]
print('✅ 清理完成！')
print('现在可以复制整个文件夹了，到新电脑运行 ./启动.sh 自动重建')
"
