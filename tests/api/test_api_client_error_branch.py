"""Direct error branch tests for API client parsing."""

from pickleball_notifier.api.client import PickleballApiClient


class BadJsonResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self):
        raise ValueError("bad json")


def test_get_match_info_handles_json_parse_error(monkeypatch) -> None:
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: BadJsonResponse())

    result = client.get_match_info("uuid-1")

    assert result.success is False
    assert "Data parsing error" in result.error_message


def test_short_slug_tokens_do_not_match_name() -> None:
    client = PickleballApiClient(monitored_player_slug="al-li")
    assert client._name_matches_monitored_player("Al Li") is False

