#!/bin/bash
# Install camera app: desktop icon + autostart
# Usage: ./install-autostart.sh [--no-autostart]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$HOME/Desktop/camera.desktop"

generate_desktop() {
    sed "s|@PROJECT_DIR@|$SCRIPT_DIR|g" "$SCRIPT_DIR/camera.desktop"
}

echo "Installing desktop icon..."
mkdir -p "$HOME/Desktop"
generate_desktop > "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
# Mark as trusted so double-click works without extra confirmation
gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
echo "  → $DESKTOP_FILE"

if [ "$1" != "--no-autostart" ]; then
    echo "Installing autostart..."
    mkdir -p "$AUTOSTART_DIR"
    generate_desktop > "$AUTOSTART_DIR/camera.desktop"
    chmod +x "$AUTOSTART_DIR/camera.desktop"
    echo "  → $AUTOSTART_DIR/camera.desktop"
fi

echo ""
echo "Done! Double-click the icon on Desktop to launch."
echo "Or run: $SCRIPT_DIR/start.sh"
