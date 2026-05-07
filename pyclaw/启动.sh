#!/bin/bash
cd "$(dirname "$0")"

# 智能查找 Python3 - 兼容各种系统（包括老版本 Mac）
find_python3() {
    # 按优先级试各种可能的名字
    for cmd in python3 python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            version="$("$cmd" --version 2>&1 | head -1)"
            if echo "$version" | grep -q "Python 3"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    # Mac 额外试 Homebrew 路径
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
    echo "❌ 未找到 Python3！"
    echo ""
    
    # 智能检测系统，给出对应安装命令
    if [ "$(uname)" = "Darwin" ]; then
        OS_NAME="🍎 macOS"
        INSTALL_CMD="brew install python3"
    elif [ -f /etc/debian_version ]; then
        OS_NAME="🐧 Debian/Ubuntu"
        INSTALL_CMD="sudo apt update && sudo apt install python3 python3-pip python3-venv -y"
    elif [ -f /etc/redhat-release ]; then
        OS_NAME="🎩 RHEL/CentOS/Fedora"
        INSTALL_CMD="sudo dnf install python3 python3-pip -y"
    elif [ -f /etc/arch-release ]; then
        OS_NAME="🐧 Arch Linux"
        INSTALL_CMD="sudo pacman -S python python-pip --noconfirm"
    else
        OS_NAME="🐧 Linux"
        INSTALL_CMD=""
    fi
    
    echo "检测到系统: $OS_NAME"
    echo ""
    
    if [ -n "$INSTALL_CMD" ]; then
        echo "推荐安装命令:"
        echo "   $INSTALL_CMD"
        echo ""
        
        # 交互式询问是否自动安装
        if [ -t 0 ]; then  # 只在终端模式下询问
            read -p "需要我帮你自动安装吗？（y/N） " answer
            if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
                echo ""
                echo "🚀 开始自动安装 Python3...（可能需要输入密码）"
                echo ""
                eval "$INSTALL_CMD"
                echo ""
                echo "✅ 安装完成！正在重新启动 PyClaw..."
                sleep 2
                exec "$0"  # 重新运行自己
                exit 0
            fi
        fi
    else
        echo "请用你的包管理器安装 python3 和 python3-pip"
    fi
    
    echo ""
    echo "安装完成后，再次运行本脚本即可。"
    echo ""
    [ -t 0 ] && read -p "按回车退出"
    exit 1
fi

echo "✅ 已找到 Python: $PYTHON"
exec "$PYTHON" run.py

