#!/usr/bin/env bash
# 🦞 PyClaw One-Click Install (Linux/macOS)
set -e

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
DIM='\033[2m'
RESET='\033[0m'

echo -e "${CYAN}"
echo "   ╔══════════════════════════════╗"
echo "   ║     🦞 PyClaw Installer     ║"
echo "   ╚══════════════════════════════╝"
echo -e "${RESET}"

# ── 语言选择 ──
printf "\n  ${CYAN}Language / 语言${RESET}\n"
printf "    1) English\n"
printf "    2) 中文\n"
printf "\n  ${CYAN}Choose (1/2): ${RESET}"
read lang_choice < /dev/tty 2>/dev/null || read lang_choice
echo ""

if [[ "$lang_choice" == "2" ]]; then
    # 中文
    MSG_PYTHON_OK="检测到"
    MSG_PYTHON_REQ="需要 Python 3.8+，请先安装"
    MSG_GIT_NOT_FOUND="未检测到 git，将使用 curl 下载"
    MSG_DOWNLOADING="正在下载 PyClaw..."
    MSG_DOWNLOAD_OK="下载完成"
    MSG_CLI_PROMPT="是否安装 pyclaw 命令行工具?"
    MSG_CLI_INSTALLED="安装后可在终端直接运行 pyclaw <command>"
    MSG_CLI_SKIPPED="不安装则需 python -m pyclaw.cli <command>"
    MSG_CLI_ASK="安装 CLI? (Y/n)"
    MSG_CLI_INSTALL="正在安装 pyclaw 命令..."
    MSG_CLI_OK="pyclaw 命令已安装"
    MSG_CLI_PIP_OK="(pip)"
    MSG_CLI_USER_OK="(user)"
    MSG_CLI_SYMLINK_OK="(symlink)"
    MSG_CLI_PATH_HINT="确保 ~/.local/bin 在 PATH 中"
    MSG_CLI_SKIP="跳过 CLI 安装"
    MSG_PIP_FAIL="pip 安装失败，回退到脚本模式"
    MSG_PIP_CMD="使用"
    MSG_DEPS="正在安装 Python 依赖..."
    MSG_CFG_EXIST="已有配置，跳过"
    MSG_WIZARD="打开配置向导..."
    MSG_READY="安装完成!"
    MSG_START="启动"
    MSG_CMDS="命令"
    MSG_SHORTCUT_CREATE="创建桌面快捷方式"
    MSG_SHORTCUT_DESC="一键启动: 开启服务 + 打开浏览器"
    MSG_SHORTCUT_ASK="创建快捷方式"
    MSG_SHORTCUT_OK="桌面快捷方式已创建!"
    MSG_SHORTCUT_SKIP="跳过创建桌面快捷方式"
    MSG_SKILL_PROMPT="选择要禁用的 Skill (Space选择, Enter确认)"
    MSG_SKILL_HELP="选中的 Skill 将被移入回收站，不加载"
    MSG_SKILL_DONE="Skill 配置完成"
    MSG_SKILL_SKIP="跳过 Skill 配置"
    MSG_SKILL_TIP="输入编号（逗号分隔，留空=全部保留）"
