#!/usr/bin/env bash
set -e

echo "📦 Compilando y empaquetando EnvyTweaks GPU Switcher v2..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Compilar esquemas GSettings localmente
if command -v glib-compile-schemas >/dev/null 2>&1; then
    echo "[*] Compilando esquemas GSettings localmente..."
    glib-compile-schemas schemas/
fi

# 2. Empaquetar Extensión de GNOME Shell (.zip) para extensions.gnome.org (excluyendo gschemas.compiled según guías GNOME 45+)
echo "[*] Creando paquete zip para extensions.gnome.org..."
zip -FS -r envytweaks@cachyos.org.shell-extension.zip metadata.json extension.js prefs.js img/ lib/ locale/ schemas/ ui/ -x "*.zip" -x "schemas/gschemas.compiled"

echo "✅ ¡Empaquetado exitoso!"
echo "   - Extensión Zip: envytweaks-gnome/envytweaks@cachyos.org.shell-extension.zip"
