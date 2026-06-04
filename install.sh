#!/usr/bin/env bash
set -e

# Determine the actual non-root user if run with sudo
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "=== EnvyTweaks Installer ==="

# 1. Install CLI
echo "Installing envytweaks-cli system-wide..."
if [ "$EUID" -ne 0 ]; then
    echo "CLI installation requires sudo. Asking for password..."
    sudo pip install --upgrade --break-system-packages ./envytweaks-cli
else
    pip install --upgrade --break-system-packages ./envytweaks-cli
fi

# 2. Install GNOME Extension
EXTENSION_DIR="$REAL_HOME/.local/share/gnome-shell/extensions/envytweaks@cachyos.org"
echo "Installing envytweaks-gnome to $EXTENSION_DIR..."

# Clean old directory
rm -rf "$EXTENSION_DIR"
mkdir -p "$EXTENSION_DIR"

# Copy extension files
cp -r envytweaks-gnome/* "$EXTENSION_DIR/"

# Compile schemas
echo "Compiling GSettings schemas..."
glib-compile-schemas "$EXTENSION_DIR/schemas/"

# Set correct ownership for extension files if run under sudo
if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
    chown -R "$REAL_USER:$REAL_USER" "$EXTENSION_DIR"
fi

echo "=== Installation complete! ==="
echo "Please reload GNOME Shell (or log out and log in again) to enable the extension."
echo "You can enable it using:"
echo "  gnome-extensions enable envytweaks@cachyos.org"
