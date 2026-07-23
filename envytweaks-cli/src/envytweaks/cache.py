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


