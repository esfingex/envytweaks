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