else
    # English
    MSG_PYTHON_OK="detected"
    MSG_PYTHON_REQ="Python 3.8+ required. Install it"
    MSG_GIT_NOT_FOUND="git not found, will use curl to download"
    MSG_DOWNLOADING="Downloading PyClaw..."
    MSG_DOWNLOAD_OK="Download complete"
    MSG_CLI_PROMPT="Install pyclaw CLI?"
    MSG_CLI_INSTALLED="Installed: run 'pyclaw <command>' anywhere"
    MSG_CLI_SKIPPED="Skipped: use 'python -m pyclaw.cli <command>' instead"
    MSG_CLI_ASK="Install CLI? (Y/n)"
    MSG_CLI_INSTALL="Installing pyclaw command..."
    MSG_CLI_OK="pyclaw command installed"
    MSG_CLI_PIP_OK="(pip)"
    MSG_CLI_USER_OK="(user)"
    MSG_CLI_SYMLINK_OK="(symlink)"
    MSG_CLI_PATH_HINT="Make sure ~/.local/bin is in your PATH"
    MSG_CLI_SKIP="Skipped CLI install"
    MSG_PIP_FAIL="pip install failed, fallback to script:"
    MSG_PIP_CMD="Use"
    MSG_DEPS="Installing Python dependencies..."
    MSG_CFG_EXIST="Config already exists, skipping"
    MSG_WIZARD="Launching setup wizard..."
    MSG_READY="Ready!"
    MSG_START="Start"
    MSG_CMDS="Commands"
    MSG_SHORTCUT_CREATE="Create desktop shortcut"
    MSG_SHORTCUT_DESC="One-click launch: starts server + opens browser"
    MSG_SHORTCUT_ASK="Create shortcut"
    MSG_SHORTCUT_OK="Desktop shortcut created!"
    MSG_SHORTCUT_SKIP="Skipped desktop shortcut"
    MSG_SKILL_PROMPT="Select Skills to disable (SPACE select, Enter confirm)"
    MSG_SKILL_HELP="Selected skills will be moved to trash"
    MSG_SKILL_DONE="Skills configured"
    MSG_SKILL_SKIP="Skipped skill configuration"
    MSG_SKILL_TIP="Enter numbers (comma separated, empty=keep all)"
fi

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        MAJOR=${VER%.*}
        MINOR=${VER#*.}
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            echo -e "  ${GREEN}✅ Python ${VER}+ ${MSG_PYTHON_OK}${RESET}"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}❌ ${MSG_PYTHON_REQ}:${RESET}"
    echo "     apt install python3 python3-pip  (Debian/Ubuntu)"
    echo "     brew install python3             (macOS)"
    echo "     https://www.python.org/downloads/ (manual)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == "$HOME" && "$0" == "bash" ]]; then
    echo -e "  ${DIM}📦 ${MSG_DOWNLOADING}${RESET}"
    if command -v git &>/dev/null; then
        git clone --depth 1 https://github.com/LK-BLOG/PyClaw.git /tmp/pyclaw-install 2>/dev/null || true
        if [ -d /tmp/pyclaw-install ]; then
            PROJECT_DIR="/tmp/pyclaw-install"
        fi
    fi

    if [ ! -d "$PROJECT_DIR/pyclaw" ]; then
        curl -fsSL https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main -o /tmp/pyclaw.tar.gz
        mkdir -p /tmp/pyclaw-install
        tar -xzf /tmp/pyclaw.tar.gz -C /tmp/pyclaw-install --strip-components=1
        PROJECT_DIR="/tmp/pyclaw-install"
    fi
    cd "$PROJECT_DIR"
    echo -e "  ${GREEN}✅ ${MSG_DOWNLOAD_OK}${RESET}"
fi

printf "\n  ${CYAN}🔧 ${MSG_CLI_PROMPT}${RESET}\n"
printf "     ${MSG_CLI_INSTALLED}\n"
printf "     ${MSG_CLI_SKIPPED}\n"
printf "\n  ${CYAN}${MSG_CLI_ASK}: ${RESET}"
read install_cli < /dev/tty 2>/dev/null || read install_cli
install_cli=${install_cli:-y}

if [[ "$install_cli" == "y" ]] || [[ "$install_cli" == "Y" ]] || [[ "$install_cli" == "" ]]; then
    echo -e "  ${DIM}🔧 ${MSG_CLI_INSTALL}${RESET}"
    if pip install --break-system-packages -e "$PROJECT_DIR" 2>/dev/null; then
        echo -e "  ${GREEN}✅ ${MSG_CLI_OK} (pip)${RESET}"
    elif pip install --user -e "$PROJECT_DIR" 2>/dev/null; then
        echo -e "  ${GREEN}✅ ${MSG_CLI_OK} (user)${RESET}"
    else
        mkdir -p ~/.local/bin
        ln -sf "$PROJECT_DIR/pyclaw.sh" ~/.local/bin/pyclaw
        echo -e "  ${GREEN}✅ ${MSG_CLI_OK} (symlink)${RESET}"
        echo -e "  ${DIM}   ${MSG_CLI_PATH_HINT}${RESET}"
    fi
