"""Request-path tests for API client network handling."""

import requests
from pickleball_notifier.api.client import PickleballApiClient

from shared.helpers import DummyResponse


def test_get_match_info_success_with_court_assignment(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    payload = {
        "data": [{
            "court_title": "SC1",
            "match_completed": None,
            "team_one_player_one_name": "Jane Doe",
            "team_one_player_two_name": "Partner One",
            "team_two_player_one_name": "Opp A",
            "team_two_player_two_name": "Opp B",
        }]
    }
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))

    result = client.get_match_info("uuid-1")

    assert result.success is True
    assert result.court_assigned is True
    assert result.court_title == "SC1"
    assert result.partner_name == "Partner One"


def test_get_match_info_handles_missing_data(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: DummyResponse(payload={"data": []}))

    result = client.get_match_info("uuid-1")

    assert result.success is False
    assert "No data found" in result.error_message


def test_get_match_info_handles_request_exception(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    monkeypatch.setattr(
        client.session,
        "get",
        lambda *args, **kwargs: DummyResponse(raise_error=requests.RequestException("timeout")),
    )

    result = client.get_match_info("uuid-1")

    assert result.success is False
    assert "Request failed" in result.error_message

