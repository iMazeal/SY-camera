#!/bin/bash
# camera start script — run this to launch the camera app
# Usage: ./start.sh          (with display)
#        ./start.sh offscreen (headless test)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

export PYTHONPATH="$SCRIPT_DIR"
export DISPLAY="${DISPLAY:-:0}"

if [ "$1" = "offscreen" ]; then
    export QT_QPA_PLATFORM=offscreen
fi

exec python src/main.py
