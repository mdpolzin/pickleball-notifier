"""Tests for shared logging redaction helpers."""

from pickleball_notifier.utils.logging import redact_sensitive_text


def test_redact_sensitive_text_masks_query_and_json_api_key() -> None:
    text = (
        'request url: https://example.test/path?key=abc123&foo=1 '
        'payload: {"api_key":"xyz789"} token=tok-123'
    )

    redacted = redact_sensitive_text(text)

    assert "abc123" not in redacted
    assert "xyz789" not in redacted
    assert "tok-123" not in redacted
    assert "key=[REDACTED]" in redacted
    assert "[REDACTED]" in redacted


def test_redact_sensitive_text_returns_empty_input_unchanged() -> None:
    assert redact_sensitive_text("") == ""

