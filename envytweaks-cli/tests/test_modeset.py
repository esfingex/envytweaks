"""Tests for modprobe/RTD3 content generation and the hybrid switch path."""

from types import SimpleNamespace

import pytest
from envytweaks import switcher
from envytweaks.config import (
    MODESET_PATH,
    UDEV_PM_PATH,
    build_modeset_content,
    build_modeset_rtd3,
)


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_build_modeset_rtd3_uses_requested_level(level: int) -> None:
    content = build_modeset_rtd3(level)
    assert f'NVreg_DynamicPowerManagement=0x0{level}' in content


def test_build_modeset_content_without_rtd3_has_no_power_option() -> None:
    content = build_modeset_content("nvidia")
    assert "NVreg_DynamicPowerManagement" not in content
    assert "options nvidia-drm modeset=1" in content


def _patch_hybrid(monkeypatch, written: dict) -> None:
    monkeypatch.setattr(switcher, "cleanup", lambda **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "_run_subprocess",
        lambda cmd: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(switcher, "rebuild_initramfs", lambda: None)
    monkeypatch.setattr(switcher, "save_current_mode", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "create_file",
        lambda path, content, **kwargs: written.__setitem__(path, content) or True,
    )


def test_hybrid_switch_writes_selected_rtd3(monkeypatch) -> None:
    written: dict = {}
    _patch_hybrid(monkeypatch, written)

    assert switcher.graphics_mode_switcher(
        "hybrid", None, False, None, 3, False
    ) is True

    assert 'NVreg_DynamicPowerManagement=0x03' in written[MODESET_PATH]
    assert UDEV_PM_PATH in written


def test_hybrid_switch_aborts_when_write_fails(monkeypatch) -> None:
    called = {"rebuild": False, "save": False}
    monkeypatch.setattr(switcher, "cleanup", lambda **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "_run_subprocess",
        lambda cmd: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        switcher, "rebuild_initramfs", lambda: called.update(rebuild=True)
    )
    monkeypatch.setattr(
        switcher, "save_current_mode", lambda *args, **kwargs: called.update(save=True)
    )
    monkeypatch.setattr(switcher, "create_file", lambda *args, **kwargs: False)

    assert switcher.graphics_mode_switcher(
        "hybrid", None, False, None, 2, False
    ) is False
    assert called == {"rebuild": False, "save": False}


def test_nvidia_switch_aborts_when_write_fails(monkeypatch) -> None:
    called = {"rebuild": False, "save": False}
    monkeypatch.setattr(switcher, "cleanup", lambda **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "_run_subprocess",
        lambda cmd: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        switcher, "rebuild_initramfs", lambda: called.update(rebuild=True)
    )
    monkeypatch.setattr(
        switcher, "save_current_mode", lambda *args, **kwargs: called.update(save=True)
    )
    monkeypatch.setattr(switcher, "get_igpu_vendor", lambda: "intel")
    monkeypatch.setattr(switcher, "get_display_manager", lambda: None)
    monkeypatch.setattr(switcher.system, "get_nvidia_gpu_pci_bus", lambda: "PCI:1:0:0")
    monkeypatch.setattr(switcher, "create_file", lambda *args, **kwargs: False)

    assert switcher.graphics_mode_switcher(
        "nvidia", None, False, None, None, False
    ) is False
    assert called == {"rebuild": False, "save": False}


def test_hybrid_switch_with_rtd3_zero_disables_power_rules(monkeypatch) -> None:
    written: dict = {}
    _patch_hybrid(monkeypatch, written)

    switcher.graphics_mode_switcher(
        "hybrid", None, False, None, 0, False
    )

    assert "NVreg_DynamicPowerManagement" not in written[MODESET_PATH]
    assert UDEV_PM_PATH not in written


def test_hybrid_switch_uses_nvidia_current_driver(monkeypatch) -> None:
    written: dict = {}
    _patch_hybrid(monkeypatch, written)

    switcher.graphics_mode_switcher(
        "hybrid", None, False, None, 2, True
    )

    assert "options nvidia-current-drm modeset=1" in written[MODESET_PATH]
    assert 'options nvidia-current "NVreg_DynamicPowerManagement=0x02"' in written[MODESET_PATH]