else
    echo -e "  ${YELLOW}⏭️  ${MSG_CLI_SKIP}${RESET}"
fi

echo -e "  ${DIM}📦 ${MSG_DEPS}${RESET}"
"$PYTHON" -m pip install --break-system-packages httpx uvicorn fastapi websockets 2>/dev/null || \
"$PYTHON" -m pip install --user httpx uvicorn fastapi websockets 2>/dev/null || true

printf "\n  ${CYAN}📌 ${MSG_SHORTCUT_CREATE}?${RESET}\n"
printf "     ${MSG_SHORTCUT_DESC}\n"
printf "\n  ${CYAN}${MSG_SHORTCUT_ASK} (Y/n): ${RESET}"
read create_shortcut < /dev/tty 2>/dev/null || read create_shortcut
create_shortcut=${create_shortcut:-y}

if [[ "$create_shortcut" == "y" ]] || [[ "$create_shortcut" == "Y" ]] || [[ "$create_shortcut" == "" ]]; then
    SHORTCUT_PATH="$HOME/Desktop/pyclaw.desktop"
    mkdir -p "$HOME/Desktop"
    cat > "$SHORTCUT_PATH" <<SHORTCUT_EOF
[Desktop Entry]
Name=PyClaw
Comment=🦞 PyClaw AI Assistant
Exec=$PROJECT_DIR/start.sh
Icon=$PROJECT_DIR/pyclaw.png
Terminal=true
Type=Application
Categories=Network;AI;
SHORTCUT_EOF
    chmod +x "$SHORTCUT_PATH"
    cp "$SHORTCUT_PATH" "$HOME/.local/share/applications/pyclaw.desktop" 2>/dev/null || true
    echo -e "  ${GREEN}✅ ${MSG_SHORTCUT_OK}${RESET}"
else
    echo -e "  ${YELLOW}⏭️  ${MSG_SHORTCUT_SKIP}${RESET}"
fi

cd "$PROJECT_DIR"
if [ -f "API.txt" ] && [ -s "API.txt" ]; then
    # 已有配置 → 写入/更新 LANGUAGE
    if grep -q "^LANGUAGE=" API.txt 2>/dev/null; then
        # 语言选择不同则替换
        if [ "$lang_choice" == "1" ] && ! grep -q "^LANGUAGE=en-US" API.txt; then
            sed -i 's/^LANGUAGE=.*/LANGUAGE=en-US/' API.txt
        elif [ "$lang_choice" == "2" ] && ! grep -q "^LANGUAGE=zh-CN" API.txt; then
            sed -i 's/^LANGUAGE=.*/LANGUAGE=zh-CN/' API.txt
        fi
    else
        # API.txt 有内容但没有 LANGUAGE
        lang_val="zh-CN"; [ "$lang_choice" == "1" ] && lang_val="en-US"
        echo "LANGUAGE=$lang_val" >> API.txt
    fi
    echo -e "  ${DIM}📄 ${MSG_CFG_EXIST}${RESET}"
    echo -e "  ${DIM}   Re-run: pyclaw setup${RESET}"
else
    echo -e "\n  ${CYAN}🧞 ${MSG_WIZARD}${RESET}"
    "$PYTHON" -m pyclaw.cli setup
fi

echo ""
echo -e "${GREEN}   ╔══════════════════════════════╗"
echo -e "   ║     🦞 PyClaw ${MSG_READY}      ║"
echo -e "   ╚══════════════════════════════╝${RESET}"
echo ""
echo -e "   ${CYAN}${MSG_START}:${RESET}"
echo -e "     pyclaw start              Interactive mode"
echo -e "     pyclaw start --mode web   Web browser"
echo ""
echo -e "   ${CYAN}${MSG_CMDS}:${RESET}"
echo -e "     pyclaw shell              Interactive chat"
echo -e "     pyclaw setup              Re-run wizard"
echo -e "     pyclaw status             Check status"
echo ""
