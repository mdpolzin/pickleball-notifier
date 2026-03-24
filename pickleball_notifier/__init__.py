"""Pickleball notifier package."""

__all__ = [
    "ConfigManager",
    "ExecutionRecord",
    "MatchApiResult",
    "MatchInfo",
    "NotificationHandler",
    "PickleballApiClient",
    "PickleballPlayerScraper",
    "YouTubeStreamChecker",
]


def __getattr__(name: str):
    """Lazily expose package symbols to avoid import-time side-effects."""
    if name in {"MatchApiResult", "PickleballApiClient"}:
        from pickleball_notifier.api.client import MatchApiResult, PickleballApiClient

        return {"MatchApiResult": MatchApiResult, "PickleballApiClient": PickleballApiClient}[name]
    if name in {"ConfigManager", "ExecutionRecord", "MatchInfo"}:
        from pickleball_notifier.core.config import ConfigManager, ExecutionRecord, MatchInfo

        return {"ConfigManager": ConfigManager, "ExecutionRecord": ExecutionRecord, "MatchInfo": MatchInfo}[name]
    if name == "NotificationHandler":
        from pickleball_notifier.notifications.handler import NotificationHandler

        return NotificationHandler
    if name == "PickleballPlayerScraper":
        from pickleball_notifier.services.scraper import PickleballPlayerScraper

        return PickleballPlayerScraper
    if name == "YouTubeStreamChecker":
        from pickleball_notifier.youtube.checker import YouTubeStreamChecker

        return YouTubeStreamChecker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

