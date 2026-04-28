"""Unit tests for notification handling behavior."""

import requests
from pickleball_notifier.notifications.handler import NotificationHandler

from shared.helpers import DummyResponse, build_match


class DummyConfigManager:
    """Small config manager stub for notification tests."""

    def __init__(self, pending=None, court_assigned=None):
        self.pending = pending or []
        self.court_assigned = court_assigned or self.pending
        self.marked = []
        self.completion_marked = []
        self.saved = False

    def get_pending_notifications(self):
        return self.pending

    def get_pending_completion_notifications(self):
        return []

    def mark_as_notified(self, uuid: str) -> None:
        self.marked.append(uuid)

    def mark_completion_notified(self, uuid: str) -> None:
        self.completion_marked.append(uuid)

    def save_config(self) -> None:
        self.saved = True

    def get_court_assigned_matches(self):
        return self.court_assigned


def build_handler(monkeypatch, config_manager: DummyConfigManager) -> NotificationHandler:
    """Build handler with config/file reads disabled."""
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub-123")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok-123")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    return NotificationHandler(config_manager)


def test_send_notification_posts_user_messages_endpoint(monkeypatch) -> None:
    config = DummyConfigManager()
    handler = build_handler(monkeypatch, config)
    match = build_match()
    last: dict = {}

    def capture_post(url, **kwargs):
        last["url"] = url
        last["params"] = kwargs.get("params")
        last["json"] = kwargs.get("json")
        return DummyResponse(payload={})

    monkeypatch.setattr(handler, "_create_notification_message", lambda _m: "hello")
    monkeypatch.setattr(handler.session, "post", capture_post)

    assert handler.send_notification(match) is True
    assert last["url"] == "https://api.groupme.com/v3/groups/sub-123/messages"
    assert last["params"] == {"token": "tok-123"}
    assert last["json"]["message"]["text"] == "hello"
    assert len(last["json"]["message"]["source_guid"]) > 8


def test_create_message_includes_live_stream_and_pickleball_link(monkeypatch) -> None:
    config = DummyConfigManager()
    handler = build_handler(monkeypatch, config)
    match = build_match(opponent_names=["Opponent A"])
    monkeypatch.setattr(
        handler.stream_checker,
        "check_court_stream",
        lambda _court: {"is_live": True, "stream_url": "https://yt", "error": None},
    )

    message = handler._create_notification_message(match)

    assert "LIVE STREAM: https://yt" in message
    assert "vs Opponent A" in message
    assert f"🔗 Match URL: {match.url}" in message


def test_create_message_includes_pickleball_link_without_live_stream(monkeypatch) -> None:
    handler = build_handler(monkeypatch, DummyConfigManager())
    match = build_match(uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", court_title="SC1")
    monkeypatch.setattr(
        handler.stream_checker,
        "check_court_stream",
        lambda _court: {"is_live": False, "stream_url": None, "error": None},
    )
    monkeypatch.setattr(handler.stream_checker, "get_pickleball_tv_message", lambda _ct: "")
    msg = handler._create_notification_message(match)
    assert msg.strip().split("\n")[-1] == f"🔗 Match URL: {match.url}"


def test_send_notification_handles_request_exception(monkeypatch) -> None:
    config = DummyConfigManager()
    handler = build_handler(monkeypatch, config)
    match = build_match()
    monkeypatch.setattr(handler, "_create_notification_message", lambda _m: "hello")
    monkeypatch.setattr(
        handler.session,
        "post",
        lambda *args, **kwargs: DummyResponse(raise_error=requests.RequestException("boom")),
    )

    assert handler.send_notification(match) is False


def test_process_pending_notifications_marks_and_saves(monkeypatch) -> None:
    matches = [
        build_match(uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        build_match(uuid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    ]
    config = DummyConfigManager(pending=matches)
    handler = build_handler(monkeypatch, config)
    monkeypatch.setattr(handler, "send_notification", lambda _m: True)

    sent_count = handler.process_pending_notifications()

    assert sent_count == 2
    assert set(config.marked) == {
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    }
    assert config.saved is True


def test_notification_summary_counts_notified(monkeypatch) -> None:
    court_assigned = [
        build_match(uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", notified=True),
        build_match(uuid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", notified=False),
        build_match(uuid="cccccccc-cccc-cccc-cccc-cccccccccccc", notified=False),
    ]
    pending = [
        build_match(uuid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", notified=False),
        build_match(uuid="cccccccc-cccc-cccc-cccc-cccccccccccc", notified=False),
    ]
    config = DummyConfigManager(pending=pending, court_assigned=court_assigned)
    handler = build_handler(monkeypatch, config)

    summary = handler.get_notification_summary()

    assert summary["total_court_assigned"] == 3
    assert summary["pending_notifications"] == 2
    assert summary["notifications_sent"] == 1
    assert summary["pending_completion_notifications"] == 0
    assert summary["completion_notifications_sent"] == 0
