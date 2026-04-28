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


def test_get_match_uuids_for_status_refresh(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    u_future = "11111111-1111-1111-1111-111111111111"
    u_live = "22222222-2222-2222-2222-222222222222"
    u_done = "33333333-3333-3333-3333-333333333333"

    manager.update_matches(
        [
            f"/results/match/{u_future}",
            f"/results/match/{u_live}",
            f"/results/match/{u_done}",
        ]
    )

    manager.update_court_assignment(u_live, "SC1", True, match_completed=None)
    manager.update_court_assignment(u_done, "SC2", True, match_completed="done")

    page = {u_future, u_live, u_done}
    refreshed = manager.get_match_uuids_for_status_refresh(page)

    assert set(refreshed) == {u_future, u_live}


def test_get_pending_completion_and_mark_completion(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    url = "/results/match/44444444-4444-4444-4444-444444444444"
    uuid = "44444444-4444-4444-4444-444444444444"
    manager.update_matches([url])
    manager.update_court_assignment(uuid, "SC9", True, match_completed="Win")

    pending = manager.get_pending_completion_notifications()
    assert len(pending) == 1

    manager.mark_completion_notified(uuid)
    pending2 = manager.get_pending_completion_notifications()
    assert len(pending2) == 0
    assert manager.matches[uuid].completion_notified is True


def test_get_match_uuids_skips_matches_not_on_player_page(tmp_path) -> None:
    """UUIDs not listed on the current scrape should not be polled."""
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    ua = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    ub = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    manager.update_matches([f"/results/match/{ua}", f"/results/match/{ub}"])

    refreshed = manager.get_match_uuids_for_status_refresh({ua})
    assert refreshed == [ua]


def test_load_config_drops_legacy_assignment_notice_field(tmp_path) -> None:
    """Older configs may persist a deprecated GroupMe field; it must not block load."""
    config_file = tmp_path / "scraper_config.json"
    config_file.write_text(
        """
{
  "matches": {
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": {
      "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "url": "https://pickleball.com/results/match/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "first_seen": "2026-01-01T00:00:00+00:00",
      "last_seen": "2026-01-01T00:00:00+00:00",
      "status": "assigned",
      "assignment_notice_groupme_url": "https://legacy.groupme.example/x"
    }
  },
  "execution_history": []
}
""".strip(),
        encoding="utf-8",
    )
    manager = ConfigManager(config_file=str(config_file))
    m = manager.matches["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]
    assert not hasattr(m, "assignment_notice_groupme_url")
