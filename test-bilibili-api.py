#!/usr/bin/env python3
import bilibili_api
import bilibili_api.dynamic
print(dir(bilibili_api.dynamic))
print("\nTypes:")
for item in dir(bilibili_api.dynamic):
    if not item.startswith('_'):
        print(f"  - {item}")
