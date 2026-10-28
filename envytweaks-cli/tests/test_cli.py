"""Tests for CLI flag wiring that must not touch the real system."""

import sys

from envytweaks import cli as cli_mod


def test_cache_delete_dry_run_forwards_flag(monkeypatch) -> None:
    called: dict = {}
    monkeypatch.setattr(
        cli_mod.CachedConfig,
        "delete_cache_file",
        staticmethod(lambda dry_run=False: called.update(dry_run=dry_run)),
    )
    monkeypatch.setattr(sys, "argv", ["envytweaks", "--cache-delete", "--dry-run"])

    cli_mod.main()

    assert called == {"dry_run": True}


def test_reset_sddm_dry_run_forwards_flag(monkeypatch) -> None:
    called: dict = {}
    monkeypatch.setattr(
        cli_mod,
        "reset_sddm_xsetup",
        lambda dry_run=False: called.update(dry_run=dry_run),
    )
    monkeypatch.setattr(sys, "argv", ["envytweaks", "--reset-sddm", "--dry-run"])

    cli_mod.main()

    assert called == {"dry_run": True}


def test_reset_dry_run_forwards_flags_and_restores_backups(monkeypatch) -> None:
    called: dict = {}
    monkeypatch.setattr(
        cli_mod,
        "cleanup",
        lambda dry_run=False, restore_backups=False: called.update(
            cleanup=(dry_run, restore_backups)
        ),
    )
    monkeypatch.setattr(
        cli_mod,
        "clear_current_mode",
        lambda dry_run=False: called.update(clear_state=dry_run),
    )
    monkeypatch.setattr(
        cli_mod.CachedConfig,
        "delete_cache_file",
        staticmethod(lambda dry_run=False: called.update(cache=dry_run)),
    )
    monkeypatch.setattr(cli_mod, "rebuild_initramfs", lambda: called.update(rebuilt=True))
    monkeypatch.setattr(sys, "argv", ["envytweaks", "--reset", "--dry-run"])

    cli_mod.main()

    assert called == {
        "cleanup": (True, True),
        "clear_state": True,
        "cache": True,
    }
