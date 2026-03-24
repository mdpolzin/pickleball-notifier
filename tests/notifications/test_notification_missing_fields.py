"""Coverage for missing field branches in notification config loading."""

import json

import pytest
from pickleball_notifier.notifications.handler import NotificationHandler


def test_load_bot_id_missing_field_raises_runtime_error(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"player": {"slug": "jane-doe"}}), encoding="utf-8")
    handler = NotificationHandler.__new__(NotificationHandler)

    with pytest.raises(RuntimeError):
        handler._load_bot_id()


def test_load_player_slug_missing_file_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    handler = NotificationHandler.__new__(NotificationHandler)

    with pytest.raises(FileNotFoundError):
        handler._load_player_slug()

