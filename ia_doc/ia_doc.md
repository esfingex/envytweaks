# CONTEXT PRIMER
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


---

## File: .github/workflows/ci.yml
```yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest

      - name: Lint with Ruff
        run: |
          # run ruff on the cli directory
          ruff check envytweaks-cli/

      - name: Syntax compile check
        run: |
          python -m py_compile envytweaks-cli/src/envytweaks/*.py

      - name: Install package dry-run
        run: |
          cd envytweaks-cli
          pip install --dry-run .

```

## File: .planning/PROJECT.md
```md
# PROJECT.md — envytweaks

## Vision & Scope

envytweaks is a monorepo that modernizes and maintains two abandoned projects:
- envycontrol (Python CLI for NVIDIA Optimus GPU mode switching)
- GPU_profile_selector (GNOME Shell extension, GUI frontend for envycontrol)

The goal is NOT a from-scratch rewrite — it is a port+modernization. The original logic is preserved
and cleaned up: pathlib.Path, match/case, type hints, bug fixes, and missing features added.

envytweaks is a sub-tool that will be published independently on GitHub and then integrated
as a component inside cachy-tweaks (the renamed version of cachy-gnome-tweaks, which now
also covers KDE and is no longer GNOME-exclusive).

Development workflow:
  1. Code and iterate locally at /home/esfingex/workspace/envytweaks
  2. Test on this machine (CachyOS + GNOME 50)
  3. Create GitHub repo and push
  4. Integrate into cachy-tweaks as a sub-tool

Target users: Linux laptop users with hybrid Intel+NVIDIA or AMD+NVIDIA GPU setups (Optimus).
Target distros: Arch/CachyOS, Debian/Ubuntu, RHEL/Fedora, NixOS, OSTree-based distros (Bazzite, Kinoite).
Target GNOME: 43 through 50+.

---

## Architecture & Components

### Component 1: envytweaks-cli (Python 3.10+)

Rewrite of envycontrol as a modern Python package.

Key differences from envycontrol:
- Fully pathlib.Path based (zero os.path usage)
- match/case for mode switching and distro detection
- Type hints on all public functions
- Proper package structure (src layout)
- pyproject.toml packaging (PEP 517/518)
- Bug fix: get_amd_igpu_name() UnboundLocalError
- Extracted _run_subprocess() helper replacing 5 duplicate verbose blocks
- Distro detection refactored to match/case

```
envytweaks-cli/
├── pyproject.toml
├── src/
│   └── envytweaks/
│       ├── __init__.py
│       ├── cli.py          # argparse entry point
│       ├── switcher.py     # graphics_mode_switcher() and mode logic
│       ├── system.py       # GPU/iGPU/DM detection, initramfs rebuild
│       ├── config.py       # File creation, cleanup, path constants
│       └── cache.py        # CachedConfig class
└── tests/
    ├── test_switcher.py
    ├── test_system.py
    └── test_config.py
```

### Component 2: envytweaks-gnome (GNOME Shell Extension, GJS/ESM)

Rewrite of GPU_profile_selector as a cleaner GNOME extension.

Key differences from GPU_profile_selector:
- pkexec exit code handling: 126=cancelled, 127=not installed, 0=success
- envycontrol/envytweaks-cli detection (NOT_INSTALLED state)
- RTD3 mode configurable (0/1/2/3) via GSettings integer key
- Feature parity between QuickSettingsView and TopBarView
- Re-query state on pkexec cancellation (no stale state)
- Disabled menu items when CLI tool not installed

```
envytweaks-gnome/
├── metadata.json
├── extension.js
├── prefs.js
├── lib/
│   └── Utility.js
├── ui/
│   ├── QuickSettingsView.js
│   └── TopBarView.js
├── schemas/
│   └── org.gnome.shell.extensions.envytweaks.gschema.xml
└── img/
    ├── icon.png
    ├── intel_icon_plain.svg
    ├── nvidia_icon_plain.svg
    └── hybrid_icon_plain.svg
```

### Monorepo Root:

```
envytweaks/
├── .planning/               # GSD lifecycle and planning documents
├── .github/workflows/       # CI/CD for both components
├── envytweaks-cli/          # Python CLI component
├── envytweaks-gnome/        # GNOME extension component
├── README.md                # Project overview
└── CONTRIBUTING.md          # Development guide
```

---

## Key Constants & Conventions

### envytweaks-cli:
- CACHE_FILE_PATH = Path('/var/cache/envytweaks/cache.json')
- Config files path pattern: /etc/modprobe.d/, /etc/udev/rules.d/, /etc/X11/
- Supported modes: ['integrated', 'hybrid', 'nvidia']
- Supported DMs: ['gdm', 'gdm3', 'sddm', 'lightdm']
- RTD3 modes: [0, 1, 2, 3]

### envytweaks-gnome:
- CLI invocation: pkexec envytweaks -s <mode> [args]
- Query: GLib.spawn_command_line_sync("envytweaks --query")
- pkexec exit codes: 0=success, 126=cancelled, 127=not_found
- GSchema ID: org.gnome.shell.extensions.envytweaks
- UUID: envytweaks@envytweaks.dev (TBD)

---

## Core Ecosystem Conventions

1. **Rust Token Killer (RTK)**: All terminal commands executed by the agent must be prefixed with `rtk`.
2. **Bilingual Caveman Format (BCF)**: Facts stored in the CaveMem database use: `[EN]` in compressed caveman-style English for agent scanning efficiency, and `[ES]` in natural Spanish for developer reference.
3. **Zero-Pollution Encapsulation**: Maintain global agent rules in `~/.gemini/` or `~/.agents/`. Do not leave local configurations (like `.cursorrules`) inside the repository root.
4. **No Emojis or Icons**: Do not include emojis or visual symbols in planning and roadmap files to conserve context window tokens.
5. **pathlib.Path only**: Never use os.path in the Python component.
6. **Python 3.10+ minimum**: Required for match/case syntax.
7. **Type hints required**: All public functions must have full type annotations.
8. **GJS/ESM only**: The GNOME extension uses native GJS with ES modules — no bundlers, no npm.
9. **Schema recompile**: After any gschema.xml change, run glib-compile-schemas schemas/.

```

## File: .planning/ROADMAP.md
```md
# ROADMAP.md — envytweaks

## Development Roadmap (GSD Phases)

---

## Phase 1.0: Monorepo Scaffolding

Objective: Set up the repository structure for both components before any code is written.

Tasks:
- `[ ]` Initialize git repo and .gitignore.
- `[ ]` Create envytweaks-cli/ directory with pyproject.toml and src/ layout.
- `[ ]` Create envytweaks-gnome/ directory with extension skeleton files.
- `[ ]` Write root README.md with project overview.
- `[ ]` Configure .github/workflows/ with CI stubs.

Status: Pending

---

## Phase 1.1: envytweaks-cli — Core Logic Port

Objective: Port envycontrol logic to modern Python package structure.

Tasks:
- `[ ]` Create src/envytweaks/config.py — path constants (pathlib.Path), file creation, cleanup.
- `[ ]` Create src/envytweaks/system.py — GPU/iGPU/DM detection, rebuild_initramfs() with match/case.
- `[ ]` Create src/envytweaks/cache.py — CachedConfig class.
- `[ ]` Create src/envytweaks/switcher.py — graphics_mode_switcher() with match/case.
- `[ ]` Create src/envytweaks/cli.py — argparse entry point.
- `[ ]` Fix bug: get_amd_igpu_name() xrandr_output UnboundLocalError.
- `[ ]` Implement _run_subprocess() helper to eliminate verbose/debug duplication.
- `[ ]` Add type hints to all functions.

Status: Pending

---

## Phase 1.2: envytweaks-cli — Packaging & CI

Objective: Make the CLI installable and validated by CI.

Tasks:
- `[ ]` Write pyproject.toml with [project], [project.scripts], [build-system].
- `[ ]` Verify pip install --dry-run . works cleanly.
- `[ ]` Write .github/workflows/ci-cli.yml: py_compile, ruff/pylint, import check.

Status: Pending

---

## Phase 2.0: envytweaks-gnome — Extension Skeleton

Objective: Create the base GNOME extension with updated metadata.

Tasks:
- `[ ]` Write metadata.json with new UUID and GNOME 43-50 shell-version support.
- `[ ]` Write GSettings schema (gschema.xml) with all keys including rtd3-mode (integer).
- `[ ]` Compile schema: glib-compile-schemas schemas/.
- `[ ]` Write extension.js entry point (same QuickSettings/TopBar logic as original).
- `[ ]` Copy and migrate icons from GPU_profile_selector.

Status: Pending

---

## Phase 2.1: envytweaks-gnome — Utility.js Rewrite

Objective: Rewrite Utility.js with proper pkexec exit code handling and envytweaks-cli detection.

Tasks:
- `[ ]` Define GPU_PROFILE_NOT_INSTALLED constant.
- `[ ]` In getCurrentProfile(): detect not-installed via exit code, return GPU_PROFILE_NOT_INSTALLED.
- `[ ]` In _execSwitch(): capture exit code and pass it to callback.
- `[ ]` Replace hardcoded RTD3_MODE = 2 with settings.get_int('rtd3-mode').
- `[ ]` Update switchHybrid() to use integer rtd3-mode setting.

Status: Pending

---

## Phase 2.2: envytweaks-gnome — View Updates

Objective: Fix UX bugs and achieve feature parity between QuickSettings and TopBar views.

Tasks:
- `[ ]` QuickSettingsView: handle GPU_PROFILE_NOT_INSTALLED (disable items, warning subtitle).
- `[ ]` QuickSettingsView: re-query on pkexec cancel (exit 126), don't keep stale state.
- `[ ]` QuickSettingsView: distinguish cancel vs error in _onSwitchComplete.
- `[ ]` TopBarView: add restart-pending visual indicator.
- `[ ]` TopBarView: add NOT_INSTALLED handling.

Status: Pending

---

## Phase 2.3: envytweaks-gnome — Preferences

Objective: Add RTD3 mode selector to preferences window.

Tasks:
- `[ ]` Add ComboRow or SpinRow for rtd3-mode (0=disabled, 1=coarse, 2=fine, 3=Ampere+).
- `[ ]` Improve description for force-topbar-view row.
- `[ ]` Bind all settings correctly in prefs.js.

Status: Pending

---

## Phase 3.0: Integration & Release

Objective: Wire both components together and prepare first release.

Tasks:
- `[ ]` Update GNOME extension to call envytweaks CLI (not envycontrol).
- `[ ]` Write unified .github/workflows/release.yml for both components.
- `[ ]` Write CONTRIBUTING.md.
- `[ ]` Tag v1.0.0.

Status: Pending

```

