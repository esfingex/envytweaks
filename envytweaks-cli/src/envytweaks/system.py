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
