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