## File: .planning/STATE.md
```md
# STATE.md — envytweaks

## Development State

- **Active Phase**: Phase 1.0 (Monorepo Scaffolding)
- **Current Milestone**: Repository initialization pending.
- **Git Position**: No commits yet — empty directory.

---

## Architectural Decision Records (ADR)

### ADR-001: Monorepo structure (envytweaks-cli + envytweaks-gnome)
- **Date**: 2026-06-04
- **Context**: envycontrol (CLI) and GPU_profile_selector (GNOME extension) are separate repos, both abandoned.
  The goal is to unify them under active maintenance with shared conventions and a single release pipeline.
- **Decision**: Single monorepo with two top-level subdirectories: envytweaks-cli/ and envytweaks-gnome/.
- **Justification**: Simplifies versioning (one tag = one release), shared CI/CD, easier cross-component changes.
  Alternatives considered: two separate repos (rejected: split maintenance burden), single flat structure (rejected: mixing Python and JS).

### ADR-002: Python 3.10+ minimum
- **Date**: 2026-06-04
- **Context**: envycontrol targets Python 3.8+. Modern idioms (match/case) require 3.10+.
- **Decision**: envytweaks-cli targets Python 3.10+ as minimum.
- **Justification**: Python 3.10 released Oct 2021 — all actively maintained distros include it.
  Debian 12 ships 3.11, Ubuntu 22.04 ships 3.10, Arch/CachyOS is always current.
  The match/case syntax significantly improves readability of mode and distro detection logic.

### ADR-003: pyproject.toml replaces setup.py
- **Date**: 2026-06-04
- **Context**: envycontrol uses legacy setup.py. PEP 517/518 (2018) standardized pyproject.toml.
- **Decision**: envytweaks-cli uses pyproject.toml with setuptools or hatchling backend.
- **Justification**: setup.py is deprecated for new projects. All major distro packaging tools support pyproject.toml.

### ADR-004: pkexec exit codes must be handled explicitly
- **Date**: 2026-06-04
- **Context**: GPU_profile_selector does not distinguish pkexec cancel (126) from real error.
  This leads to stale UI state and confusing restart prompts on user cancellation.
- **Decision**: _execSwitch() in Utility.js must capture and pass exit code to callback.
  126 = user cancelled (re-query state, no restart prompt). 127 = not installed (show error). 0 = success.
- **Justification**: Prevents UX regression where cancelling pkexec triggers a restart dialog.

### ADR-005: GPU_PROFILE_NOT_INSTALLED state added
- **Date**: 2026-06-04
- **Context**: GPU_profile_selector always shows a restart popup even when envycontrol is not installed.
- **Decision**: Add GPU_PROFILE_NOT_INSTALLED constant. getCurrentProfile() returns it when CLI is absent.
  Both views disable profile switching menu items when this state is active.
- **Justification**: Clear user feedback when the dependency is missing, prevents broken state loops.

---

## Active Blockers

- None.

```

## File: .planning/continue-here.md
```md
# continue-here.md — envytweaks

## Handoff State

Project just connected via forge. All planning documents written. No code exists yet.

## Next Immediate Step

Execute Phase 1.0: Monorepo Scaffolding.
Start with: forge wave-start "monorepo-scaffolding"

## Context Summary

envytweaks is a monorepo rewrite of:
- envycontrol (Python CLI for NVIDIA Optimus GPU switching)
- GPU_profile_selector (GNOME Shell extension, GUI frontend)

Both original projects are abandoned. envytweaks unifies them under active maintenance.

Components:
1. envytweaks-cli/ — Python 3.10+, pathlib.Path, match/case, pyproject.toml, src layout
2. envytweaks-gnome/ — GJS/ESM extension, GNOME 43-50, fixes pkexec exit codes, adds RTD3 mode setting

Key decisions (see STATE.md ADRs):
- Python 3.10+ minimum (match/case required)
- pyproject.toml packaging
- pkexec exit 126=cancel, 127=not_installed must be handled explicitly
- GPU_PROFILE_NOT_INSTALLED state disables UI buttons

## Files to read at start of next session:
- .planning/PROJECT.md — full architecture
- .planning/ROADMAP.md — all phases and tasks
- .planning/STATE.md — ADR history

```

## File: diagnose.py
```py
#!/usr/bin/env python3
"""diagnose.py — Diagnostic script to verify EnvyTweaks integration and GPU status."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path



# Helper functions for colored console output
def color(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(text: str) -> str:
    return color(text, "1;32")


def red(text: str) -> str:
    return color(text, "1;31")


def yellow(text: str) -> str:
    return color(text, "1;33")


def blue(text: str) -> str:
    return color(text, "1;34")


def bold(text: str) -> str:
    return color(text, "1")


def print_header(title: str) -> None:
    print(bold(blue(f"\n=== {title} ===")))


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, str]:
    """Run a terminal command and return exit code, stdout, and stderr."""
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Command not found"


def find_nvidia_pci_id() -> str | None:
    """Find and return the normalized PCI ID (e.g. 0000:01:00.0) of the NVIDIA GPU."""
    code, stdout, _ = run_cmd(["lspci"])
    if code != 0:
        return None

    for line in stdout.splitlines():
        if "NVIDIA" in line and (
            "VGA compatible controller" in line or "3D controller" in line
        ):
            match = re.match(r"^([0-9a-fA-F:\.]+)", line)
            if match:
                pci_id = match.group(1)
                # Normalize: if format is "01:00.0", prepend "0000:"
                if len(pci_id.split(":")) == 2:
                    return f"0000:{pci_id}"
                return pci_id
    return None


def main() -> None:
    print_header("EnvyTweaks Diagnostic Utility")
    print("This script verifies if the CLI, GNOME widget, and GPU offloading are working.")

    # -------------------------------------------------------------------------
    # 1. CLI Validation
    # -------------------------------------------------------------------------
    print_header("1. CLI Verification")
    cli_path = shutil.which("envytweaks")

    if cli_path:
        print(f"CLI Path: {green(cli_path)}")
        # Check CLI version
        _, version_out, _ = run_cmd(["envytweaks", "-v"])
        print(f"CLI Version: {green(version_out)}")

        # Check Active Mode
        _, mode_out, _ = run_cmd(["envytweaks", "-q"])
        print(f"Active Mode: {green(mode_out)}")
    else:
        print(f"CLI Status: {red('Not found in system PATH!')}")
        print("Please run the installer: sudo ./install.sh")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # 2. GNOME Extension Validation
    # -------------------------------------------------------------------------
    print_header("2. GNOME Shell Extension Verification")
    user_home = Path.home()
    ext_path = user_home / ".local/share/gnome-shell/extensions/envytweaks@cachyos.org"

    if ext_path.exists():
        print(f"Extension Files: {green('Installed')} in {ext_path}")

        # Check activation state via gnome-extensions
        code, stdout, _ = run_cmd(["gnome-extensions", "info", "envytweaks@cachyos.org"])
        if code == 0:
            active_match = re.search(r"Estado:\s*(\w+)", stdout)
            # Fallback for English output
            if not active_match:
                active_match = re.search(r"State:\s*(\w+)", stdout)

            if active_match:
                state = active_match.group(1)
                match state.upper():
                    case "ACTIVE" | "ENABLED" | "ACTIVO":
                        print(f"Extension State: {green(f'ACTIVE ({state})')}")
                        print("The GNOME widget should be visible in your top panel / Quick Settings.")
                    case _:
                        print(f"Extension State: {yellow(f'INACTIVE ({state})')}")
                        print("You can enable it using: gnome-extensions enable envytweaks@cachyos.org")
            else:
                print(f"Extension State: {yellow('Unknown (could not parse gnome-extensions output)')}")
        else:
            print(f"Extension State: {yellow('Not active or could not query state')}")
            print("Try enabling it using: gnome-extensions enable envytweaks@cachyos.org")
    else:
        print(f"Extension Status: {red('Not installed in user directory!')}")
        print("Please run `./install.sh` to install both the CLI and GNOME extension.")

    # -------------------------------------------------------------------------
    # 3. GPU Hardware & Power Management (RTD3) Validation
    # -------------------------------------------------------------------------
    print_header("3. GPU Hardware & Runtime Power Management")
    pci_id = find_nvidia_pci_id()

    if pci_id:
        print(f"NVIDIA GPU PCI Bus ID: {green(pci_id)}")
        pci_dir = Path("/sys/bus/pci/devices") / pci_id

        # Runtime PM parameters
        status_path = pci_dir / "power" / "runtime_status"
        suspended_time_path = pci_dir / "power" / "runtime_suspended_time"
        control_path = pci_dir / "power" / "control"

        if status_path.exists():
            status = status_path.read_text(encoding="utf-8").strip()
            status_colored = green(status) if status == "suspended" else yellow(status)
            print(f"Runtime Power Status: {status_colored}")
        else:
            print(f"Runtime Power Status: {yellow('Unavailable (sysfs path not found)')}")

        if control_path.exists():
            control = control_path.read_text(encoding="utf-8").strip()
            print(f"Runtime Power Control: {green(control)}")
        else:
            print(f"Runtime Power Control: {yellow('Unavailable')}")

        if suspended_time_path.exists():
            try:
                suspended_ms = int(suspended_time_path.read_text(encoding="utf-8").strip())
                if suspended_ms > 0:
                    print(f"Historical Suspends: {green('Yes')} ({suspended_ms} ms suspended total)")
                else:
                    print(f"Historical Suspends: {yellow('No yet')} (0 ms suspended)")
            except ValueError:
                print(f"Historical Suspends: {yellow('Could not parse suspended time')}")

        # Check nvidia-smi processes
        code, smi_out, _ = run_cmd(["nvidia-smi"])
        if code == 0:
            print(f"\n{bold('NVIDIA-SMI status:')}")
            # Check for processes keeping GPU active
            proc_lines = []
            capture = False
            for line in smi_out.splitlines():
                if "Processes:" in line:
                    capture = True
                    continue
                if capture and line.strip() and not line.startswith("+") and not line.startswith("|="):
                    proc_lines.append(line.strip())

            if proc_lines:
                print(yellow("Warning: The following processes are using the NVIDIA GPU, keeping it awake:"))
                for pl in proc_lines:
                    print(f"  {pl}")
            else:
                print(green("No processes are currently running on the NVIDIA GPU."))
        else:
            print(yellow("\nNVIDIA-SMI not accessible or GPU drivers not loaded."))
    else:
        print(f"NVIDIA Hardware: {red('NVIDIA GPU not detected via lspci!')}")
        print("Note: If you are in 'integrated' mode, the GPU is powered off and will not show up.")

    # -------------------------------------------------------------------------
    # 4. Rendering Offload Test
    # -------------------------------------------------------------------------
    print_header("4. Graphics Offloading (Render Offload) Test")

    if shutil.which("glxinfo"):
        # Test 1: Standard Execution (should use Integrated iGPU)
        # Clear any nvidia-offload vars in the agent's environment
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["__GLX_VENDOR_LIBRARY_NAME", "__NV_PRIME_RENDER_OFFLOAD"]
        }

        clean_env["__GLX_VENDOR_LIBRARY_NAME"] = ""
        clean_env["__NV_PRIME_RENDER_OFFLOAD"] = ""

        _, i_out, _ = run_cmd(["glxinfo"], env=clean_env)
        igpu_renderer = "Unknown"
        for line in i_out.splitlines():
            if "OpenGL renderer string" in line:
                igpu_renderer = line.split(":", 1)[1].strip()
                break

        print(f"Default GPU (Integrated): {blue(igpu_renderer)}")

        # Test 2: Offloaded Execution (should use NVIDIA dGPU)
        offload_env = clean_env.copy()
        offload_env["__NV_PRIME_RENDER_OFFLOAD"] = "1"
        offload_env["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"

        _, d_out, _ = run_cmd(["glxinfo"], env=offload_env)
        dgpu_renderer = "Unknown"
        for line in d_out.splitlines():
            if "OpenGL renderer string" in line:
                dgpu_renderer = line.split(":", 1)[1].strip()
                break

        print(f"Offloaded GPU (NVIDIA dGPU): {blue(dgpu_renderer)}")

        if "NVIDIA" in dgpu_renderer and "NVIDIA" not in igpu_renderer:
            print(f"\nOffloading Status: {green('WORKING PERFECTLY')}")
            print("Applications run on the Integrated GPU by default, and use the NVIDIA GPU only when requested.")
        elif "NVIDIA" in igpu_renderer and "NVIDIA" in dgpu_renderer:
            print(f"\nOffloading Status: {yellow('NVIDIA ALWAYS ACTIVE')}")
            print("Both default and offloaded applications are running on the NVIDIA GPU.")
            print("This is normal if you have an external monitor connected to an NVIDIA-wired port.")
        else:
            print(f"\nOffloading Status: {red('OFFLOAD FAILED OR UNEXPECTED')}")
            print("NVIDIA dGPU was not detected as the offloaded renderer.")
    else:
        print(yellow("glxinfo utility is not installed. Skipping render offload test."))
        print("Install 'mesa-utils' (Debian/Ubuntu) or 'mesa-utils' (Arch/Fedora) to run this test.")


if __name__ == "__main__":
    main()

```

