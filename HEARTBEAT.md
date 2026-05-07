# HEARTBEAT.md - 心跳检查任务

## 隧道监控检查

检查 /home/claw/.openclaw/workspace/logs/tunnel-restore-notify.txt 是否存在：
- 如果存在，读取内容并获取新链接
- 确认B站动态是否已发布
- 在会话中告知用户新链接是什么
- 删除该通知文件

## 频率
每30分钟检查一次，或按默认心跳间隔

