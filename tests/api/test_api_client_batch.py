"""Batch and filtering tests for API client."""

from pickleball_notifier.api.client import MatchApiResult, PickleballApiClient


def test_check_multiple_matches_invokes_sleep_between_calls(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    calls = []

    def fake_get_match_info(uuid: str) -> MatchApiResult:
        return MatchApiResult(uuid=uuid, success=True, court_assigned=False)

    monkeypatch.setattr(client, "get_match_info", fake_get_match_info)
    monkeypatch.setattr("pickleball_notifier.api.client.time.sleep", lambda _secs: calls.append("sleep"))

    results = client.check_multiple_matches(["u1", "u2", "u3"])

    assert [r.uuid for r in results] == ["u1", "u2", "u3"]
    assert len(calls) == 2


def test_get_court_assigned_from_api_filters_results(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    monkeypatch.setattr(
        client,
        "check_multiple_matches",
        lambda _uuids: [
            MatchApiResult(uuid="a", success=True, court_assigned=True, court_title="SC1"),
            MatchApiResult(uuid="b", success=True, court_assigned=False),
            MatchApiResult(uuid="c", success=False, court_assigned=False),
        ],
    )

    assigned = client.get_court_assigned_from_api(["a", "b", "c"])

    assert [match.uuid for match in assigned] == ["a"]

