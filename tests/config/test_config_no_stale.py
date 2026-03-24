"""Coverage for no-stale early return branch."""

from pickleball_notifier.core.config import ConfigManager


def test_remove_stale_matches_returns_zero_when_none_stale(tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    manager.update_matches([f"/results/match/{uuid}"])

    removed = manager.remove_stale_matches({uuid})

    assert removed == 0

