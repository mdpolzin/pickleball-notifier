"""Additional branch coverage for ConfigManager."""

import builtins
from datetime import datetime, timedelta, timezone

from pickleball_notifier.core.config import ConfigManager, ExecutionRecord


def test_load_config_converts_legacy_match_status_values(tmp_path) -> None:
    config_file = tmp_path / "scraper_config.json"
    config_file.write_text(
        """
{
  "matches": {
    "a": {
      "uuid": "a",
      "url": "https://pickleball.com/results/match/a",
      "first_seen": "2026-01-01T00:00:00+00:00",
      "last_seen": "2026-01-01T00:00:00+00:00",
      "status": "current"
    },
    "b": {
      "uuid": "b",
      "url": "https://pickleball.com/results/match/b",
      "first_seen": "2026-01-01T00:00:00+00:00",
      "last_seen": "2026-01-01T00:00:00+00:00",
      "status": "unknown"
    }
  },
  "execution_history": [
    {
      "timestamp": "2026-01-01T00:00:00+00:00",
      "matches_found": 1,
      "new_matches": 1,
      "future_matches": 1,
      "assigned_matches": 0,
      "court_assignments_checked": 0,
      "court_assignments_found": 0,
      "notifications_sent": 0,
      "stale_matches_removed": 0
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    manager = ConfigManager(config_file=str(config_file))

    assert manager.matches["a"].status == "assigned"
    assert manager.matches["b"].status == "future"
    assert len(manager.execution_history) == 1


def test_save_config_handles_write_error(monkeypatch, tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    real_open = builtins.open

    def failing_open(*args, **kwargs):
        if str(args[0]).endswith("cfg.json") and "w" in args[1]:
            raise OSError("write blocked")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", failing_open)
    manager.save_config()


def test_record_execution_trims_history_to_100(tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    manager.execution_history = [
        ExecutionRecord(
            timestamp=f"2026-01-01T00:00:{i:02d}+00:00",
            matches_found=0,
            new_matches=0,
            future_matches=0,
            assigned_matches=0,
        )
        for i in range(100)
    ]
    manager.record_execution(
        matches_found=1,
        match_counts={"new_matches": 1, "future_matches": 1, "assigned_matches": 0},
    )

    assert len(manager.execution_history) == 100


def test_summary_and_getters_cover_paths(tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    manager.update_matches(["/results/match/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"])
    manager.update_court_assignment("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "SC1", True)

    assert manager.get_match_summary()["total_matches"] == 1
    assert len(manager.get_future_matches()) == 0
    assert len(manager.get_assigned_matches()) == 1
    assert len(manager.get_matches_needing_court_check()) == 0
    assert len(manager.get_court_assigned_matches()) == 1
    assert manager.cleanup_old_execution_history(max_records=100) == 0
    cleanup = manager.get_cleanup_summary()
    assert cleanup["assigned_matches"] == 1


def test_recent_execution_summary_branches(tmp_path) -> None:
    manager = ConfigManager(config_file=str(tmp_path / "cfg.json"))
    empty = manager.get_recent_execution_summary()
    assert empty["total_executions"] == 0

    now = datetime.now(timezone.utc)
    manager.execution_history = [
        ExecutionRecord(
            timestamp=(now - timedelta(hours=1)).isoformat(),
            matches_found=1,
            new_matches=0,
            future_matches=0,
            assigned_matches=0,
            court_assignments_found=1,
        ),
        ExecutionRecord(
            timestamp=(now - timedelta(hours=2)).isoformat(),
            matches_found=1,
            new_matches=0,
            future_matches=0,
            assigned_matches=0,
        ),
    ]
    summary = manager.get_recent_execution_summary(hours=24)

    assert summary["total_executions"] == 2
    assert summary["active_executions"] == 1
    assert summary["total_court_assignments_found"] == 1

