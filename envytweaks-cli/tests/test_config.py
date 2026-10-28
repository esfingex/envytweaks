"""Tests for config file helpers that do not touch the real system."""

import stat

import pytest
from envytweaks import config


def test_create_file_dry_run_does_not_write(tmp_path, capsys) -> None:
    target = tmp_path / "generated.conf"

    config.create_file(target, "content\n", dry_run=True)

    assert not target.exists()
    assert "[DRY-RUN] Would create" in capsys.readouterr().out


def test_create_file_executable_sets_exec_bit(tmp_path) -> None:
    target = tmp_path / "script.sh"

    config.create_file(target, "#!/bin/sh\n", executable=True)

    assert target.read_text(encoding="utf-8") == "#!/bin/sh\n"
    assert target.stat().st_mode & stat.S_IXUSR


def test_create_file_returns_false_on_write_error(tmp_path) -> None:
    target = tmp_path / "directory"
    target.mkdir()

    assert config.create_file(target, "content\n") is False


def test_create_file_backs_up_user_file(tmp_path) -> None:
    target = tmp_path / "xorg.conf"
    target.write_text("user config\n", encoding="utf-8")

    assert config.create_file(target, "# generated\n") is True

    assert target.read_text(encoding="utf-8") == "# generated\n"
    backup = config.backup_path(target)
    assert backup.read_text(encoding="utf-8") == "user config\n"


def test_create_file_refuses_when_backup_already_exists(tmp_path) -> None:
    target = tmp_path / "xorg.conf"
    target.write_text("user config\n", encoding="utf-8")
    config.backup_path(target).write_text("older config\n", encoding="utf-8")

    assert config.create_file(target, "# generated\n") is False

    assert target.read_text(encoding="utf-8") == "user config\n"
    assert config.backup_path(target).read_text(encoding="utf-8") == "older config\n"


def test_create_file_overwrites_generated_file_without_backup(tmp_path) -> None:
    target = tmp_path / "xorg.conf"
    target.write_text(f"# {config.GENERATED_MARKER}\nold\n", encoding="utf-8")

    assert config.create_file(target, "# generated\n") is True

    assert target.read_text(encoding="utf-8") == "# generated\n"
    assert not config.backup_path(target).exists()


def test_create_file_dry_run_reports_backup_without_writing(tmp_path, capsys) -> None:
    target = tmp_path / "xorg.conf"
    target.write_text("user config\n", encoding="utf-8")

    assert config.create_file(target, "# generated\n", dry_run=True) is True

    assert target.read_text(encoding="utf-8") == "user config\n"
    assert not config.backup_path(target).exists()
    assert "Would back up" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (f"# {config.GENERATED_MARKER}\noptions nvidia-drm modeset=1\n", True),
        ("# user-managed file\n", False),
    ],
)
def test_is_generated_file(tmp_path, content: str, expected: bool) -> None:
    target = tmp_path / "file.conf"
    target.write_text(content, encoding="utf-8")

    assert config.is_generated_file(target) is expected


def test_is_generated_file_missing_path_is_false(tmp_path) -> None:
    assert config.is_generated_file(tmp_path / "missing.conf") is False
