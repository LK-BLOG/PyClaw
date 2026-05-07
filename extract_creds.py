#!/usr/bin/env python3
import re

with open('/home/claw/.openclaw/workspace/TOOLS.md', 'r') as f:
    content = f.read()

# Extract credentials
patterns = {
    'SESSDATA': r'- SESSDATA:\s*(.*)$',
    'BILI_JCT': r'- bili_jct:\s*(.*)$', 
    'BUVID3': r'- buvid3:\s*(.*)$'
}

creds = {}
for name, pattern in patterns.items():
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        creds[name] = match.group(1).strip()
        print(f"{name}: {creds[name][:8]}... (length {len(creds[name])})")
    else:
        print(f"{name}: NOT FOUND")

# Write to a file that can be sourced
with open('/tmp/bilibili_creds.sh', 'w') as f:
    for name, value in creds.items():
        if value:
            f.write(f'export {name}=\"{value}\"\n')

print("\nCreated /tmp/bilibili_creds.sh")
