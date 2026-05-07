#!/bin/bash
pkill -f "uvicorn server_multisession:app" 2>/dev/null
rm -rf logs/*.log pyclaw/__pycache__ 2>/dev/null
echo "已清理进程和临时文件"