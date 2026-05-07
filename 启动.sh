#!/bin/bash
cd "$(dirname "$0")"
# 检查端口是否被占用
if lsof -i:8000 > /dev/null 2>&1; then
 echo "端口8000已被占用，请先运行清理脚本"
 exit 1
fi
uvicorn server_multisession:app --host 0.0.0.0 --port 8000 --reload