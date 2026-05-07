#!/bin/bash
pkill -9 -f cloudflared 2>/dev/null
rm -f /tmp/cloudflared.log
cloudflared tunnel --url http://localhost:80 > /tmp/cloudflared.log 2>&1 &
echo $! > /tmp/cloudflared.pid
sleep 8
cat /tmp/cloudflared.log | grep -E "https://.*trycloudflare.com|INF" | head -10
