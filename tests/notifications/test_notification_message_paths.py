"""Additional message and error-path tests for NotificationHandler."""

from pickleball_notifier.notifications.handler import NotificationHandler

from shared.helpers import build_match


class DummyConfigManager:
    def get_pending_notifications(self):
        return []

    def mark_as_notified(self, _uuid: str) -> None:
        return None

    def save_config(self) -> None:
        return None

    def get_court_assigned_matches(self):
        return []


def build_handler(monkeypatch) -> NotificationHandler:
    monkeypatch.setattr(NotificationHandler, "_load_bot_id", lambda self: "bot-123")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    return NotificationHandler(DummyConfigManager())


def test_create_message_uses_pickleball_tv_fallback(monkeypatch) -> None:
    handler = build_handler(monkeypatch)
    match = build_match(court_title="SC1")
    monkeypatch.setattr(handler.stream_checker, "check_court_stream", lambda _court: {"is_live": False, "stream_url": None, "error": None})
    monkeypatch.setattr(handler.stream_checker, "get_pickleball_tv_message", lambda _court: " (tv)")

    message = handler._create_notification_message(match)

    assert message.endswith(" (tv)")


def test_create_message_handles_youtube_exception(monkeypatch) -> None:
    handler = build_handler(monkeypatch)
    match = build_match(court_title="SC1")
    monkeypatch.setattr(handler.stream_checker, "check_court_stream", lambda _court: (_ for _ in ()).throw(RuntimeError("boom")))

    message = handler._create_notification_message(match)

    assert "Court SC1" in message


def test_build_player_info_handles_multiple_opponents(monkeypatch) -> None:
    handler = build_handler(monkeypatch)
    match = build_match(partner_name="Partner", opponent_names=["Opp A", "Opp B", "Opp C"])

    info = handler._build_player_info_string(match)

    assert "Partner: Partner" in info
    assert "vs Opp A, Opp B & Opp C" in info

