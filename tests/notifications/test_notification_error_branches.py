"""Error and edge branch coverage for NotificationHandler."""


import pytest
from pickleball_notifier.notifications.handler import NotificationHandler

from shared.helpers import DummyResponse, build_match


class DummyConfigManager:
    def get_pending_notifications(self):
        return []

    def mark_as_notified(self, _uuid: str) -> None:
        return None

    def save_config(self) -> None:
        return None

    def get_court_assigned_matches(self):
        return []


def _build_handler(monkeypatch) -> NotificationHandler:
    monkeypatch.setattr(NotificationHandler, "_load_bot_id", lambda self: "bot-123")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    return NotificationHandler(DummyConfigManager())


def test_send_notification_success_path(monkeypatch) -> None:
    handler = _build_handler(monkeypatch)
    monkeypatch.setattr(handler, "_create_notification_message", lambda _m: "ok")
    monkeypatch.setattr(handler.session, "post", lambda *args, **kwargs: DummyResponse(payload={}))

    assert handler.send_notification(build_match()) is True


def test_send_notification_unexpected_error_path(monkeypatch) -> None:
    handler = _build_handler(monkeypatch)
    monkeypatch.setattr(handler, "_create_notification_message", lambda _m: (_ for _ in ()).throw(RuntimeError("bad")))

    assert handler.send_notification(build_match()) is False


def test_process_pending_notifications_empty(monkeypatch) -> None:
    handler = _build_handler(monkeypatch)
    assert handler.process_pending_notifications() == 0


def test_build_player_info_exactly_two_opponents(monkeypatch) -> None:
    handler = _build_handler(monkeypatch)
    info = handler._build_player_info_string(build_match(opponent_names=["A", "B"]))
    assert "vs A & B" in info


def test_load_methods_handle_invalid_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text("{bad", encoding="utf-8")
    handler = NotificationHandler.__new__(NotificationHandler)

    with pytest.raises(ValueError):
        handler._load_bot_id()

    with pytest.raises(ValueError):
        handler._load_player_slug()

