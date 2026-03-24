"""Core domain and state management modules."""

__all__ = ["ConfigManager", "ExecutionRecord", "MatchInfo"]


def __getattr__(name: str):
    """Lazily expose core configuration symbols."""
    if name in {"ConfigManager", "ExecutionRecord", "MatchInfo"}:
        from pickleball_notifier.core.config import ConfigManager, ExecutionRecord, MatchInfo

        return {"ConfigManager": ConfigManager, "ExecutionRecord": ExecutionRecord, "MatchInfo": MatchInfo}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
