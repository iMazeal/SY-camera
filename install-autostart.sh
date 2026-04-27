#!/bin/bash
# Install camera app autostart for current user
# Usage: ./install-autostart.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"

mkdir -p "$AUTOSTART_DIR"

# Generate desktop file with correct paths
sed "s|@PROJECT_DIR@|$SCRIPT_DIR|g" "$SCRIPT_DIR/camera.desktop" > "$AUTOSTART_DIR/camera.desktop"

chmod +x "$AUTOSTART_DIR/camera.desktop"
echo "Autostart installed to $AUTOSTART_DIR/camera.desktop"
echo "Reboot or run: $SCRIPT_DIR/start.sh"
