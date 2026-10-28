"""Tests for the PCI bus cache and its interaction with the switcher."""

import json
from types import SimpleNamespace

from envytweaks import cache as cache_mod
from envytweaks import switcher, system
from envytweaks.cache import CachedConfig


def _cache_file(tmp_path, bus: str = "PCI:1:0:0"):
    path = tmp_path / "cache.json"
    path.write_text(json.dumps({"nvidia_gpu_pci_bus": bus}), encoding="utf-8")
    return path


def test_delete_cache_file_dry_run_keeps_file(monkeypatch, tmp_path) -> None:
    path = _cache_file(tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE_PATH", path)

    CachedConfig.delete_cache_file(dry_run=True)

    assert path.exists()


def test_delete_cache_file_removes_file(monkeypatch, tmp_path) -> None:
    path = _cache_file(tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE_PATH", path)

    CachedConfig.delete_cache_file()

    assert not path.exists()


def test_adapter_uses_cached_bus(monkeypatch, tmp_path) -> None:
    path = _cache_file(tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE_PATH", path)
    monkeypatch.setattr(cache_mod, "get_current_mode", lambda: "nvidia")

    def fail() -> str:
        raise AssertionError("lspci must not be called when a cache exists")

    monkeypatch.setattr(system, "get_nvidia_gpu_pci_bus", fail)

    cached = CachedConfig(SimpleNamespace(dry_run=False))
    with cached.adapter():
        assert system.get_nvidia_gpu_pci_bus() == "PCI:1:0:0"

    assert system.get_nvidia_gpu_pci_bus is fail


def test_switcher_uses_cached_bus(monkeypatch, tmp_path) -> None:
    path = _cache_file(tmp_path)
    monkeypatch.setattr(cache_mod, "CACHE_FILE_PATH", path)
    monkeypatch.setattr(cache_mod, "get_current_mode", lambda: "nvidia")

    def fail() -> str:
        raise AssertionError("lspci must not be called when a cache exists")

    monkeypatch.setattr(system, "get_nvidia_gpu_pci_bus", fail)

    written: dict = {}
    monkeypatch.setattr(switcher, "cleanup", lambda **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "_run_subprocess",
        lambda cmd: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(switcher, "rebuild_initramfs", lambda: None)
    monkeypatch.setattr(switcher, "save_current_mode", lambda *args, **kwargs: None)
    monkeypatch.setattr(switcher, "get_igpu_vendor", lambda: "intel")
    monkeypatch.setattr(switcher, "get_display_manager", lambda: None)
    monkeypatch.setattr(
        switcher,
        "create_file",
        lambda target, content, **kwargs: written.__setitem__(target, content) or True,
    )

    cached = CachedConfig(SimpleNamespace(dry_run=False))
    with cached.adapter():
        switcher.graphics_mode_switcher(
            "nvidia", None, False, None, None, False
        )

    assert 'BusID "PCI:1:0:0"' in written[switcher.XORG_PATH]
