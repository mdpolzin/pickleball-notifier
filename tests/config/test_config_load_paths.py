"""Tests for config manager load/save branches."""

from pickleball_notifier.core.config import ConfigManager


def test_load_config_gracefully_handles_bad_json(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    config_file.write_text("{not-json", encoding="utf-8")

    manager = ConfigManager(config_file=str(config_file))

    assert manager.matches == {}
    assert manager.execution_history == []


def test_remove_stale_matches_requires_ten_runs(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    manager = ConfigManager(config_file=str(config_file))
    uuid = "77777777-7777-7777-7777-777777777777"
    manager.update_matches([f"/results/match/{uuid}"])

    removed = 0
    for _ in range(9):
        removed = manager.remove_stale_matches(set())
    assert removed == 0
    assert uuid in manager.matches

    removed = manager.remove_stale_matches(set())
    assert removed == 1
    assert uuid not in manager.matches

