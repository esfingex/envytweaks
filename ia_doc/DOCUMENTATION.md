# 🟢 Documentación Técnica del Proyecto: EnvyTweaks

## 1. Visión General

**EnvyTweaks** es una suite completa de gestión y conmutación de perfiles GPU (NVIDIA Optimus: *Integrated*, *Hybrid*, *Nvidia*) para laptops Linux en sistemas con tarjetas gráficas dedicadas NVIDIA.

Ofrece tres capas de interacción principal:
1. **`envytweaks-cli`**: Herramienta de línea de comandos en Python 3.10+ (PEP 517) derivada de EnvyControl con sintaxis estricta, caché rápido y gestión de energía RTD3.
2. **`envytweaks-gnome`**: Extensión de GNOME Shell (soporta GNOME 43 a 50+) integrada en Quick Settings y la barra superior.
3. **`envytweaks-kde`**: Widget nativo para la bandeja del sistema en **KDE Plasma 6**.

---

## 2. Arquitectura del Proyecto

```
                     +---------------------------------------+
                     |           EnvyTweaks Suite            |
                     +-------------------+-------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
+-----------------------+     +-----------------------+     +-----------------------+
|   envytweaks-gnome    |     |    envytweaks-cli     |     |     envytweaks-kde    |
| (GNOME Shell Ext)     |     | (Python 3.10+ Core)   |     | (KDE Plasma 6 Widget) |
+-----------+-----------+     +-----------+-----------+     +-----------+-----------+
            |                             |                             |
            +-----------------------------+-----------------------------+
                                          | (Ejecución privilegiada vía pkexec)
                                          v
                              +-----------------------+
                              | Configuración Kernel  |
                              | - Modprobe / Udev     |
                              | - Reglas de Energía   |
                              | - Reconstrucción initramfs |
                              +-----------------------+
```

---

## 3. Estructura de Módulos y Archivos

* [README.md](file:///home/esfingex/workspace/envytweaks/README.md): Instrucciones generales e información de créditos.
* [install.sh](file:///home/esfingex/workspace/envytweaks/install.sh): Script de instalación unificado para CLI y extensión GNOME.
* [diagnose.py](file:///home/esfingex/workspace/envytweaks/diagnose.py): Script de auditoría de hardware y estado de drivers GPU.
* **Componente CLI ([envytweaks-cli/](file:///home/esfingex/workspace/envytweaks/envytweaks-cli)):**
  * `cli.py`: Interfaz de entrada CLI y opciones (`envytweaks --switch <mode>`).
  * `switcher.py`: Lógica de conmutación de controladores y generación de archivos modprobe/udev.
  * `system.py`: Detección de distribución, gestor de paquetes e inspección del kernel.
  * `cache.py`: Sistema de almacenamiento en caché para respuestas ultrarrápidas.
  * `config.py`: Manejo de configuraciones y perfiles.
* **Componente GNOME ([envytweaks-gnome/](file:///home/esfingex/workspace/envytweaks/envytweaks-gnome)):**
  * `extension.js`: Extensión Quick Settings para GNOME Shell.
* **Componente KDE ([envytweaks-kde/](file:///home/esfingex/workspace/envytweaks/envytweaks-kde)):**
  * Widget Plasmoid para KDE Plasma 6.

---

## 4. Comandos Principales

```bash
# Ver el modo GPU actual
envytweaks --query

# Cambiar a modo Integrado (ahorro de batería)
sudo envytweaks --switch integrated

# Cambiar a modo Híbrido (RTD3 habilitado)
sudo envytweaks --switch hybrid

# Cambiar a modo Rendimiento NVIDIA
sudo envytweaks --switch nvidia

# Ejecutar diagnóstico de hardware GPU
python3 diagnose.py
```
