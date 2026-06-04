# EnvyTweaks

EnvyTweaks is a modernized GPU mode switching suite for NVIDIA Optimus laptops on Linux. It includes:

1. **[envytweaks-cli](file:///home/esfingex/workspace/envytweaks/envytweaks-cli)**: A modernized, PEP 517-compliant CLI utility ported from EnvyControl, featuring modern Python syntax, strict static typing, and robust caching.
2. **[envytweaks-gnome](file:///home/esfingex/workspace/envytweaks/envytweaks-gnome)**: A modernized GNOME Shell extension (supporting GNOME 43 to 50) ported from GPU Profile Selector, featuring full Quick Settings and Top Bar integration, dynamic RTD3 settings, and graceful fallback when the CLI tool is not installed.

## Project Structure

- `envytweaks-cli/`: Python packaging structure (`pyproject.toml`, `src/envytweaks/`).
- `envytweaks-gnome/`: GNOME Shell extension package (`extension.js`, `metadata.json`, etc.).

## License

This project is licensed under the MIT License and GNU General Public License v3.0.
