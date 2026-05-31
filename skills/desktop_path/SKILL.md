---
name: desktop-path
description: Detect the correct Linux desktop path (Chinese 桌面 vs English Desktop)
---

## Instructions

When the user asks about their "desktop" or "桌面" files:

1. **First** call `get_desktop_path` to detect the actual desktop path
2. **Then** use the returned path to list/read files

The desktop path might be `~/Desktop` or `~/桌面` depending on system language.
Do NOT assume it's `~/Desktop` — always check first.

## Example

User: 看看桌面上有什么
Steps:
1. `get_desktop_path()` → returns e.g. `~/桌面`
2. `ls ~/桌面` → list the files
