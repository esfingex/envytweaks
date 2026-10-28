# EnvyTweaks GPU Switcher — GNOME Shell Extension

A GNOME Shell extension for switching GPU modes on NVIDIA Optimus laptops.
It is the graphical frontend for the [envytweaks CLI](../envytweaks-cli) and
supports both Quick Settings and a classic top-bar menu.

## Requirements

- GNOME Shell 45 or newer (the extension uses ESM and the GNOME 45 extension API)
- [envytweaks](../envytweaks-cli) installed and available in `PATH`
- `pkexec` for privileged mode switching

The extension resolves the `envytweaks` binary at runtime with
`GLib.find_program_in_path()`, so installs in `/usr/local/bin` work too.

## Installation

### GNOME Extensions

Install it from [extensions.gnome.org](https://extensions.gnome.org/extension/10456/envytweaks-gpu-switcher/)
after installing the CLI.

### Manual

```bash
cd envytweaks-gnome
./build.sh
gnome-extensions install --force envytweaks@cachyos.org.shell-extension.zip
glib-compile-schemas ~/.local/share/gnome-shell/extensions/envytweaks@cachyos.org/schemas
gnome-extensions enable envytweaks@cachyos.org
```

Log out and back in if GNOME Shell does not pick up the new extension
immediately.

## Translation

Spanish strings live in [`../po/es.po`](../po/es.po). `build.sh` compiles them
into `locale/es/LC_MESSAGES/envytweaks.mo` when `msgfmt` is available.

## Debugging

```bash
journalctl -f -o cat /usr/bin/gnome-shell
```

To show extension log messages:

```bash
export G_MESSAGES_DEBUG=all
```
