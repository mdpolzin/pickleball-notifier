"""Additional branch tests for YouTube checker."""

import json

import pytest
from pickleball_notifier.youtube.checker import YouTubeStreamChecker

from shared.helpers import DummyResponse


def test_check_youtube_api_no_live_items(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"youtube": {"api_key": "k"}}), encoding="utf-8")
    checker = YouTubeStreamChecker()
    monkeypatch.setattr(checker.session, "get", lambda *args, **kwargs: DummyResponse(payload={"items": []}))

    result = checker._check_youtube_api("SC1")

    assert result["is_live"] is False
    assert result["stream_url"] is None


def test_get_api_key_raises_value_error_for_invalid_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text("{bad", encoding="utf-8")
    checker = YouTubeStreamChecker()

    with pytest.raises(ValueError):
        checker._get_api_key()


def test_load_free_court_codes_handles_non_list_and_exception(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"pickleball_tv": {"free_court_codes": "CC"}}),
        encoding="utf-8",
    )
    checker = YouTubeStreamChecker()
    assert checker.free_court_codes == {"CC"}

    monkeypatch.setattr("pickleball_notifier.youtube.checker.json.load", lambda _f: (_ for _ in ()).throw(RuntimeError("bad")))
    assert checker._load_free_court_codes() == {"CC"}

