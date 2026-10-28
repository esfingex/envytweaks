"""Tests for the SDDM Xsetup backup/restore flow."""

import stat
from types import SimpleNamespace

from envytweaks import config, switcher, system


def _patch_paths(monkeypatch, tmp_path):
    xsetup = tmp_path / "Xsetup"
    backup = tmp_path / "Xsetup.envytweaks.bak"
    monkeypatch.setattr(config, "SDDM_XSETUP_PATH", xsetup)
    monkeypatch.setattr(config, "SDDM_XSETUP_BACKUP_PATH", backup)
    return xsetup, backup


def test_restore_backup_recovers_original_and_removes_backup(monkeypatch, tmp_path) -> None:
    xsetup, backup = _patch_paths(monkeypatch, tmp_path)
    xsetup.write_text(f"# {config.GENERATED_MARKER}\n", encoding="utf-8")
    backup.write_text("original script\n", encoding="utf-8")

    assert config.restore_sddm_xsetup() is True

    assert xsetup.read_text(encoding="utf-8") == "original script\n"
    assert xsetup.stat().st_mode & stat.S_IXUSR
    assert not backup.exists()


def test_restore_dry_run_keeps_backup(monkeypatch, tmp_path, capsys) -> None:
    xsetup, backup = _patch_paths(monkeypatch, tmp_path)
    xsetup.write_text(f"# {config.GENERATED_MARKER}\n", encoding="utf-8")
    backup.write_text("original script\n", encoding="utf-8")

    assert config.restore_sddm_xsetup(dry_run=True) is True

    assert backup.exists()
    assert config.is_generated_file(xsetup)
    assert "Would restore Xsetup backup" in capsys.readouterr().out


def test_restore_failure_keeps_backup(monkeypatch, tmp_path) -> None:
    _xsetup, backup = _patch_paths(monkeypatch, tmp_path)
    backup.write_text("original script\n", encoding="utf-8")
    monkeypatch.setattr(config, "create_file", lambda *args, **kwargs: False)

    assert config.restore_sddm_xsetup() is True

    assert backup.exists()


def test_reset_without_backup_writes_default(monkeypatch, tmp_path) -> None:
    xsetup, _backup = _patch_paths(monkeypatch, tmp_path)

    config.reset_sddm_xsetup()

    assert xsetup.read_text(encoding="utf-8") == config.SDDM_XSETUP_CONTENT
    assert xsetup.stat().st_mode & stat.S_IXUSR


def test_restore_without_backup_returns_false(monkeypatch, tmp_path) -> None:
    _xsetup, _backup = _patch_paths(monkeypatch, tmp_path)

    assert config.restore_sddm_xsetup() is False


def test_reset_without_backup_keeps_unmanaged_xsetup(monkeypatch, tmp_path) -> None:
    xsetup, _backup = _patch_paths(monkeypatch, tmp_path)
    xsetup.write_text("user script\n", encoding="utf-8")

    config.reset_sddm_xsetup()

    assert xsetup.read_text(encoding="utf-8") == "user script\n"


def test_reset_skips_when_sddm_is_not_installed(monkeypatch, tmp_path) -> None:
    xsetup = tmp_path / "missing-sddm" / "Xsetup"
    monkeypatch.setattr(config, "SDDM_XSETUP_PATH", xsetup)
    monkeypatch.setattr(config, "SDDM_XSETUP_BACKUP_PATH", config.backup_path(xsetup))

    config.reset_sddm_xsetup()

    assert not xsetup.exists()


def test_nvidia_sddm_writes_generated_script_to_xsetup(monkeypatch, tmp_path) -> None:
    xsetup = tmp_path / "Xsetup"
    xsetup.write_text("original script\n", encoding="utf-8")

    monkeypatch.setattr(switcher, "SDDM_XSETUP_PATH", xsetup)
    monkeypatch.setattr(switcher, "cleanup", lambda **kwargs: None)
    monkeypatch.setattr(
        switcher,
        "_run_subprocess",
        lambda cmd: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(switcher, "rebuild_initramfs", lambda: None)
    monkeypatch.setattr(switcher, "save_current_mode", lambda *args, **kwargs: None)
    monkeypatch.setattr(switcher, "get_igpu_vendor", lambda: "intel")
    monkeypatch.setattr(system, "get_nvidia_gpu_pci_bus", lambda: "PCI:1:0:0")

    written: dict = {}
    monkeypatch.setattr(
        switcher,
        "create_file",
        lambda target, content, **kwargs: written.__setitem__(target, content) or True,
    )

    switcher.graphics_mode_switcher("nvidia", "sddm", False, None, None, False)

    assert "xrandr --setprovideroutputsource" in written[xsetup]
    assert not (tmp_path / "Xsetup.sh.bak").exists()

