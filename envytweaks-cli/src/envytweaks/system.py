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
        return None  # FIX: was missing — caused UnboundLocalError in envycontrol

    pattern = re.compile(r"(name:).*(ATI*|AMD*|AMD\/ATI)*")
    if pattern.findall(xrandr_output):
        return re.search(pattern, xrandr_output).group(0)[5:]  # type: ignore[union-attr]

    logging.warning("Could not find AMD iGPU in xrandr output")
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
# initramfs rebuild (distro-aware)
# ---------------------------------------------------------------------------


def rebuild_initramfs() -> None:
    """Rebuild the initramfs using the appropriate tool for the current distro."""

    def _is_ostree() -> bool:
        return Path("/ostree").exists() or Path("/sysroot/ostree").exists()

    match True:
        case _ if _is_ostree():
            print("Rebuilding the initramfs with rpm-ostree...")
            command = ["rpm-ostree", "initramfs", "--enable", "--arg=--force"]
        case _ if Path("/etc/debian_version").exists():
            command = ["update-initramfs", "-u", "-k", "all"]
        case _ if (
            Path("/etc/redhat-release").exists()
            or Path("/usr/bin/zypper").exists()
        ):
            command = ["dracut", "--force", "--regenerate-all"]
        case _ if (
            Path("/usr/lib/endeavouros-release").exists()
            and Path("/usr/bin/dracut").exists()
        ):
            command = ["dracut-rebuild"]
        case _ if Path("/etc/altlinux-release").exists():
            command = ["make-initrd"]
        case _ if Path("/etc/arch-release").exists():
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

    print("Rebuilding the initramfs...")
    result = _run_subprocess(command)
    if result.returncode == 0:
        print("Successfully rebuilt the initramfs!")
    else:
        logging.error("An error occurred while rebuilding the initramfs")


# ---------------------------------------------------------------------------
# Root check
# ---------------------------------------------------------------------------


def assert_root() -> None:
    """Exit with error if not running as root."""
    if os.geteuid() != 0:
        logging.error("This operation requires root privileges")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Current mode detection
# ---------------------------------------------------------------------------


def get_current_mode() -> str:
    """Detect the current GPU mode by checking which config files are present."""
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
