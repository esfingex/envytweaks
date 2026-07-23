# PROJECT CONTEXT PRIMER — ENVYTWEAKS

## Identity
- **Project**: EnvyTweaks
- **Domain**: Linux GPU Mode Switching (NVIDIA Optimus: Integrated, Hybrid, Nvidia) for GNOME & KDE
- **Entry Points**: `envytweaks-cli/src/envytweaks/cli.py`, `envytweaks-gnome/extension.js`, `diagnose.py`

## Architecture Map (Mental Model)
- `envytweaks-cli/` → Núcleo Python 3.10+ PEP 517 para cambio de modos GPU, udev rules, modprobe y RTD3.
- `envytweaks-gnome/` → Extensión de GNOME Shell 43-50+ para integración en Quick Settings.
- `envytweaks-kde/` → Widget Plasmoid para KDE Plasma 6.
- `diagnose.py` → Script de auditoría de hardware y estado del sistema.

## Conventions & Gotchas (Tribal Knowledge)
- **Privilegios**: Los cambios de modo GPU modifican archivos de sistema (`/etc/modprobe.d/`, `/etc/udev/rules.d/`) por lo que requieren ejecución con `sudo` o `pkexec`.
- **Reinicio de Sesión**: La conmutación de GPU requiere reiniciar el servidor de pantalla (X11 / Wayland) o la sesión para surtir efecto.

## Current Task
> **Goal**: Mantener la documentación técnica de la suite y habilitar ingesta de contexto para asistentes IA.
