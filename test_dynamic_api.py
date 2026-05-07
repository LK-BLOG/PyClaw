#!/usr/bin/env python3
import asyncio
import inspect
import bilibili_api.dynamic
from bilibili_api import Credential

print("Available functions in bilibili_api.dynamic:")
for name, obj in inspect.getmembers(bilibili_api.dynamic):
    if inspect.isfunction(obj) and not name.startswith('_'):
        print(f"  - {name}")
        sig = inspect.signature(obj)
        print(f"    {sig}")

print("\nClasses:")
for name, obj in inspect.getmembers(bilibili_api.dynamic):
    if inspect.isclass(obj) and not name.startswith('_'):
        print(f"  - {name}")
