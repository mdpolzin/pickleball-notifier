"""Unit tests for configuration manager behavior."""

from pickleball_notifier.core.config import ConfigManager


def test_update_matches_tracks_new_and_existing(tmp_path) -> None:
    """update_matches should count new and existing UUIDs correctly."""
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))

    urls = [
        "/results/match/11111111-1111-1111-1111-111111111111",
        "/results/match/22222222-2222-2222-2222-222222222222",
    ]
    first = manager.update_matches(urls)
    second = manager.update_matches(urls)

    assert first["new_matches"] == 2
    assert first["existing_matches"] == 0
    assert second["new_matches"] == 0
    assert second["existing_matches"] == 2


def test_update_court_assignment_sets_assigned_and_player_details(tmp_path) -> None:
    """Court assignment updates should move match to assigned and keep names."""
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    url = "/results/match/33333333-3333-3333-3333-333333333333"
    manager.update_matches([url])
    uuid = "33333333-3333-3333-3333-333333333333"

    manager.update_court_assignment(
        uuid=uuid,
        court_title="SC1",
        assigned=True,
        match_completed=None,
        partner_name="Partner One",
        opponent_names=["Opponent A", "Opponent B"],
    )

    match = manager.matches[uuid]
    assert match.status == "assigned"
    assert match.court_assigned is True
    assert match.court_title == "SC1"
    assert match.partner_name == "Partner One"
    assert match.opponent_names == ["Opponent A", "Opponent B"]


def test_get_pending_notifications_excludes_notified_and_completed(tmp_path) -> None:
    """Pending notifications should include only assigned, unnotified, active matches."""
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    uuids = [
        "44444444-4444-4444-4444-444444444444",
        "55555555-5555-5555-5555-555555555555",
        "66666666-6666-6666-6666-666666666666",
    ]
    urls = [f"/results/match/{uuid}" for uuid in uuids]
    manager.update_matches(urls)

    manager.update_court_assignment(uuids[0], "SC1", True)
    manager.update_court_assignment(uuids[1], "SC2", True)
    manager.update_court_assignment(uuids[2], "SC3", True, match_completed="done")
    manager.mark_as_notified(uuids[1])

    pending = manager.get_pending_notifications()

    assert len(pending) == 1
    assert pending[0].uuid == uuids[0]

