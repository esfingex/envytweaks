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
