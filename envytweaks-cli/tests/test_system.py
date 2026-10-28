"""Tests for state persistence and logging."""

import logging

from envytweaks import system


def test_save_current_mode_logs_readable_error(monkeypatch, tmp_path, caplog) -> None:
    # A directory makes write_text() fail with IsADirectoryError.
    state_path = tmp_path / "current_mode"
    state_path.mkdir()
    monkeypatch.setattr(system, "STATE_FILE_PATH", state_path)

    with caplog.at_level(logging.WARNING):
        system.save_current_mode("hybrid")

    assert "Could not persist mode" in caplog.text


def test_get_current_mode_reads_state_file(monkeypatch, tmp_path) -> None:
    state_path = tmp_path / "current_mode"
    state_path.write_text("nvidia", encoding="utf-8")
    monkeypatch.setattr(system, "STATE_FILE_PATH", state_path)

    assert system.get_current_mode() == "nvidia"


def test_clear_current_mode_removes_state_file(monkeypatch, tmp_path) -> None:
    state_dir = tmp_path / "envytweaks"
    state_dir.mkdir()
    state_path = state_dir / "current_mode"
    state_path.write_text("hybrid", encoding="utf-8")
    monkeypatch.setattr(system, "STATE_FILE_PATH", state_path)

    system.clear_current_mode()

    assert not state_path.exists()
    assert not state_dir.exists()


def test_clear_current_mode_dry_run_keeps_state(monkeypatch, tmp_path, capsys) -> None:
    state_path = tmp_path / "current_mode"
    state_path.write_text("hybrid", encoding="utf-8")
    monkeypatch.setattr(system, "STATE_FILE_PATH", state_path)

    system.clear_current_mode(dry_run=True)

    assert state_path.exists()
    assert "Would remove state file" in capsys.readouterr().out