## File: envytweaks-cli/pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "envytweaks"
version = "1.0.0"
description = "GPU mode switcher for NVIDIA Optimus laptops on Linux"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
keywords = ["nvidia", "optimus", "prime", "gpu", "linux"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: POSIX :: Linux",
]

[project.scripts]
envytweaks = "envytweaks.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

```

## File: envytweaks-cli/src/envytweaks.egg-info/SOURCES.txt
```txt
pyproject.toml
src/envytweaks/__init__.py
src/envytweaks/cache.py
src/envytweaks/cli.py
src/envytweaks/config.py
src/envytweaks/switcher.py
src/envytweaks/system.py
src/envytweaks.egg-info/PKG-INFO
src/envytweaks.egg-info/SOURCES.txt
src/envytweaks.egg-info/dependency_links.txt
src/envytweaks.egg-info/entry_points.txt
src/envytweaks.egg-info/top_level.txt
```

## File: envytweaks-cli/src/envytweaks.egg-info/dependency_links.txt
```txt


```

## File: envytweaks-cli/src/envytweaks.egg-info/entry_points.txt
```txt
[console_scripts]
envytweaks = envytweaks.cli:main

```

## File: envytweaks-cli/src/envytweaks.egg-info/top_level.txt
```txt
envytweaks

```

## File: envytweaks-cli/src/envytweaks/__init__.py
```py
"""envytweaks — GPU mode switcher for NVIDIA Optimus laptops."""

VERSION = "1.0.0"

```

## File: envytweaks-cli/src/envytweaks/cache.py
```py
"""cache.py — CachedConfig: persists the NVIDIA GPU PCI bus ID between mode switches."""

import json
import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from envytweaks.config import CACHE_FILE_PATH
from envytweaks.system import get_nvidia_gpu_pci_bus, get_current_mode


class CachedConfig:
    """Adapter that caches the NVIDIA GPU PCI bus ID to avoid lspci failures
    when switching from integrated mode (where the GPU is powered off)."""

    def __init__(self, app_args) -> None:  # noqa: ANN001
        self.app_args = app_args
        self.current_mode: str = get_current_mode()
        self._nvidia_gpu_pci_bus: str | None = None
        self._obj: dict | None = None

    # ------------------------------------------------------------------
    # Context manager adapter
    # ------------------------------------------------------------------

    @contextmanager
    def adapter(self) -> Generator[None, None, None]:
        """Temporarily rebind get_nvidia_gpu_pci_bus to the cached version."""
        import envytweaks.system as _system

        original_fn = _system.get_nvidia_gpu_pci_bus
        use_cache = CACHE_FILE_PATH.exists()

        if self._is_hybrid():
            self.create_cache_file()

        if use_cache:
            self.read_cache_file()
            _system.get_nvidia_gpu_pci_bus = self.get_nvidia_gpu_pci_bus  # type: ignore[method-assign]

        try:
            yield
        finally:
            _system.get_nvidia_gpu_pci_bus = original_fn  # type: ignore[method-assign]

    # ------------------------------------------------------------------
    # Cache lifecycle
    # ------------------------------------------------------------------

    def create_cache_file(self) -> None:
        if not self._is_hybrid():
            raise ValueError(
                "--cache-create requires that the system be in the hybrid Optimus mode"
            )
        self._nvidia_gpu_pci_bus = get_nvidia_gpu_pci_bus()
        self._obj = {"nvidia_gpu_pci_bus": self._nvidia_gpu_pci_bus}
        self._write_cache_file()

    def read_cache_file(self) -> None:
        if CACHE_FILE_PATH.exists():
            self._obj = json.loads(CACHE_FILE_PATH.read_text(encoding="utf-8"))
            self._nvidia_gpu_pci_bus = self._obj["nvidia_gpu_pci_bus"]
        elif self._is_hybrid():
            self._nvidia_gpu_pci_bus = get_nvidia_gpu_pci_bus()
        else:
            raise ValueError(
                "No cache present. Operation requires the system to be in hybrid mode"
            )

    def _write_cache_file(self) -> None:
        dry_run = getattr(self.app_args, "dry_run", False)
        if dry_run:
            print(f"[DRY-RUN] Would create cache file {CACHE_FILE_PATH}")
            return
        try:
            CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE_PATH.write_text(
                json.dumps(self._obj, indent=4), encoding="utf-8"
            )
            logging.debug("Created cache file %s", CACHE_FILE_PATH)
        except PermissionError:
            logging.warning("Could not write cache to %s (insufficient permissions)", CACHE_FILE_PATH)

    @staticmethod
    def delete_cache_file(dry_run: bool = False) -> None:
        if dry_run:
            print(f"[DRY-RUN] Would delete cache file {CACHE_FILE_PATH}")
            return
        try:
            CACHE_FILE_PATH.unlink(missing_ok=True)
            try:
                CACHE_FILE_PATH.parent.rmdir()
            except OSError:
                pass
            logging.debug("Removed cache file %s", CACHE_FILE_PATH)
        except PermissionError:
            logging.warning("Could not delete cache file %s", CACHE_FILE_PATH)

    @staticmethod
    def show_cache_file() -> None:
        if CACHE_FILE_PATH.exists():
            print(CACHE_FILE_PATH.read_text(encoding="utf-8"))
        else:
            print(f"ERROR: Could not read {CACHE_FILE_PATH}")

    def get_nvidia_gpu_pci_bus(self) -> str:
        if self._nvidia_gpu_pci_bus is None:
            logging.error("Cache not loaded — call read_cache_file() first")
            sys.exit(1)
        return self._nvidia_gpu_pci_bus

    def _is_hybrid(self) -> bool:
        return self.current_mode == "hybrid"



