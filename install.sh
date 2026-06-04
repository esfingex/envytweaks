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
GNOME_INSTALLED=false
if command -v gnome-shell >/dev/null 2>&1; then
    EXTENSION_DIR="$REAL_HOME/.local/share/gnome-shell/extensions/envytweaks@cachyos.org"
    echo "GNOME Shell detected. Installing envytweaks-gnome to $EXTENSION_DIR..."
    
    # Clean old directory
    rm -rf "$EXTENSION_DIR"
    mkdir -p "$EXTENSION_DIR"
    
    # Copy extension files
    cp -r envytweaks-gnome/* "$EXTENSION_DIR/"
    
    # Compile schemas
    echo "Compiling GSettings schemas..."
    glib-compile-schemas "$EXTENSION_DIR/schemas/"
    
    # Set correct ownership for GNOME extension files if run under sudo
    if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$REAL_USER:$REAL_USER" "$EXTENSION_DIR"
    fi
    GNOME_INSTALLED=true
else
    echo "GNOME Shell not detected. Skipping GNOME Extension installation."
fi

# 3. Install KDE Plasma Widget
KDE_INSTALLED=false
if [ -d "envytweaks-kde" ]; then
    if command -v plasmashell >/dev/null 2>&1; then
        KDE_DIR="$REAL_HOME/.local/share/plasma/plasmoids/optimus-gpu-switcher"
        echo "KDE Plasma detected. Installing envytweaks-kde to $KDE_DIR..."
        rm -rf "$KDE_DIR"
        mkdir -p "$KDE_DIR"
        cp -r envytweaks-kde/* "$KDE_DIR/"
        if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
            chown -R "$REAL_USER:$REAL_USER" "$KDE_DIR"
        fi
        KDE_INSTALLED=true
    else
        echo "KDE Plasma (plasmashell) not detected. Skipping KDE Plasma Widget installation."
    fi
fi

echo "=== Installation complete! ==="
if [ "$GNOME_INSTALLED" = true ]; then
    echo "Please reload GNOME Shell (or log out and log in again) to enable the GNOME extension:"
    echo "  gnome-extensions enable envytweaks@cachyos.org"
fi
if [ "$KDE_INSTALLED" = true ]; then
    echo "For KDE Plasma, the widget 'Optimus GPU Switcher' has been added to your local plasmoids list."
fi
