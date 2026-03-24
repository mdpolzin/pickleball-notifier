"""Helpers for safe console logging without leaking secrets."""

import re

SENSITIVE_PATTERNS = [
    (r'([?&]key=)[^&\s]+', r'\1[REDACTED]'),
    (r'("api_key"\s*:\s*")[^"]+(")', r'\1[REDACTED]\2'),
    (r'((?:api[_-]?key|token|secret|bot_id)\s*[=:]\s*)\S+', r'\1[REDACTED]'),
]


def redact_sensitive_text(text: str) -> str:
    """Redact common secret key/value patterns from loggable text."""
    if not text:
        return text

    redacted = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    return redacted

