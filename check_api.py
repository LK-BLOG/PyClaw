#!/usr/bin/env python3
import bilibili_api
print("bilibili-api version:", bilibili_api.__version__)
import inspect
from bilibili_api import dynamic
print("\nAvailable functions in dynamic:")
for name, obj in inspect.getmembers(dynamic):
    if inspect.isfunction(obj):
        print(f"  - {name}")
        sig = inspect.signature(obj)
        print(f"    {sig}")
