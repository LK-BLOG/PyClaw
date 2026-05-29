#!/usr/bin/env bash
# 🦞 PyClaw 一键安装脚本 (Linux / macOS)
# 用法:
#   本地: ./install.sh.sh
#   远程: curl -fsSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh | bash

set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
DIM='\033[2m'
RESET='\033[0m'

echo -e "${CYAN}"
echo "   ╔══════════════════════════════╗"
echo "   ║     🦞 PyClaw 一键安装      ║"
echo "   ╚══════════════════════════════╝"
echo -e "${RESET}"

# ── 检测 Python ──
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        MAJOR=${VER%.*}
        MINOR=${VER#*.}
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            echo -e "  ${GREEN}✅ Python ${VER}+${RESET}"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}❌ 需要 Python 3.8+，请先安装:${RESET}"
    echo "     apt install python3 python3-pip  (Debian/Ubuntu)"
    echo "     brew install python3             (macOS)"
    exit 1
fi

# ── 检测 Git ──
if ! command -v git &>/dev/null; then
    echo -e "  ${YELLOW}⚠️  未检测到 git，将使用 curl 下载${RESET}"
fi

# ── 进入项目目录 ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 如果在 /tmp 或 HOME 下运行（远程管道模式），clone 项目
if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == "$HOME" && "$0" == "bash" ]]; then
    echo -e "  ${DIM}📦 下载 PyClaw...${RESET}"
    if command -v git &>/dev/null; then
        git clone --depth 1 https://github.com/LK-BLOG/PyClaw.git /tmp/pyclaw-install 2>/dev/null || true
        if [ -d /tmp/pyclaw-install ]; then
            PROJECT_DIR="/tmp/pyclaw-install"
        fi
    fi

    # git 失败回退到 curl
    if [ ! -d "$PROJECT_DIR/pyclaw" ]; then
        curl -fsSL https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main -o /tmp/pyclaw.tar.gz
        mkdir -p /tmp/pyclaw-install
        tar -xzf /tmp/pyclaw.tar.gz -C /tmp/pyclaw-install --strip-components=1
        PROJECT_DIR="/tmp/pyclaw-install"
    fi
    cd "$PROJECT_DIR"
    echo -e "  ${GREEN}✅ 下载完成${RESET}"
fi

# ── 安装 pyclaw CLI ──
echo -e "  ${DIM}🔧 安装 pyclaw 命令...${RESET}"
if pip install --break-system-packages -e "$PROJECT_DIR" 2>/dev/null; then
    echo -e "  ${GREEN}✅ pyclaw 命令已安装 (pip)${RESET}"
elif pip install --user -e "$PROJECT_DIR" 2>/dev/null; then
    echo -e "  ${GREEN}✅ pyclaw 命令已安装 (user)${RESET}"
else
    # 回退到 symlink
    mkdir -p ~/.local/bin
    ln -sf "$PROJECT_DIR/pyclaw.sh" ~/.local/bin/pyclaw
    echo -e "  ${GREEN}✅ pyclaw 命令已安装 (symlink)${RESET}"
    echo -e "  ${DIM}   确保 ~/.local/bin 在 PATH 中${RESET}"
fi

# ── 安装依赖 ──
echo -e "  ${DIM}📦 安装 Python 依赖...${RESET}"
"$PYTHON" -m pip install --break-system-packages httpx uvicorn fastapi websockets 2>/dev/null || \
"$PYTHON" -m pip install --user httpx uvicorn fastapi websockets 2>/dev/null || true

# ── 配置向导 ──
echo ""
echo -e "  ${CYAN}🧞 打开配置向导...${RESET}"
cd "$PROJECT_DIR"
if [ -f "API.txt" ] && [ -s "API.txt" ]; then
    echo -e "  ${DIM}   已有配置，跳过${RESET}"
    echo -e "  ${DIM}   想重新配置请运行: pyclaw setup${RESET}"
else
    "$PYTHON" -m pyclaw.cli setup
fi

# ── 完成 ──
echo ""
echo -e "${GREEN}   ╔══════════════════════════════╗"
echo -e "   ║     🦞 PyClaw 安装完成!      ║"
echo -e "   ╚══════════════════════════════╝${RESET}"
echo ""
echo -e "   ${CYAN}启动:${RESET}"
echo -e "     pyclaw start             交互选择模式"
echo -e "     pyclaw start --mode web 浏览器模式"
echo ""
echo -e "   ${CYAN}其他命令:${RESET}"
echo -e "     pyclaw shell             交互对话"
echo -e "     pyclaw setup             重新配置"
echo -e "     pyclaw status            查看状态"
echo ""
