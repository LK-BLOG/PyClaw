#!/usr/bin/env bash
# 🦞 PyClaw CLI wrapper — 无需 pip install
cd "$(dirname "$0")"
exec python3 -m pyclaw.cli "$@"
