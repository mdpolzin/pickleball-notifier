"""Tests for match completion / result messaging."""

import requests
from pickleball_notifier.notifications.handler import NotificationHandler

from shared.helpers import DummyResponse, build_match


class DummyCm:
    def get_pending_completion_notifications(self):
        return []

    def mark_completion_notified(self, *_a):
        return None

    def save_config(self):
        return None


def test_create_match_result_message_includes_partner_and_scores(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "s")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "t")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "alex-smith")

    cm = DummyCm()
    handler = NotificationHandler(cm)
    pb_url = "https://pickleball.com/results/match/sample-u-u-i-d"
    m = build_match(
        uuid="sample-u-u-i-d",
        court_title="SC9",
        match_completed="2026-01-02T00:00:00Z",
        partner_name="Pat",
        opponent_names=["Taylor", "Jordan"],
        player_won=True,
        game_score_lines=["Game 1: 11-9", "Game 2: 13-11"],
        url=pb_url,
    )
    msg = handler._create_match_result_message(m)
    assert "Court SC9" in msg
    assert "Alex Smith" in msg
    assert "Won" in msg
    assert "Score by game" in msg
    assert "Game 1: 11-9" in msg
    assert pb_url in msg
    assert "Taylor" in msg
    assert "Completed" not in msg


def test_create_match_result_message_shows_loss(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "s")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "t")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "alex-smith")

    handler = NotificationHandler(DummyCm())
    m = build_match(
        match_completed="2026-01-02T03:04:05Z",
        player_won=False,
        game_score_lines=["Game 1: 11-9"],
    )
    msg = handler._create_match_result_message(m)
    assert "Lost" in msg
    assert "11-9" in msg


def test_process_pending_completion_marks_saved(monkeypatch) -> None:
    class Cmdone:
        def __init__(self):
            self.marked = []
            self.saved = False

        def get_pending_completion_notifications(self):
            return [
                build_match(
                    uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    match_completed="final",
                    completion_notified=False,
                )
            ]

        def mark_completion_notified(self, uid):
            self.marked.append(uid)

        def save_config(self):
            self.saved = True

    cm = Cmdone()
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(cm)
    monkeypatch.setattr(handler, "send_match_result_notification", lambda _m: True)

    n = handler.process_pending_completion_notifications()

    assert n == 1
    assert cm.marked == ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]
    assert cm.saved is True


class OkResp:
    """Minimal response for successful GroupMe post."""

    status_code = 201

    def raise_for_status(self) -> None:
        return None

    def json(self):  # noqa: ANN001 — mirrors requests.Response
        return {}


def test_send_match_result_post_success(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(DummyCm())
    monkeypatch.setattr(handler.session, "post", lambda *a, **kw: OkResp())

    ok = handler.send_match_result_notification(
        build_match(match_completed="Winner: team A", court_title="C1")
    )
    assert ok is True


def test_send_match_result_post_failure(monkeypatch) -> None:
    cm = DummyCm()
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(cm)
    monkeypatch.setattr(
        handler.session,
        "post",
        lambda *a, **kw: DummyResponse(raise_error=requests.RequestException("down")),
    )

    ok = handler.send_match_result_notification(
        build_match(match_completed="x")
    )
    assert ok is False


def test_post_groupme_raises_non_request_exception(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(DummyCm())

    def boom(*_a, **_kw):
        raise ValueError("boom")

    monkeypatch.setattr(handler.session, "post", boom)

    assert handler._post_groupme_message("hi", "uuid-here") is False


def test_send_match_result_wraps_builder_errors(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(DummyCm())

    def bad(_match):
        raise RuntimeError("nocreate")

    monkeypatch.setattr(handler, "_create_match_result_message", bad)

    ok = handler.send_match_result_notification(build_match())
    assert ok is False


def test_process_pending_completion_empty(monkeypatch) -> None:
    monkeypatch.setattr(NotificationHandler, "_load_subgroup_id", lambda self: "sub")
    monkeypatch.setattr(NotificationHandler, "_load_access_token", lambda self: "tok")
    monkeypatch.setattr(NotificationHandler, "_load_player_slug", lambda self: "jane-doe")
    handler = NotificationHandler(DummyCm())

    assert handler.process_pending_completion_notifications() == 0