```

## File: envytweaks-cli/src/envytweaks/cli.py
```py
"""cli.py — Argument parsing and entry point for the envytweaks CLI."""

import argparse
import logging
import sys

from envytweaks import VERSION
from envytweaks.cache import CachedConfig, get_current_mode
from envytweaks.config import (
    SDDM_XSETUP_PATH,
    SDDM_XSETUP_CONTENT,
    SUPPORTED_MODES,
    SUPPORTED_DISPLAY_MANAGERS,
    RTD3_MODES,
    create_file,
    cleanup,
)
from envytweaks.system import assert_root, rebuild_initramfs
from envytweaks.switcher import graphics_mode_switcher


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envytweaks",
        description="GPU mode switcher for NVIDIA Optimus laptops on Linux",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=VERSION,
        help="Output the current version",
    )
    parser.add_argument(
        "-q", "--query", action="store_true",
        help="Query the current graphics mode",
    )
    parser.add_argument(
        "-s", "--switch", type=str, metavar="MODE", choices=SUPPORTED_MODES,
        help=f"Switch the graphics mode. Available: {', '.join(SUPPORTED_MODES)}",
    )
    parser.add_argument(
        "--dm", type=str, metavar="DISPLAY_MANAGER", choices=SUPPORTED_DISPLAY_MANAGERS,
        help=f"Manually specify your Display Manager for nvidia mode. Available: {', '.join(SUPPORTED_DISPLAY_MANAGERS)}",
    )
    parser.add_argument(
        "--force-comp", action="store_true",
        help="Enable ForceCompositionPipeline on nvidia mode",
    )
    parser.add_argument(
        "--coolbits", type=int, nargs="?", metavar="VALUE", const=28,
        help="Enable Coolbits on nvidia mode (default: 28)",
    )
    parser.add_argument(
        "--rtd3", type=int, nargs="?", metavar="VALUE", choices=RTD3_MODES, const=2,
        help=f"Setup RTD3 Power Management on hybrid mode. Available: {RTD3_MODES}. Default: 2",
    )
    parser.add_argument(
        "--use-nvidia-current", action="store_true",
        help="Use nvidia-current instead of nvidia for kernel modules",
    )
    parser.add_argument(
        "--reset-sddm", action="store_true",
        help="Restore the default SDDM Xsetup file",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Revert all changes made by envytweaks",
    )
    parser.add_argument(
        "--cache-create", action="store_true",
        help="Create cache (only works in hybrid mode)",
    )
    parser.add_argument(
        "--cache-delete", action="store_true",
        help="Delete the envytweaks cache",
    )
    parser.add_argument(
        "--cache-query", action="store_true",
        help="Show the envytweaks cache",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Previsualize changes without modifying system files",
    )
    parser.add_argument(
        "--verbose", action="store_true", default=False,
        help="Enable verbose mode",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    logging.basicConfig(format="%(levelname)s: %(message)s")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # read-only commands — no root required
    if args.query:
        print(get_current_mode())
        return
    if args.cache_query:
        CachedConfig.show_cache_file()
        return

    # cache management
    if args.cache_create:
        if not args.dry_run:
            assert_root()
        CachedConfig(args).create_cache_file()
        return
    if args.cache_delete:
        if not args.dry_run:
            assert_root()
        CachedConfig.delete_cache_file()
        return

    # write operations
    if args.switch or args.reset_sddm or args.reset:
        with CachedConfig(args).adapter():
            if args.switch:
                if not args.dry_run:
                    assert_root()
                graphics_mode_switcher(
                    args.switch,
                    args.dm,
                    args.force_comp,
                    args.coolbits,
                    args.rtd3,
                    args.use_nvidia_current,
                    dry_run=args.dry_run,
                )
            elif args.reset_sddm:
                if not args.dry_run:
                    assert_root()
                create_file(SDDM_XSETUP_PATH, SDDM_XSETUP_CONTENT, executable=True, dry_run=args.dry_run)
                print("Operation completed successfully")
            elif args.reset:
                if not args.dry_run:
                    assert_root()
                cleanup(dry_run=args.dry_run)
                if not args.dry_run:
                    CachedConfig.delete_cache_file()
                    rebuild_initramfs()
                print("Operation completed successfully")


if __name__ == "__main__":
    main()

```

## File: envytweaks-cli/src/envytweaks/config.py
```py
"""config.py — Path constants, file creation, and cleanup for envytweaks."""

import logging
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

CACHE_FILE_PATH = Path("/var/cache/envytweaks/cache.json")

BLACKLIST_PATH = Path("/etc/modprobe.d/blacklist-nvidia.conf")
UDEV_INTEGRATED_PATH = Path("/etc/udev/rules.d/50-remove-nvidia.rules")
UDEV_PM_PATH = Path("/etc/udev/rules.d/80-nvidia-pm.rules")
XORG_PATH = Path("/etc/X11/xorg.conf")
EXTRA_XORG_PATH = Path("/etc/X11/xorg.conf.d/10-nvidia.conf")
MODESET_PATH = Path("/etc/modprobe.d/nvidia.conf")
SDDM_XSETUP_PATH = Path("/usr/share/sddm/scripts/Xsetup")
LIGHTDM_SCRIPT_PATH = Path("/etc/lightdm/nvidia.sh")
LIGHTDM_CONFIG_PATH = Path("/etc/lightdm/lightdm.conf.d/20-nvidia.conf")

SUPPORTED_MODES: list[str] = ["integrated", "hybrid", "nvidia"]
SUPPORTED_DISPLAY_MANAGERS: list[str] = ["gdm", "gdm3", "sddm", "lightdm"]
RTD3_MODES: list[int] = [0, 1, 2, 3]

# ---------------------------------------------------------------------------
# File content templates
# ---------------------------------------------------------------------------

BLACKLIST_CONTENT = """\
# Automatically generated by envytweaks

blacklist nouveau
blacklist nova_core
blacklist nova_drm
blacklist nvidia
blacklist nvidia_drm
blacklist nvidia_uvm
blacklist nvidia_modeset
blacklist nvidia_current
blacklist nvidia_current_drm
blacklist nvidia_current_uvm
blacklist nvidia_current_modeset
blacklist i2c_nvidia_gpu
alias nouveau off
alias nova_core off
alias nova_drm off
alias nvidia off
alias nvidia_drm off
alias nvidia_uvm off
alias nvidia_modeset off
alias nvidia_current off
alias nvidia_current_drm off
alias nvidia_current_uvm off
alias nvidia_current_modeset off
alias i2c_nvidia_gpu off
"""

UDEV_INTEGRATED = """\
# Automatically generated by envytweaks

# Remove NVIDIA USB xHCI Host Controller devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x0c0330", ATTR{power/control}="auto", ATTR{remove}="1"

# Remove NVIDIA USB Type-C UCSI devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x0c8000", ATTR{power/control}="auto", ATTR{remove}="1"

# Remove NVIDIA Audio devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x040300", ATTR{power/control}="auto", ATTR{remove}="1"

# Remove NVIDIA VGA/3D controller devices
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x03[0-9]*", ATTR{power/control}="auto", ATTR{remove}="1"
"""

UDEV_PM_CONTENT = """\
# Automatically generated by envytweaks

# Remove NVIDIA USB xHCI Host Controller devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x0c0330", ATTR{remove}="1"

# Remove NVIDIA USB Type-C UCSI devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x0c8000", ATTR{remove}="1"

# Remove NVIDIA Audio devices, if present
ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x040300", ATTR{remove}="1"

# Enable runtime PM for NVIDIA VGA/3D controller devices on driver bind
ACTION=="bind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030000", TEST=="power/control", ATTR{power/control}="auto"
ACTION=="bind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030200", TEST=="power/control", ATTR{power/control}="auto"

# Disable runtime PM for NVIDIA VGA/3D controller devices on driver unbind
ACTION=="unbind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030000", TEST=="power/control", ATTR{power/control}="on"
ACTION=="unbind", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{class}=="0x030200", TEST=="power/control", ATTR{power/control}="on"
"""

XORG_INTEL = """\
# Automatically generated by envytweaks

Section "ServerLayout"
    Identifier "layout"
    Screen 0 "nvidia"
    Inactive "intel"
EndSection

Section "Device"
    Identifier "nvidia"
    Driver "nvidia"
    BusID "{}"
EndSection

Section "Screen"
    Identifier "nvidia"
    Device "nvidia"
    Option "AllowEmptyInitialConfiguration"
EndSection

Section "Device"
    Identifier "intel"
    Driver "modesetting"
EndSection

Section "Screen"
    Identifier "intel"
    Device "intel"
EndSection
"""

XORG_AMD = """\
# Automatically generated by envytweaks

Section "ServerLayout"
    Identifier "layout"
    Screen 0 "nvidia"
    Inactive "amdgpu"
EndSection

Section "Device"
    Identifier "nvidia"
    Driver "nvidia"
    BusID "{}"
EndSection

Section "Screen"
    Identifier "nvidia"
    Device "nvidia"
    Option "AllowEmptyInitialConfiguration"
EndSection

Section "Device"
    Identifier "amdgpu"
    Driver "amdgpu"
EndSection

Section "Screen"
    Identifier "amd"
    Device "amdgpu"
EndSection
"""

EXTRA_XORG_CONTENT = """\
# Automatically generated by envytweaks

Section "OutputClass"
    Identifier "nvidia"
    MatchDriver "nvidia-drm"
    Driver "nvidia"
"""

FORCE_COMP = '    Option "ForceCompositionPipeline" "true"\n'
COOLBITS_TEMPLATE = '    Option "Coolbits" "{}"\n'

def build_modeset_content(driver: str = "nvidia", rtd3: int | None = None) -> str:
    """Generate modprobe content parameterized by driver name and RTD3 level."""
    base = (
        f"# Automatically generated by envytweaks\n\n"
        f"options {driver}-drm modeset=1\n"
    )
    if rtd3 is not None:
        base += f'options {driver} "NVreg_DynamicPowerManagement=0x0{rtd3}"\n'
    base += f"options {driver} NVreg_UsePageAttributeTable=1 NVreg_InitializeSystemMemoryAllocations=0\n"
    return base


MODESET_CONTENT = build_modeset_content("nvidia")
MODESET_CURRENT_CONTENT = build_modeset_content("nvidia-current")


def build_modeset_rtd3(rtd3_mode: int, driver: str = "nvidia") -> str:
    return build_modeset_content(driver=driver, rtd3=rtd3_mode)


MODESET_RTD3 = build_modeset_content("nvidia", 1)  # Template placeholder
MODESET_CURRENT_RTD3 = build_modeset_content("nvidia-current", 1)

LIGHTDM_CONFIG_CONTENT = """\
# Automatically generated by envytweaks

[Seat:*]
display-setup-script=/etc/lightdm/nvidia.sh
"""

SDDM_XSETUP_CONTENT = """\
#!/bin/sh
# Xsetup - run as root before the login dialog appears

"""

NVIDIA_XRANDR_SCRIPT = """\
#!/bin/sh
# Automatically generated by envytweaks

current=""

xrandr --setprovideroutputsource "{}" NVIDIA-0
xrandr --auto

for next in $(xrandr --listmonitors | grep -E " *[0-9]+:.*" | cut -d" " -f6); do
  [ -z "$current" ] && current=$next && continue
  xrandr --output "$current" --auto --output "$next" --auto --right-of "$current"
  current=$next
done
"""

# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def create_file(path: Path, content: str, executable: bool = False, dry_run: bool = False) -> None:
    """Write content to path, creating parent directories as needed."""
    if dry_run:
        exec_str = " (executable)" if executable else ""
        print(f"[DRY-RUN] Would create {path}{exec_str} ({len(content.encode('utf-8'))} bytes)")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print(content)
        return

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logging.info("Created file %s", path)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print(content)
        if executable:
            subprocess.run(["chmod", "+x", str(path)], stdout=subprocess.DEVNULL)
            logging.info("Added execution privilege to %s", path)
    except OSError as e:
        logging.error("Failed to create file '%s': %s", path, e)


def cleanup(dry_run: bool = False) -> None:
    """Remove all config files generated by envytweaks."""
    to_remove: list[Path] = [
        BLACKLIST_PATH,
        UDEV_INTEGRATED_PATH,
        UDEV_PM_PATH,
        XORG_PATH,
        EXTRA_XORG_PATH,
        MODESET_PATH,
        LIGHTDM_SCRIPT_PATH,
        LIGHTDM_CONFIG_PATH,
        # legacy envycontrol paths
        Path("/etc/X11/xorg.conf.d/90-nvidia.conf"),
        Path("/lib/udev/rules.d/50-remove-nvidia.rules"),
        Path("/lib/udev/rules.d/80-nvidia-pm.rules"),
    ]

    for file_path in to_remove:
        if dry_run:
            if file_path.exists():
                print(f"[DRY-RUN] Would remove file {file_path}")
            continue

        try:
            file_path.unlink(missing_ok=True)
            logging.info("Removed file %s", file_path)
        except OSError as e:
            logging.error("Failed to remove file '%s': %s", file_path, e)

    backup_path = Path(str(SDDM_XSETUP_PATH) + ".bak")
    if backup_path.exists():
        if dry_run:
            print(f"[DRY-RUN] Would restore Xsetup backup {backup_path} -> {SDDM_XSETUP_PATH}")
        else:
            logging.info("Restoring Xsetup backup")
            create_file(SDDM_XSETUP_PATH, backup_path.read_text(encoding="utf-8"))
            backup_path.unlink()
            logging.info("Removed file %s", backup_path)

```

## File: envytweaks-cli/src/envytweaks/switcher.py
```py
"""switcher.py — Main GPU mode switching logic for envytweaks."""

import logging
import subprocess

from envytweaks.config import (
    BLACKLIST_PATH,
    BLACKLIST_CONTENT,
    COOLBITS_TEMPLATE,
    EXTRA_XORG_PATH,
    EXTRA_XORG_CONTENT,
    FORCE_COMP,
    LIGHTDM_CONFIG_PATH,
    LIGHTDM_CONFIG_CONTENT,
    LIGHTDM_SCRIPT_PATH,
    MODESET_PATH,
    MODESET_CONTENT,
    MODESET_CURRENT_CONTENT,
    MODESET_RTD3,
    MODESET_CURRENT_RTD3,
    SDDM_XSETUP_PATH,
    SDDM_XSETUP_CONTENT,
    UDEV_INTEGRATED_PATH,
    UDEV_INTEGRATED,
    UDEV_PM_PATH,
    UDEV_PM_CONTENT,
    XORG_PATH,
    XORG_INTEL,
    XORG_AMD,
    create_file,
    cleanup,
)
from envytweaks.system import (
    _run_subprocess,
    generate_xrandr_script,
    get_display_manager,
    get_igpu_vendor,
    get_nvidia_gpu_pci_bus,
    rebuild_initramfs,
    save_current_mode,
)


def graphics_mode_switcher(
    graphics_mode: str,
    user_display_manager: str | None,
    enable_force_comp: bool,
    coolbits_value: int | None,
    rtd3_value: int | None,
    use_nvidia_current: bool,
    dry_run: bool = False,
) -> None:
    """Switch the GPU mode to integrated, hybrid, or nvidia."""
    print(f"Switching to {graphics_mode} mode{' (DRY-RUN)' if dry_run else ''}")

    match graphics_mode:
        case "integrated":
            if dry_run:
                print("[DRY-RUN] Would disable nvidia-persistenced.service")
            else:
                result = _run_subprocess(
                    ["systemctl", "disable", "nvidia-persistenced.service"]
                )
                if result.returncode == 0:
                    print("Successfully disabled nvidia-persistenced.service")
                else:
                    logging.error("An error occurred while disabling service")

            cleanup(dry_run=dry_run)
            create_file(BLACKLIST_PATH, BLACKLIST_CONTENT, dry_run=dry_run)
            create_file(UDEV_INTEGRATED_PATH, UDEV_INTEGRATED, dry_run=dry_run)
            if not dry_run:
                rebuild_initramfs()

        case "hybrid":
            print(f"Enable PCI-Express Runtime D3 (RTD3) Power Management: {rtd3_value or False}")
            cleanup(dry_run=dry_run)

            if dry_run:
                print("[DRY-RUN] Would enable nvidia-persistenced.service")
            else:
                result = _run_subprocess(
                    ["systemctl", "enable", "nvidia-persistenced.service"]
                )
                if result.returncode == 0:
                    print("Successfully enabled nvidia-persistenced.service")
                else:
                    logging.error("An error occurred while enabling service")

            if rtd3_value is None:
                modeset = MODESET_CURRENT_CONTENT if use_nvidia_current else MODESET_CONTENT
            else:
                template = MODESET_CURRENT_RTD3 if use_nvidia_current else MODESET_RTD3
                modeset = template.format(rtd3_value)
                create_file(UDEV_PM_PATH, UDEV_PM_CONTENT, dry_run=dry_run)

            create_file(MODESET_PATH, modeset, dry_run=dry_run)
            if not dry_run:
                rebuild_initramfs()

        case "nvidia":
            print(f"Enable ForceCompositionPipeline: {enable_force_comp}")
            print(f"Enable Coolbits: {coolbits_value or False}")

            if dry_run:
                print("[DRY-RUN] Would enable nvidia-persistenced.service")
            else:
                result = _run_subprocess(
                    ["systemctl", "enable", "nvidia-persistenced.service"]
                )
                if result.returncode == 0:
                    print("Successfully enabled nvidia-persistenced.service")
                else:
                    logging.error("An error occurred while enabling service")

            cleanup(dry_run=dry_run)
            nvidia_pci_bus = get_nvidia_gpu_pci_bus()
            igpu_vendor = get_igpu_vendor()

            match igpu_vendor:
                case "intel":
                    create_file(XORG_PATH, XORG_INTEL.format(nvidia_pci_bus), dry_run=dry_run)
                case "amd":
                    create_file(XORG_PATH, XORG_AMD.format(nvidia_pci_bus), dry_run=dry_run)

            modeset = MODESET_CURRENT_CONTENT if use_nvidia_current else MODESET_CONTENT
            create_file(MODESET_PATH, modeset, dry_run=dry_run)

            # optional extra Xorg config
            if enable_force_comp and coolbits_value is not None:
                create_file(
                    EXTRA_XORG_PATH,
                    EXTRA_XORG_CONTENT
                    + FORCE_COMP
                    + COOLBITS_TEMPLATE.format(coolbits_value)
                    + "EndSection\n",
                    dry_run=dry_run,
                )
            elif enable_force_comp:
                create_file(
                    EXTRA_XORG_PATH,
                    EXTRA_XORG_CONTENT + FORCE_COMP + "EndSection\n",
                    dry_run=dry_run,
                )
            elif coolbits_value is not None:
                create_file(
                    EXTRA_XORG_PATH,
                    EXTRA_XORG_CONTENT
                    + COOLBITS_TEMPLATE.format(coolbits_value)
                    + "EndSection\n",
                    dry_run=dry_run,
                )

            display_manager = user_display_manager or get_display_manager()

            match display_manager:
                case "sddm":
                    if SDDM_XSETUP_PATH.exists():
                        logging.info("Creating Xsetup backup")
                        create_file(
                            SDDM_XSETUP_PATH.with_suffix(".sh.bak"),
                            SDDM_XSETUP_PATH.read_text(encoding="utf-8"),
                            dry_run=dry_run,
                        )
                    create_file(
                        SDDM_XSETUP_PATH,
                        generate_xrandr_script(igpu_vendor),
                        executable=True,
                        dry_run=dry_run,
                    )
                case "lightdm":
                    create_file(
                        LIGHTDM_SCRIPT_PATH,
                        generate_xrandr_script(igpu_vendor),
                        executable=True,
                        dry_run=dry_run,
                    )
                    create_file(LIGHTDM_CONFIG_PATH, LIGHTDM_CONFIG_CONTENT, dry_run=dry_run)

            if not dry_run:
                rebuild_initramfs()

    save_current_mode(graphics_mode, dry_run=dry_run)
    print("Operation completed successfully")
    if not dry_run:
        print("Please reboot your computer for changes to take effect!")

```

## File: envytweaks-cli/src/envytweaks/system.py
```py
"""system.py — GPU/iGPU/DM detection and initramfs rebuild for envytweaks."""

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from envytweaks.config import NVIDIA_XRANDR_SCRIPT


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------


def _run_subprocess(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess, suppressing output unless verbose/debug mode is on."""
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        return subprocess.run(cmd)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------


def get_nvidia_gpu_pci_bus() -> str:
    """Return the NVIDIA dGPU PCI bus ID in 'PCI:bus:device:function' format."""
    lspci_output = subprocess.check_output(["lspci"]).decode("utf-8")
    for line in lspci_output.splitlines():
        if "NVIDIA" in line and (
            "VGA compatible controller" in line or "3D controller" in line
        ):
            pci_bus_id = line.split()[0].replace("0000:", "")
            logging.info("Found NVIDIA GPU at %s", pci_bus_id)
            bus, device_function = pci_bus_id.split(":")
            device, function = device_function.split(".")
            return f"PCI:{int(bus, 16)}:{int(device, 16)}:{int(function, 16)}"

    logging.error("Could not find NVIDIA GPU")
    print("Try switching to hybrid mode first!")
    sys.exit(1)


def get_igpu_vendor() -> str | None:
    """Return 'intel', 'amd', or None based on lspci output."""
    lspci_output = subprocess.check_output(["lspci"]).decode("utf-8")
    for line in lspci_output.splitlines():
        if "VGA compatible controller" in line or "Display controller" in line:
            if "Intel" in line:
                logging.info("Found Intel iGPU")
                return "intel"
            if "ATI" in line or "AMD" in line or "AMD/ATI" in line:
                logging.info("Found AMD iGPU")
                return "amd"
    logging.warning("Could not find Intel or AMD iGPU")
    return None


STATE_FILE_PATH = Path("/var/lib/envytweaks/current_mode")
SAFE_PROVIDER_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def get_amd_igpu_name() -> str | None:
    """Return the AMD iGPU provider name from xrandr, or None on failure."""
    if not Path("/usr/bin/xrandr").exists():
        logging.warning("'xrandr' not available — make sure the package is installed")
        return None

    try:
        xrandr_output = subprocess.check_output(
            ["xrandr", "--listproviders"]
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        logging.warning("Failed to run 'xrandr --listproviders'")
        return None

    match = re.search(r"name:\s*([a-zA-Z0-9._-]+)", xrandr_output)
    if match:
        raw_name = match.group(1)
        if SAFE_PROVIDER_RE.match(raw_name):
            return raw_name

    logging.warning("Could not find valid AMD iGPU in xrandr output")
    return None


def generate_xrandr_script(igpu_vendor: str | None) -> str:
    """Return the xrandr shell script content for the given iGPU vendor."""
    match igpu_vendor:
        case "intel":
            return NVIDIA_XRANDR_SCRIPT.format("modesetting")
        case "amd":
            amd_name = get_amd_igpu_name()
            return NVIDIA_XRANDR_SCRIPT.format(amd_name or "modesetting")
        case _:
            return NVIDIA_XRANDR_SCRIPT.format("modesetting")


# ---------------------------------------------------------------------------
# Display Manager detection
# ---------------------------------------------------------------------------


def get_display_manager() -> str | None:
    """Detect the active display manager from systemd service symlink."""
    dm_service = Path("/etc/systemd/system/display-manager.service")
    try:
        content = dm_service.read_text(encoding="utf-8")
        match = re.search(r"ExecStart=(.+)\n", content)
        if match:
            display_manager = os.path.basename(match.group(1))
            logging.info("Found display manager: %s", display_manager)
            return display_manager
    except FileNotFoundError:
        logging.warning("Display Manager detection not available")
    return None


# ---------------------------------------------------------------------------
# initramfs rebuild (distro-aware & tool-aware)
# ---------------------------------------------------------------------------


def rebuild_initramfs() -> None:
    """Rebuild the initramfs using the appropriate tool for the current distro."""

    def _is_ostree() -> bool:
        return Path("/ostree").exists() or Path("/sysroot/ostree").exists()

    match True:
        case _ if _is_ostree() and shutil.which("rpm-ostree"):
            print("Rebuilding the initramfs with rpm-ostree...")
            command = ["rpm-ostree", "initramfs", "--enable", "--arg=--force"]
        case _ if shutil.which("mkinitcpio") and (Path("/etc/arch-release").exists() or Path("/etc/cachyos-release").exists()):
            command = ["mkinitcpio", "-P"]
        case _ if shutil.which("dracut-rebuild"):
            command = ["dracut-rebuild"]
        case _ if shutil.which("dracut"):
            command = ["dracut", "--force", "--regenerate-all"]
        case _ if shutil.which("update-initramfs"):
            command = ["update-initramfs", "-u", "-k", "all"]
        case _ if shutil.which("make-initrd"):
            command = ["make-initrd"]
        case _ if shutil.which("mkinitcpio"):
            command = ["mkinitcpio", "-P"]
        case _:
            command = []

    if shutil.which("systemd-inhibit") and command:
        command = [
            "systemd-inhibit",
            "--who=envytweaks",
            "--why", "Rebuilding initramfs",
            "--",
            *command,
        ]

    if not command:
        return

    print("Rebuilding the initramfs (protecting session shutdown)...")
    result = _run_subprocess(command)
    if result.returncode == 0:
        print("Successfully rebuilt the initramfs!")
    else:
        logging.error("An error occurred while rebuilding the initramfs")


# ---------------------------------------------------------------------------
# Root check & State management
# ---------------------------------------------------------------------------


def assert_root() -> None:
    """Exit with error if not running as root."""
    if os.geteuid() != 0:
        logging.error("This operation requires root privileges")
        sys.exit(1)


def save_current_mode(mode: str, dry_run: bool = False) -> None:
    """Persist the current mode to STATE_FILE_PATH."""
    if dry_run:
        print(f"[DRY-RUN] Would write state '{mode}' to {STATE_FILE_PATH}")
        return
    try:
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE_PATH.write_text(mode, encoding="utf-8")
    except Exception as e:
        logging.warning("Could not persist mode to %s: %e", STATE_FILE_PATH, e)


def get_current_mode() -> str:
    """Detect the current GPU mode from state file or config file heuristics."""
    if STATE_FILE_PATH.exists():
        try:
            mode = STATE_FILE_PATH.read_text(encoding="utf-8").strip()
            if mode in ("integrated", "hybrid", "nvidia"):
                return mode
        except Exception:
            pass

    from envytweaks.config import (
        BLACKLIST_PATH,
        UDEV_INTEGRATED_PATH,
        XORG_PATH,
        MODESET_PATH,
    )

    blacklist_active = BLACKLIST_PATH.exists()
    udev_integrated_active = UDEV_INTEGRATED_PATH.exists() or Path(
        "/lib/udev/rules.d/50-remove-nvidia.rules"
    ).exists()

    if blacklist_active and udev_integrated_active:
        return "integrated"
    if XORG_PATH.exists() and MODESET_PATH.exists():
        return "nvidia"
    return "hybrid"

```

## File: envytweaks-gnome/build.sh
```sh
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

```

## File: envytweaks-gnome/extension.js
```js
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Extension from 'resource:///org/gnome/shell/extensions/extension.js';

import * as TopBarView from './ui/TopBarView.js';
import * as QuickSettingsView from './ui/QuickSettingsView.js';


export default class GpuSelector extends Extension.Extension {
    enable() {
        let all_settings = this.getSettings();
        if (all_settings.get_boolean("force-topbar-view") !== true) {
            this._indicator = new QuickSettingsView.QuickSettingsIndicator(this);
            this._indicator.quickSettingsItems.push(new QuickSettingsView.QuickSettingsToggle(this));
            Main.panel.statusArea.quickSettings.addExternalIndicator(this._indicator);
        } else {
            this._indicator = new TopBarView.TopBarView(this);
            Main.panel.addToStatusArea("envytweaks", this._indicator, 1);
        }
        this._indicator.enable();
    }

    disable() {
        this._indicator.disable();
        this._indicator.destroy();
        this._indicator = null;
    }
}

```

## File: envytweaks-gnome/lib/Utility.js
```js
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';

export const EXTENSION_ICON_FILE_NAME = '/img/icon.png';

export const GPU_PROFILE_INTEGRATED = "integrated";
export const GPU_PROFILE_HYBRID = "hybrid";
export const GPU_PROFILE_NVIDIA = "nvidia";
export const GPU_PROFILE_UNKNOWN = "unknown";
export const GPU_PROFILE_NOT_INSTALLED = "not_installed";

export function getCurrentProfile() {
    if (!GLib.find_program_in_path("envytweaks")) {
        return GPU_PROFILE_NOT_INSTALLED;
    }

    try {
        let proc = new Gio.Subprocess({
            argv: ['envytweaks', '--query'],
            flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE,
        });
        proc.init(null);
        let [ok, stdout] = proc.communicate_utf8(null, null);

        if (ok && stdout) {
            const profileString = stdout.trim().toLowerCase();

            if (profileString === GPU_PROFILE_INTEGRATED ||
                profileString === GPU_PROFILE_HYBRID ||
                profileString === GPU_PROFILE_NVIDIA) {
                return profileString;
            }
        }

        return GPU_PROFILE_UNKNOWN;
    } catch (e) {
        return GPU_PROFILE_UNKNOWN;
    }
}


export function capitalizeFirstLetter(string) {
    if (!string) return "";
    return string.charAt(0).toUpperCase() + string.slice(1);
}

export function switchIntegrated(onComplete = null) {
    _execSwitch(GPU_PROFILE_INTEGRATED, [], onComplete);
}

export function switchHybrid(all_settings, onComplete = null) {
    const args = [];
    if (all_settings.get_boolean("rtd3")) {
        const rtd3Mode = all_settings.get_int("rtd3-mode");
        args.push('--rtd3', String(rtd3Mode));
    }
    _execSwitch(GPU_PROFILE_HYBRID, args, onComplete);
}

export function switchNvidia(all_settings, onComplete = null) {
    const args = [];
    if (all_settings.get_boolean("force-composition-pipeline")) {
        args.push('--force-comp');
    }
    if (all_settings.get_boolean("coolbits")) {
        args.push('--coolbits');
    }
    _execSwitch(GPU_PROFILE_NVIDIA, args, onComplete);
}

export function requestReboot() {
    let systemActions = SystemActions.getDefault();
    systemActions.activateRestart();
}

function _execSwitch(profile, args, onComplete) {
    try {
        let proc = Gio.Subprocess.new(
            ['pkexec', '/usr/bin/envytweaks', '-s', profile, ...args],
            Gio.SubprocessFlags.NONE
        );

        proc.wait_async(null, (obj, res) => {
            try {
                obj.wait_finish(res);
                let exitStatus = 0;
                if (obj.get_if_exited()) {
                    exitStatus = obj.get_exit_status();
                } else {
                    exitStatus = -1;
                }
                if (typeof onComplete === 'function') {
                    onComplete(exitStatus);
                }
            } catch (e) {
                if (typeof onComplete === 'function') {
                    onComplete(-1);
                }
            }
        });
    } catch (e) {
        if (typeof onComplete === 'function') {
            onComplete(-1);
        }
    }
}

```

## File: envytweaks-gnome/metadata.json
```json
{
  "uuid": "envytweaks@cachyos.org",
  "name": "EnvyTweaks GPU Switcher",
  "description": "A GNOME Shell extension that provides an easy way to switch between GPU profiles on Nvidia Optimus systems in just a few clicks. Powered by envytweaks.",
  "shell-version": [
    "45",
    "46",
    "47",
    "48",
    "49",
    "50"
  ],
  "settings-schema": "org.gnome.shell.extensions.envytweaks",
  "gettext-domain": "envytweaks",
  "url": "https://github.com/esfingex/envytweaks",
  "version": 2
}

```

## File: envytweaks-gnome/prefs.js
```js
import Gio from 'gi://Gio';
import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';

import {ExtensionPreferences, gettext as _} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

export default class GpuProfileSwitcherPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        // Create a preferences page, with a single group
        const page = new Adw.PreferencesPage({
            title: _('General'),
            icon_name: 'dialog-information-symbolic',
        });
        
        const group = new Adw.PreferencesGroup({
            title: _('Settings'),
            description: _('Adjust extension and GPU profile switching options'),
        });

        const row_rtd3 = new Adw.SwitchRow({
            title: _('RTD3'),
            subtitle: _('Enable PCI-Express Runtime D3 (RTD3) Power Management on Hybrid mode. When not disabled, RTD3 allows the dGPU to be dynamically turned off when not in use'),
        });

        const row_rtd3_mode = new Adw.ComboRow({
            title: _('RTD3 Power Management Mode'),
            subtitle: _('Select the level of PCI-Express Runtime D3 Power Management (default is Coarse-Grained)'),
            model: Gtk.StringList.new([
                _('0: Disabled'),
                _('1: Fine-Grained'),
                _('2: Coarse-Grained (Default)'),
                _('3: Aggressive')
            ])
        });

        const row_force_composition_pipeline = new Adw.SwitchRow({
            title: _('Force Composition Pipeline'),
            subtitle: _('Enable ForceCompositionPipeline on Nvidia mode. Use this option if facing screen tearing'),
        });

        const row_coolbits = new Adw.SwitchRow({
            title: _('Coolbits'),
            subtitle: _('Enable Coolbits, which allows overclocking on Nvidia mode (not recommended)'),
        });

        const row_force_topbar_view = new Adw.SwitchRow({
            title: _('Force Topbar View'),
            subtitle: _('Show the GPU profile selector directly in the panel/topbar instead of the Quick Settings menu'),
        });
        
        row_rtd3.bind_property('active', row_rtd3_mode, 'sensitive', GObject.BindingFlags.DEFAULT);

        group.add(row_rtd3);
        group.add(row_rtd3_mode);
        group.add(row_force_composition_pipeline);
        group.add(row_coolbits);
        group.add(row_force_topbar_view);

        page.add(group);
        
        window._settings = this.getSettings();
        window._settings.bind('rtd3', row_rtd3, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('rtd3-mode', row_rtd3_mode, 'selected', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('force-composition-pipeline', row_force_composition_pipeline, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('coolbits', row_coolbits, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('force-topbar-view', row_force_topbar_view, 'active', Gio.SettingsBindFlags.DEFAULT);
        window.add(page);
    }
}

```

## File: envytweaks-gnome/ui/QuickSettingsView.js
```js
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import GObject from 'gi://GObject';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as QuickSettings from 'resource:///org/gnome/shell/ui/quickSettings.js';

import * as Utility from '../lib/Utility.js';

export const QuickSettingsToggle = GObject.registerClass(
class QuickSettingsToggle extends QuickSettings.QuickMenuToggle {  
    _init(extensionObject) {
        this._extension = extensionObject;
        const _ = this._extension.gettext.bind(this._extension);
        
        this.activeProfile = Utility.getCurrentProfile(); // initialized profile since startup
        
        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this.chosenProfile = 'not_installed';
        } else if (this.activeProfile === Utility.GPU_PROFILE_UNKNOWN) {
            this.chosenProfile = 'unknown';
        } else {
            this.chosenProfile = this.activeProfile;
        }
        
        this.restartPending = false;
        this.doNotSwitch = false;
        
        super._init({
            title: _('GPU Profile'),
            subtitle: this.chosenProfile === 'not_installed' ? _('Not Installed') : Utility.capitalizeFirstLetter(this.chosenProfile),
            iconName: 'power-profile-performance-symbolic',
            toggleMode: false, // disable the possibility to click the button
            checked: this.activeProfile === 'hybrid' || this.activeProfile === 'nvidia',
        });
        this._all_settings = this._extension.getSettings();

        // This function is unique to this class. It adds a nice header with an icon, title and optional subtitle.
        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this.menu.setHeader('dialog-warning-symbolic', super.title, _('envytweaks is not installed!'));
        } else {
            this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Choose a GPU mode'));
        }

        // add a sections of items to the menu
        this._itemsSection = new PopupMenu.PopupMenuSection();
        
        this._integratedAction = this._itemsSection.addAction(_('Integrated') + (this.activeProfile === 'integrated' ? _(' (Active)') : ''), () => {
            if (this.chosenProfile !== 'integrated' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = _('Switching...');
                this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Switching to Integrated mode...'));
                Utility.switchIntegrated(this._onSwitchComplete.bind(this));
            }
        });
        
        this._hybridAction = this._itemsSection.addAction(_('Hybrid') + (this.activeProfile === 'hybrid' ? _(' (Active)') : ''), () => {
            if (this.chosenProfile !== 'hybrid' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = _('Switching...');
                this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Switching to Hybrid mode...'));
                Utility.switchHybrid(this._all_settings, this._onSwitchComplete.bind(this));
            }
        });
        
        this._nvidiaAction = this._itemsSection.addAction(_('Nvidia') + (this.activeProfile === 'nvidia' ? _(' (Active)') : ''), () => {
            if (this.chosenProfile !== 'nvidia' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = _('Switching...');
                this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Switching to Nvidia mode...'));
                Utility.switchNvidia(this._all_settings, this._onSwitchComplete.bind(this));
            }
        });

        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this._integratedAction.sensitive = false;
            this._hybridAction.sensitive = false;
            this._nvidiaAction.sensitive = false;
        }

        this.menu.addMenuItem(this._itemsSection);

        // Add an entry-point for more settings
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        const settingsItem = this.menu.addAction(
            _('More Settings'),
            () => this._extension.openPreferences()
        );

        // Ensure the settings are unavailable when the screen is locked
        settingsItem.visible = Main.sessionMode.allowSettings;
        this.menu._settingsActions[this._extension.uuid] = settingsItem;
    }

    _onSwitchComplete(exitStatus) {
        const _ = this._extension.gettext.bind(this._extension);
        if (exitStatus === 126) {
            // User cancelled authorization
            this.chosenProfile = Utility.getCurrentProfile();
            if (this.restartPending) {
                super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile) + '*';
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 
                    _('Restart to apply %s mode').replace('%s', Utility.capitalizeFirstLetter(this.chosenProfile)));
            } else {
                super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile);
                this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Choose a GPU mode'));
            }
            this.doNotSwitch = false;
            return;
        }

        if (exitStatus !== 0) {
            // Error occurred
            this.chosenProfile = Utility.getCurrentProfile();
            super.subtitle = _('Error');
            this.menu.setHeader('dialog-warning-symbolic', super.title, _('Switching failed (code %s)').replace('%s', exitStatus));
            this.doNotSwitch = false;
            return;
        }

        // Success
        let priorProfile = this.chosenProfile;
        this.chosenProfile = Utility.getCurrentProfile();

        if (this.activeProfile === this.chosenProfile) {
            super.subtitle = Utility.capitalizeFirstLetter(this.activeProfile);
            this.menu.setHeader('power-profile-performance-symbolic', super.title, _('Choose a GPU mode'));
            this.restartPending = false;
        } else {
            super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile) + '*';
            this.menu.setHeader('power-profile-performance-symbolic', super.title, 
                _('Restart to apply %s mode').replace('%s', Utility.capitalizeFirstLetter(this.chosenProfile)));
            Utility.requestReboot();
            this.restartPending = true;
        }
        
        this.doNotSwitch = false;
    }

});

export const QuickSettingsIndicator = GObject.registerClass(
class QuickSettingsIndicator extends QuickSettings.SystemIndicator {
    _init(extensionObject) {
        super._init();
    }

    enable() {
        this._indicator = this._addIndicator();
        this._indicator.icon_name = 'power-profile-performance-symbolic';
        this._indicator.visible = false;
    }

    disable() {
        this.quickSettingsItems.forEach(item => item.destroy());
        this._indicator.destroy();
        super.destroy();
    }
});

```

## File: envytweaks-gnome/ui/TopBarView.js
```js
import St from 'gi://St';
import GObject from 'gi://GObject';
import Gio from 'gi://Gio';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

import * as Utility from '../lib/Utility.js';

const ICON_SIZE = 6;
const ICON_INTEL_FILE_NAME = '/img/intel_icon_plain.svg';
const ICON_NVIDIA_FILE_NAME = '/img/nvidia_icon_plain.svg';
const ICON_HYBRID_FILE_NAME = '/img/hybrid_icon_plain.svg';

export const TopBarView = GObject.registerClass(
class TopBarView extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(0);
        this._all_settings = extensionObject.getSettings();
        this._extension_path = extensionObject.path;
        this._extension = extensionObject;
    }


    enable() {
        this.activeProfile = Utility.getCurrentProfile();
        this.chosenProfile = this.activeProfile === 'not_installed' ? 'not_installed' : this.activeProfile;
        this.restartPending = false;
        this.restart_menu_item = null;
        this.restart_menu_item_id = 0;

        this.icon_selector = new St.Icon({
            gicon : Gio.icon_new_for_string(this._extension_path + Utility.EXTENSION_ICON_FILE_NAME),
            style_class : 'system-status-icon',
            icon_size: ICON_SIZE
        });

        const _ = this._extension.gettext.bind(this._extension);

        this.integrated_menu_item = new PopupMenu.PopupMenuItem(_('Integrated'));
        this.integrated_menu_item_id = this.integrated_menu_item.connect('activate', () => {
            this._switchProfile('integrated');
        });

        this.hybrid_menu_item = new PopupMenu.PopupMenuItem(_('Hybrid'));
        this.hybrid_menu_item_id = this.hybrid_menu_item.connect('activate', () => {
            this._switchProfile('hybrid');
        });

        this.nvidia_menu_item = new PopupMenu.PopupMenuItem(_('Nvidia'));
        this.nvidia_menu_item_id = this.nvidia_menu_item.connect('activate', () => {
            this._switchProfile('nvidia');
        });

        this.separator_menu_item = new PopupMenu.PopupSeparatorMenuItem();
        this.menu.addMenuItem(this.separator_menu_item);
        this.menu.addMenuItem(this.integrated_menu_item);
        this.menu.addMenuItem(this.hybrid_menu_item);
        this.menu.addMenuItem(this.nvidia_menu_item);

        if (this.activeProfile === 'not_installed') {
            this.integrated_menu_item.sensitive = false;
            this.hybrid_menu_item.sensitive = false;
            this.nvidia_menu_item.sensitive = false;
            
            let warningItem = new PopupMenu.PopupMenuItem(_('envytweaks is not installed!'));
            warningItem.sensitive = false;
            this.menu.addMenuItem(warningItem, 0);
        }


        this._updateTopBarIcon();
    }

    _switchProfile(profile) {
        if (this.chosenProfile === profile || this.activeProfile === 'not_installed')
            return;

        const onComplete = (exitStatus) => {
            if (exitStatus === 126) {
                // User cancelled pkexec
                this._updateTopBarIcon();
                return;
            }
            if (exitStatus !== 0) {
                // Failure
                this._updateTopBarIcon();
                return;
            }

            // Success
            this.chosenProfile = profile;
            if (this.activeProfile === this.chosenProfile) {
                this.restartPending = false;
            } else {
                this.restartPending = true;
                Utility.requestReboot();
            }
            this._updateTopBarIcon();
        };

        if (profile === 'integrated') {
            Utility.switchIntegrated(onComplete);
        } else if (profile === 'hybrid') {
            Utility.switchHybrid(this._all_settings, onComplete);
        } else if (profile === 'nvidia') {
            Utility.switchNvidia(this._all_settings, onComplete);
        }
    }

    _updateTopBarIcon() {
        const profile = Utility.getCurrentProfile();
        
        // update chosenProfile if we are not in restartPending
        if (!this.restartPending) {
            this.chosenProfile = profile === 'not_installed' ? 'not_installed' : profile;
        }

        const profileConfig = {
            [Utility.GPU_PROFILE_INTEGRATED]: { icon: ICON_INTEL_FILE_NAME, menuItem: this.integrated_menu_item },
            [Utility.GPU_PROFILE_HYBRID]: { icon: ICON_HYBRID_FILE_NAME, menuItem: this.hybrid_menu_item },
            [Utility.GPU_PROFILE_NVIDIA]: { icon: ICON_NVIDIA_FILE_NAME, menuItem: this.nvidia_menu_item },
        };
        // Use chosenProfile for the icon check if restartPending, so it points to the target profile
        const targetProfile = this.restartPending ? this.chosenProfile : profile;
        const config = profileConfig[targetProfile];

        // Move selector icon to the active/chosen menu item
        const currentParent = this.icon_selector.get_parent();
        if (currentParent)
            currentParent.remove_child(this.icon_selector);
        if (config)
            config.menuItem.add_child(this.icon_selector);

        // Update top bar icon
        if (this.icon_top)
            this.remove_child(this.icon_top);
        
        const iconPath = this._extension_path + (config ? config.icon : Utility.EXTENSION_ICON_FILE_NAME);
        this.icon_top = new St.Icon({
            gicon: Gio.icon_new_for_string(iconPath),
            style_class: 'system-status-icon',
        });
        this.add_child(this.icon_top);

        // Update the restart required item in menu
        if (this.restartPending) {
            const _ = this._extension.gettext.bind(this._extension);
            if (!this.restart_menu_item) {
                this.restart_menu_item = new PopupMenu.PopupMenuItem(_('Restart Required*'));

                this.restart_menu_item_id = this.restart_menu_item.connect('activate', () => {
                    Utility.requestReboot();
                });
                this.menu.addMenuItem(this.restart_menu_item, 0);
            }
        } else {
            if (this.restart_menu_item) {
                this.restart_menu_item.disconnect(this.restart_menu_item_id);
                this.restart_menu_item.destroy();
                this.restart_menu_item = null;
                this.restart_menu_item_id = 0;
            }
        }
    }

    disable() {
        if (this.integrated_menu_item_id) {
            this.integrated_menu_item.disconnect(this.integrated_menu_item_id);
            this.integrated_menu_item_id = 0;
        }
        this.integrated_menu_item.destroy();
        this.integrated_menu_item = null;

        if (this.hybrid_menu_item_id) {
            this.hybrid_menu_item.disconnect(this.hybrid_menu_item_id);
            this.hybrid_menu_item_id = 0;
        }
        this.hybrid_menu_item.destroy();
        this.hybrid_menu_item = null;

        if (this.nvidia_menu_item_id) {
            this.nvidia_menu_item.disconnect(this.nvidia_menu_item_id);
            this.nvidia_menu_item_id = 0;
        }
        this.nvidia_menu_item.destroy();
        this.nvidia_menu_item = null;

        if (this.restart_menu_item) {
            this.restart_menu_item.disconnect(this.restart_menu_item_id);
            this.restart_menu_item.destroy();
            this.restart_menu_item = null;
            this.restart_menu_item_id = 0;
        }

        this.separator_menu_item.destroy();
        this.separator_menu_item = null;

        this.icon_selector = null;
    }
});

```

## File: envytweaks-kde/metadata.json
```json
{
    "KPlugin": {
        "Authors": [
            {
                "Email": "eniel160990@gmail.com",
                "Name": "Eniel"
            }
        ],
        "Category": "Hardware",
        "Description": "GUI for the EnvyTweaks tool, intended for switching between GPU modes on Nvidia Optimus systems.",
        "Description[es]": "Interfaz gráfica para la herramienta EnvyTweaks, destinada a cambiar entre los modos de GPU en los sistemas Nvidia Optimus.",

        "EnabledByDefault": true,
        "Icon": "video-card-inactive",
        "Id": "optimus-gpu-switcher",
        "License": "GPL3",
        "Name": "Optimus GPU Switcher",
        "Version": "1.0.3",
        "Website": ""
    },
    "KPackageStructure": "Plasma/Applet",
    "X-Plasma-API-Minimum-Version": "6.0",
    "X-Plasma-NotificationAreaCategory": "Hardware"
}

```

## File: install.sh
```sh
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

```

