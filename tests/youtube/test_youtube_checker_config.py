"""Unit tests for YouTube checker configuration behavior."""

import json

from pickleball_notifier.youtube.checker import YouTubeStreamChecker


def test_defaults_to_cc_when_config_missing(tmp_path, monkeypatch) -> None:
    """Default free court should be CC when no config file exists."""
    monkeypatch.chdir(tmp_path)

    checker = YouTubeStreamChecker()

    assert checker.free_court_codes == {"CC"}
    assert checker.get_pickleball_tv_message("CC") == " (free to watch on PickleballTV)"
    assert checker.get_pickleball_tv_message("SC1") == " (on PickleballTV - login required)"


def test_loads_free_court_codes_from_config(tmp_path, monkeypatch) -> None:
    """Configured free court codes should be normalized and used."""
    monkeypatch.chdir(tmp_path)
    config_data = {
        "pickleball_tv": {
            "free_court_codes": [" cc ", "gs", "Center"]
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(config_data), encoding="utf-8")

    checker = YouTubeStreamChecker()

    assert checker.free_court_codes == {"CC", "GS", "CENTER"}
    assert checker.get_pickleball_tv_message("GS") == " (free to watch on PickleballTV)"
    assert checker.get_pickleball_tv_message("SC1") == " (on PickleballTV - login required)"

