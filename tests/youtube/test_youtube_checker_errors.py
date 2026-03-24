"""Error-path tests for YouTube checker configuration and wrappers."""

import json

import pytest
import requests
from pickleball_notifier.youtube.checker import YouTubeStreamChecker


def test_get_api_key_raises_for_missing_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    checker = YouTubeStreamChecker()

    with pytest.raises(FileNotFoundError):
        checker._get_api_key()


def test_get_api_key_raises_for_placeholder_key(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"youtube": {"api_key": "YOUR_YOUTUBE_API_KEY_HERE"}}),
        encoding="utf-8",
    )
    checker = YouTubeStreamChecker()

    with pytest.raises(RuntimeError):
        checker._get_api_key()


def test_check_court_stream_calls_api_method(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    checker = YouTubeStreamChecker()
    monkeypatch.setattr(checker, "_check_youtube_api", lambda court: {"is_live": False, "stream_url": None, "error": f"checked-{court}"})

    result = checker.check_court_stream("SC1")

    assert result["error"] == "checked-SC1"


def test_check_youtube_api_redacts_api_key_from_error(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"youtube": {"api_key": "super-secret-key"}}),
        encoding="utf-8",
    )
    checker = YouTubeStreamChecker()
    message = "request failed: https://example.test/path?key=super-secret-key&foo=1"
    monkeypatch.setattr(
        checker.session,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.RequestException(message)),
    )

    result = checker._check_youtube_api("SC1")

    assert "super-secret-key" not in result["error"]
    assert "key=[REDACTED]" in result["error"]

