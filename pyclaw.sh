#!/usr/bin/env bash
# 🦞 PyClaw CLI wrapper — 无需 pip install
# 使用 readlink 解析 symlink，确保从脚本真实目录运行
cd "$(dirname "$(readlink -f "$0")")"
exec python3 -m pyclaw.cli "$@"
