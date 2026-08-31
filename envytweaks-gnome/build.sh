#!/usr/bin/env bash
set -e

echo "📦 Compilando y empaquetando EnvyTweaks GPU Switcher..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Eliminar gschemas.compiled previo si existe
rm -f schemas/gschemas.compiled

# 2. Empaquetar Extensión de GNOME Shell (.zip) limpia para extensions.gnome.org
echo "[*] Creando paquete zip limpio para extensions.gnome.org..."
rm -f envytweaks@cachyos.org.shell-extension.zip

zip -r envytweaks@cachyos.org.shell-extension.zip \
    metadata.json \
    extension.js \
    prefs.js \
    img/ \
    lib/ \
    locale/ \
    schemas/ \
    ui/ \
    -x "schemas/gschemas.compiled" \
    -x "build.sh" \
    -x "*.zip"

echo "✅ ¡Empaquetado limpio exitoso!"
echo "   - Extensión Zip: envytweaks-gnome/envytweaks@cachyos.org.shell-extension.zip"
