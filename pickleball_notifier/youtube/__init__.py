"""YouTube integration modules."""

__all__ = ["YouTubeStreamChecker"]


def __getattr__(name: str):
    """Lazily expose YouTube checker symbols."""
    if name == "YouTubeStreamChecker":
        from pickleball_notifier.youtube.checker import YouTubeStreamChecker

        return YouTubeStreamChecker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
