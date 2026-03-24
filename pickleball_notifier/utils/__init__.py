"""Shared utility modules."""

__all__ = ["redact_sensitive_text"]


def __getattr__(name: str):
    """Lazily expose utility symbols."""
    if name == "redact_sensitive_text":
        from pickleball_notifier.utils.logging import redact_sensitive_text

        return redact_sensitive_text
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
