#!/usr/bin/env python3
cookie_file = "/home/claw/.openclaw/workspace/skills/bilibili-skill/Cookie.txt"
with open(cookie_file, 'r') as f:
    cookie_str = f.read().strip()
print(f"Cookie content: {repr(cookie_str)}")
print()

cookies = {}
for part in cookie_str.split(';'):
    if '=' in part:
        key, value = part.split('=', 1)
        key = key.strip()
        value = value.strip()
        cookies[key] = value
        print(f"{key}: {repr(value)}")

print()
print(f"SESSDATA found: {'SESSDATA' in cookies} -> {cookies.get('SESSDATA')}")
print(f"bili_jct found: {'bili_jct' in cookies} -> {cookies.get('bili_jct')}")
