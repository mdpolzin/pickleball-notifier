"""Unit tests for API client parsing logic."""

from pickleball_notifier.api.client import PickleballApiClient


def test_name_matches_monitored_player_uses_slug_tokens() -> None:
    """Slug token matching should work for full names and be case-insensitive."""
    client = PickleballApiClient(monitored_player_slug="jane-doe")

    assert client._name_matches_monitored_player("Jane Doe")
    assert client._name_matches_monitored_player("DOE, JANE")
    assert not client._name_matches_monitored_player("John Smith")


def test_extract_player_names_when_monitored_player_on_team_one() -> None:
    """Partner should come from team one and opponents from team two."""
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    match_data = {
        "team_one_player_one_name": "Jane Doe",
        "team_one_player_two_name": "Partner One",
        "team_two_player_one_name": "Opponent A",
        "team_two_player_two_name": "Opponent B",
    }

    partner_name, opponent_names = client._extract_player_names(match_data)

    assert partner_name == "Partner One"
    assert opponent_names == ["Opponent A", "Opponent B"]


def test_extract_player_names_when_monitored_player_on_team_two() -> None:
    """Partner should come from team two and opponents from team one."""
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    match_data = {
        "team_one_player_one_name": "Opponent A",
        "team_one_player_two_name": "Opponent B",
        "team_two_player_one_name": "Jane Doe",
        "team_two_player_two_name": "Partner One",
    }

    partner_name, opponent_names = client._extract_player_names(match_data)

    assert partner_name == "Partner One"
    assert opponent_names == ["Opponent A", "Opponent B"]


def test_extract_player_names_returns_none_if_monitored_player_missing() -> None:
    """No partner/opponents should be returned when monitored player is absent."""
    client = PickleballApiClient(monitored_player_slug="jane-doe")
    match_data = {
        "team_one_player_one_name": "Opponent A",
        "team_one_player_two_name": "Opponent B",
        "team_two_player_one_name": "Opponent C",
        "team_two_player_two_name": "Opponent D",
    }

    partner_name, opponent_names = client._extract_player_names(match_data)

    assert partner_name is None
    assert opponent_names is None

