# TOOLS.md - Local Notes

## Cloudflare Tunnel

- **当前隧道**: https://strategies-apparatus-appreciate-limit.trycloudflare.com
- **本地端口**: 80
- **状态**: ✅ 隧道已重新连接 (2026-04-29 21:18 重连)
- **进程**: cloudflared tunnel --url http://localhost:80
- **PID**: 788587 (2026-04-29 21:18 重连)

## Bilibili Authentication

- **状态**: ❌ Cookie已过期 (code=-101, 账号未登录) (2026-04-29 20:22 验证)
- **最后成功发布**: 2026-04-27 18:52
- **Cookie文件**: `~/.openclaw/workspace/skills/bilibili-skill/Cookie.txt`
- **解决方法**: 需要重新扫码登录B站获取新Cookie
  - 运行 `cd ~/.openclaw/workspace/skills/bilibili-skill && bash run_qr_login.sh`
  - 或直接 `python3 ~/.openclaw/workspace/skills/bilibili-skill/qr_login.py`

## Automatic Monitoring

- **监控脚本**: `~/.openclaw/workspace/scripts/tunnel-monitor.sh`
- **Cron任务**: `*/5 * * * *` 每5分钟检查一次
- 自动检测 tunnel 断开 → 重启 → 发布B站动态

## Skills

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.
