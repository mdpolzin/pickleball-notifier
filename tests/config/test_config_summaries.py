"""Tests for config summary and history behavior."""

from pickleball_notifier.core.config import ConfigManager, ExecutionRecord


def test_load_config_converts_legacy_execution_record(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    config_file.write_text(
        """
{
  "matches": {},
  "execution_history": [
    {
      "timestamp": "2026-01-01T00:00:00+00:00",
      "matches_found": 2,
      "new_matches": 1,
      "unknown_matches": 1,
      "completed_matches": 1
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    manager = ConfigManager(config_file=str(config_file))

    assert len(manager.execution_history) == 1
    assert manager.execution_history[0].future_matches == 1
    assert manager.execution_history[0].assigned_matches == 1


def test_cleanup_old_execution_history_trims_records(tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    manager.execution_history = [
        ExecutionRecord(
            timestamp=f"2026-01-01T00:00:0{i}+00:00",
            matches_found=1,
            new_matches=0,
            future_matches=0,
            assigned_matches=0,
        )
        for i in range(5)
    ]

    removed = manager.cleanup_old_execution_history(max_records=3)

    assert removed == 2
    assert len(manager.execution_history) == 3

