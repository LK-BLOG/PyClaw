---
name: desktop-path
description: Detect the correct Linux desktop path (Chinese 桌面 vs English Desktop)
---

## RULE: Always call get_desktop_path before desktop file operations

When the user asks about their "desktop" or "桌面" files, you **MUST**:

1. **Always** call `get_desktop_path()` first — do NOT guess or assume the path
2. Use the returned path for all file listing/reading

The actual path is **either** `~/桌面` or `~/Desktop`, depending on the system language setting. You cannot know which without calling the tool.

## Correct sequence

```
get_desktop_path()       → returns "~/桌面" or "~/Desktop"
ls <returned-path>       → list files
```

## WARNING

Do NOT skip step 1. On this system, `~/Desktop` likely does NOT exist as a real directory. The real desktop is probably `~/桌面`.

## Example

User: "桌面上有什么"
Assistant: (calls get_desktop_path → gets "~/桌面" → calls ls ~/桌面 → returns actual files)
