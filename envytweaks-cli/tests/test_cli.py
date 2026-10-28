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
