#!/usr/bin/env bash
# 🦞 PyClaw One-Click Install (Linux / macOS)
# Usage:
#   Local:   ./install.sh
#   Remote:  curl -fsSL https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.sh | bash

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

# ── Detect Python ──
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
    echo -e "  ${RED}❌ Python 3.8+ required. Install it:${RESET}"
    echo "     apt install python3 python3-pip  (Debian/Ubuntu)"
    echo "     brew install python3             (macOS)"
    echo "     https://www.python.org/downloads/ (manual)"
    exit 1
fi

# ── Detect Git ──
if ! command -v git &>/dev/null; then
    echo -e "  ${YELLOW}⚠️  git not found, will use curl to download${RESET}"
fi

# ── Determine project directory ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Running via remote pipe → download first
if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == "$HOME" && "$0" == "bash" ]]; then
    echo -e "  ${DIM}📦 Downloading PyClaw...${RESET}"
    if command -v git &>/dev/null; then
        git clone --depth 1 https://github.com/LK-BLOG/PyClaw.git /tmp/pyclaw-install 2>/dev/null || true
        if [ -d /tmp/pyclaw-install ]; then
            PROJECT_DIR="/tmp/pyclaw-install"
        fi
    fi

    # Fallback to curl
    if [ ! -d "$PROJECT_DIR/pyclaw" ]; then
        curl -fsSL https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main -o /tmp/pyclaw.tar.gz
        mkdir -p /tmp/pyclaw-install
        tar -xzf /tmp/pyclaw.tar.gz -C /tmp/pyclaw-install --strip-components=1
        PROJECT_DIR="/tmp/pyclaw-install"
    fi
    cd "$PROJECT_DIR"
    echo -e "  ${GREEN}✅ Download complete${RESET}"
fi

# ── Ask: install CLI? ──
printf "\n  ${CYAN}🔧 Install pyclaw CLI?${RESET}\n"
printf "     Installed: run 'pyclaw <command>' anywhere\n"
printf "     Skipped:  use 'python -m pyclaw.cli <command>' instead\n"
printf "\n  ${CYAN}Install CLI? (Y/n): ${RESET}"
read install_cli < /dev/tty 2>/dev/null || read install_cli
install_cli=${install_cli:-y}

if [[ "$install_cli" == "y" ]] || [[ "$install_cli" == "Y" ]] || [[ "$install_cli" == "" ]]; then

# ── Install pyclaw CLI ──
echo -e "  ${DIM}🔧 Installing pyclaw command...${RESET}"
if pip install --break-system-packages -e "$PROJECT_DIR" 2>/dev/null; then
    echo -e "  ${GREEN}✅ pyclaw command installed (pip)${RESET}"
elif pip install --user -e "$PROJECT_DIR" 2>/dev/null; then
    echo -e "  ${GREEN}✅ pyclaw command installed (user)${RESET}"
else
    # Fallback: symlink
    mkdir -p ~/.local/bin
    ln -sf "$PROJECT_DIR/pyclaw.sh" ~/.local/bin/pyclaw
    echo -e "  ${GREEN}✅ pyclaw command installed (symlink)${RESET}"
    echo -e "  ${DIM}    Make sure ~/.local/bin is in your PATH${RESET}"
fi

else
    echo -e "  ${YELLOW}⏭️  Skipped CLI install${RESET}"
fi

# ── Install dependencies ──
echo -e "  ${DIM}📦 Installing Python dependencies...${RESET}"
"$PYTHON" -m pip install --break-system-packages httpx uvicorn fastapi websockets 2>/dev/null || \
"$PYTHON" -m pip install --user httpx uvicorn fastapi websockets 2>/dev/null || true

# ── Configuration wizard ──
echo ""
echo -e "  ${CYAN}🧞 Launching setup wizard...${RESET}"
cd "$PROJECT_DIR"
if [ -f "API.txt" ] && [ -s "API.txt" ]; then
    echo -e "  ${DIM}   Config already exists, skipping${RESET}"
    echo -e "  ${DIM}   Re-run: pyclaw setup${RESET}"
else
    "$PYTHON" -m pyclaw.cli setup
fi

# ── Done ──
echo ""
echo -e "${GREEN}   ╔══════════════════════════════╗"
echo -e "   ║     🦞 PyClaw Ready!        ║"
echo -e "   ╚══════════════════════════════╝${RESET}"
echo ""
echo -e "   ${CYAN}Start:${RESET}"
echo -e "     pyclaw start              Interactive mode"
echo -e "     pyclaw start --mode web   Web browser mode"
echo ""
echo -e "   ${CYAN}Commands:${RESET}"
echo -e "     pyclaw shell              Interactive chat"
echo -e "     pyclaw setup              Re-run wizard"
echo -e "     pyclaw status             Check status"
echo ""
