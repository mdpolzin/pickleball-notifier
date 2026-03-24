"""Unit tests for YouTube checker API paths with mocked HTTP."""

import json

import requests
from pickleball_notifier.youtube.checker import YouTubeStreamChecker

from shared.helpers import DummyResponse


def _write_config(tmp_path, api_key="key-123"):
    (tmp_path / "config.json").write_text(
        json.dumps({"youtube": {"api_key": api_key}, "pickleball_tv": {"free_court_codes": ["CC"]}}),
        encoding="utf-8",
    )


def test_get_api_key_from_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path, api_key="abc")
    checker = YouTubeStreamChecker()

    assert checker._get_api_key() == "abc"


def test_check_youtube_api_live_match(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    checker = YouTubeStreamChecker()
    payload = {
        "items": [
            {"snippet": {"title": "PPA Court SC1 Live"}, "id": {"videoId": "vid123"}},
        ]
    }
    monkeypatch.setattr(checker.session, "get", lambda *args, **kwargs: DummyResponse(payload=payload))

    result = checker._check_youtube_api("SC1")

    assert result["is_live"] is True
    assert result["stream_url"] == "https://www.youtube.com/watch?v=vid123"


def test_check_youtube_api_handles_request_error(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    checker = YouTubeStreamChecker()
    monkeypatch.setattr(
        checker.session,
        "get",
        lambda *args, **kwargs: DummyResponse(raise_error=requests.RequestException("fail")),
    )

    result = checker._check_youtube_api("SC1")

    assert result["is_live"] is False
    assert "YouTube API error" in result["error"]

