# EnvyTweaks

[![Get it on GNOME Extensions](https://img.shields.io/badge/Get%20it%20on-GNOME%20Extensions-4a86e8?style=for-the-badge&logo=gnome&logoColor=white)](https://extensions.gnome.org/extension/envytweaks@cachyos.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](LICENSE)

EnvyTweaks is a modernized GPU mode switching suite for NVIDIA Optimus laptops on Linux. It includes:

1. **[envytweaks-cli](envytweaks-cli)**: A modernized, PEP 517-compliant CLI utility ported from EnvyControl, featuring modern Python syntax, strict static typing, and robust caching.
2. **[envytweaks-gnome](envytweaks-gnome)**: A modernized GNOME Shell extension (supporting GNOME 43 to 50) ported from GPU Profile Selector, featuring full Quick Settings and Top Bar integration, dynamic RTD3 settings, and graceful fallback when the CLI tool is not installed.
3. **[envytweaks-kde](envytweaks-kde)**: A modernized KDE Plasma 6 widget ported from Optimus GPU Switcher, allowing seamless GPU switching directly from the system tray under KDE Plasma.


## Installation & Setup

We provide a convenient installation script that will install the CLI system-wide (necessary for root actions via pkexec) and copy the GNOME extension to your user extension directory.

### Quick Install

Simply run the installer script from the root of the repository:

```bash
./install.sh
```

*(Note: The script will ask for sudo authorization to install the CLI command system-wide).*

### Manual Installation

If you prefer to install the components manually:

#### 1. CLI installation
```bash
sudo pip install --break-system-packages ./envytweaks-cli
```

#### 2. GNOME Extension installation
```bash
# Copy files
mkdir -p ~/.local/share/gnome-shell/extensions/envytweaks@cachyos.org
cp -r envytweaks-gnome/* ~/.local/share/gnome-shell/extensions/envytweaks@cachyos.org/

# Compile schemas
glib-compile-schemas ~/.local/share/gnome-shell/extensions/envytweaks@cachyos.org/schemas/
```

After installing, please reload GNOME Shell (or log out and log in again) and enable the extension:
```bash
gnome-extensions enable envytweaks@cachyos.org
```

---

## Project Structure
 
 - `envytweaks-cli/`: Python packaging structure (`pyproject.toml`, `src/envytweaks/`).
 - `envytweaks-gnome/`: GNOME Shell extension package (`extension.js`, `metadata.json`, etc.).
 - `envytweaks-kde/`: KDE Plasma 6 widget package (`metadata.json`, `contents/`, etc.).
 - `install.sh`: Setup script.
 
 ## Credits & Acknowledgements
 
 EnvyTweaks is based on and inspired by the following excellent projects:
 - **[EnvyControl](https://github.com/bayasdev/envycontrol)** by [bayasdev](https://github.com/bayasdev) - The core Python command-line utility for GPU switching.
 - **[GPU Profile Selector](https://github.com/LorenzoMorelli/GPU_profile_selector)** by [Lorenzo Morelli](https://github.com/LorenzoMorelli) - The GNOME Shell extension providing the graphical menu integration.
 - **[Optimus GPU Switcher](https://github.com/enielrodriguez/optimus-gpu-switcher)** by [Eniel](https://github.com/enielrodriguez) - The KDE Plasma 6 widget providing the system tray integration.
 
 Thank you to the original authors and contributors for their outstanding work.


## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).
