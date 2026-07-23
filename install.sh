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
    sudo cp ./envytweaks-cli/com.envytweaks.policy /usr/share/polkit-1/actions/
else
    pip install --upgrade --break-system-packages ./envytweaks-cli
    cp ./envytweaks-cli/com.envytweaks.policy /usr/share/polkit-1/actions/
fi
echo "[+] Polkit policy installed to /usr/share/polkit-1/actions/com.envytweaks.policy"

# Helper for non-root commands if run under sudo
run_as_real_user() {
    if [ "$EUID" -eq 0 ] && [ -n "${SUDO_USER:-}" ]; then
        sudo -u "$REAL_USER" "$@"
    else
        "$@"
    fi
}

# 2. Install GNOME Extension
GNOME_INSTALLED=false
if command -v gnome-shell >/dev/null 2>&1; then
    EXTENSION_DIR="$REAL_HOME/.local/share/gnome-shell/extensions/envytweaks@cachyos.org"
    echo "GNOME Shell detected. Installing envytweaks-gnome to $EXTENSION_DIR..."
    
    # Clean old directory as real user
    run_as_real_user rm -rf "$EXTENSION_DIR"
    run_as_real_user mkdir -p "$EXTENSION_DIR"
    
    # Copy extension files as real user
    run_as_real_user cp -r envytweaks-gnome/* "$EXTENSION_DIR/"
    
    # Compile schemas
    echo "Compiling GSettings schemas..."
    glib-compile-schemas "$EXTENSION_DIR/schemas/"
    run_as_real_user chown -R "$REAL_USER:$REAL_USER" "$EXTENSION_DIR" 2>/dev/null || true
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
        run_as_real_user rm -rf "$KDE_DIR"
        run_as_real_user mkdir -p "$KDE_DIR"
        run_as_real_user cp -r envytweaks-kde/* "$KDE_DIR/"
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
