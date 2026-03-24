"""Remaining branch coverage for API client."""

from pickleball_notifier.api.client import MatchApiResult, PickleballApiClient


def test_check_multiple_matches_prints_assigned_and_error_branches(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    monkeypatch.setattr(
        client,
        "get_match_info",
        lambda uuid: (
            MatchApiResult(uuid=uuid, success=True, court_assigned=True, court_title="SC1")
            if uuid == "a"
            else MatchApiResult(uuid=uuid, success=False, court_assigned=False, error_message="bad")
        ),
    )

    results = client.check_multiple_matches(["a", "b"])

    assert [r.uuid for r in results] == ["a", "b"]


def test_name_match_returns_false_without_slug() -> None:
    client = PickleballApiClient(monitored_player_slug=None)
    assert client._name_matches_monitored_player("Jane Doe") is False

