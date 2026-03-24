"""Tests for NotificationHandler config loading branches."""

import json

import pytest
from pickleball_notifier.notifications.handler import NotificationHandler


def _make_handler() -> NotificationHandler:
    """Create handler instance without running __init__ side effects."""
    return NotificationHandler.__new__(NotificationHandler)


def test_load_bot_id_success(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"groupme": {"bot_id": "bot-1"}, "player": {"slug": "jane-doe"}}),
        encoding="utf-8",
    )
    handler = _make_handler()

    assert handler._load_bot_id() == "bot-1"


def test_load_bot_id_missing_file_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    handler = _make_handler()

    with pytest.raises(FileNotFoundError):
        handler._load_bot_id()


def test_load_player_slug_success(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"groupme": {"bot_id": "bot-1"}, "player": {"slug": "jane-doe"}}),
        encoding="utf-8",
    )
    handler = _make_handler()

    assert handler._load_player_slug() == "jane-doe"


def test_load_player_slug_missing_field_raises_runtime_error(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"groupme": {"bot_id": "bot-1"}}), encoding="utf-8")
    handler = _make_handler()

    with pytest.raises(RuntimeError):
        handler._load_player_slug()

