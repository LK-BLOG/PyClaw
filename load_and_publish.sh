#!/bin/bash
# Load environment and publish dynamic

# Load bashrc
source ~/.bashrc

# Print debug info
echo "Checking credentials:"
echo "BILIBILI_SESSDATA length: ${#BILIBILI_SESSDATA}"
echo "BILIBILI_BILI_JCT length: ${#BILIBILI_BILI_JCT}"

# Execute python
python3 /home/claw/.openclaw/workspace/publish_dynamic.py
