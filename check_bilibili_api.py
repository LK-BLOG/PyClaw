#!/usr/bin/env python3
import bilibili_api
print(f"Bilibili-api-python version: {bilibili_api.__version__}")

# Check dynamic module contents
import bilibili_api.dynamic
print("\nDynamic module exports:")
print([item for item in dir(bilibili_api.dynamic) if not item.startswith('_')])
