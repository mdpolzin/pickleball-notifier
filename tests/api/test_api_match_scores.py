"""Parsing of winner + per-game scores from pickleball.com responses."""

from pickleball_notifier.api.client import PickleballApiClient

from shared.helpers import DummyResponse


def test_completed_match_derives_win_and_game_lines(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="ben-johns")
    payload = {
        "data": [{
            "court_title": "CC",
            "match_completed": "2026-04-14T19:39:00Z",
            "winner": 1,
            "team_one_player_one_name": "Ben Johns ",
            "team_one_player_two_name": "",
            "team_two_player_one_name": "Colin Wong ",
            "team_two_player_two_name": "",
            "team_one_game_one_score": 11,
            "team_two_game_one_score": 1,
            "team_one_game_two_score": 11,
            "team_two_game_two_score": 4,
            "team_one_game_three_score": 0,
            "team_two_game_three_score": 0,
        }]
    }
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))

    result = client.get_match_info("u1")

    assert result.success is True
    assert result.player_won is True
    assert result.game_score_lines == [
        "Game 1: 11-1",
        "Game 2: 11-4",
    ]


def test_completed_match_monitored_on_team_two_lost(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="colin-wong")
    payload = {
        "data": [{
            "court_title": "CC",
            "match_completed": "2026-04-14T19:39:00Z",
            "winner": 1,
            "team_one_player_one_name": "Ben Johns ",
            "team_two_player_one_name": "Colin Wong ",
            "team_one_game_one_score": 11,
            "team_two_game_one_score": 1,
            "team_one_game_two_score": 11,
            "team_two_game_two_score": 4,
        }]
    }
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))

    result = client.get_match_info("u1")

    assert result.player_won is False
    assert result.game_score_lines[0] == "Game 1: 11-1"


def test_infer_winner_invalid_returns_none() -> None:
    client = PickleballApiClient(monitored_player_slug="ben-johns")
    assert client._infer_player_won('one', None) is None
    assert client._infer_player_won('one', 9) is None
    assert client._infer_player_won(None, 1) is None


def test_winner_team_two_wins_match(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="ben-johns")
    payload = {
        "data": [{
            "court_title": "CC",
            "match_completed": "2026-04-14T19:39:00Z",
            "winner": 2,
            "team_one_player_one_name": "Ben Johns",
            "team_two_player_one_name": "Colin Wong",
            "team_one_game_one_score": 7,
            "team_two_game_one_score": 11,
            "team_one_game_two_score": 0,
            "team_two_game_two_score": 0,
        }]
    }
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))
    assert client.get_match_info("y").player_won is False


def test_resolve_monitored_none_when_slug_unrecognized() -> None:
    client = PickleballApiClient(monitored_player_slug="unlikely-slug-player")
    md = {"team_one_player_one_name": "Bob", "team_two_player_one_name": "Sue"}
    assert client._resolve_monitored_team(md) is None


def test_neutral_game_lines_when_slug_unrecognized(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="unlikely-slug-player")
    payload = {
        "data": [{
            "court_title": "C1",
            "match_completed": "2026-01-02T03:04:05Z",
            "winner": 1,
            "team_one_player_one_name": "A",
            "team_two_player_one_name": "B",
            "team_one_game_one_score": 11,
            "team_two_game_one_score": 5,
            "team_one_game_two_score": 0,
            "team_two_game_two_score": 0,
        }]
    }
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))
    r = client.get_match_info("z")
    assert r.player_won is None
    assert r.game_score_lines == ["Game 1: 11-5"]


def test_score_and_winner_coercion_helpers() -> None:
    assert PickleballApiClient._score_to_int("not-a-number") == 0
    assert PickleballApiClient._coerce_team_winner_digit(None) is None
    assert PickleballApiClient._coerce_team_winner_digit(3) is None
    assert PickleballApiClient._coerce_team_winner_digit("x") is None
