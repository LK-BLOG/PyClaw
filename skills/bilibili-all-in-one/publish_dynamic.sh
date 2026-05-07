#!/bin/bash
# Publish dynamic with credentials from TOOLS.md

# Extract credentials from environment (assuming they are set from TOOLS.md)
export BILIBILI_SESSDATA="${BILIBILI_SESSDATA}"
export BILIBILI_BILI_JCT="${BILIBILI_BILI_JCT}"
export BILIBILI_BUVID3="${BILIBILI_BUVID3}"

# Run the Python script
python3 publish_dynamic.py
