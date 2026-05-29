#!/usr/bin/env bash
cd "$(dirname "$0")"

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        $cmd --version 2>&1 | grep -q "3\." && { PYTHON="$cmd"; break; }
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python not found"
    exit 1
fi

echo "🦞 Starting PyClaw..."
echo "   http://localhost:2469"
echo ""

"$PYTHON" webapp.py &

sleep 2
xdg-open "http://localhost:2469" 2>/dev/null || sensible-browser "http://localhost:2469" 2>/dev/null || true

wait
