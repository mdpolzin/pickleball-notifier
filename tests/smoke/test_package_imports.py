"""Smoke tests and structure stubs."""


def test_package_imports() -> None:
    """Ensure core modules can be imported."""
    from pickleball_notifier.api.client import PickleballApiClient
    from pickleball_notifier.core.config import ConfigManager
    from pickleball_notifier.notifications.handler import NotificationHandler
    from pickleball_notifier.services.scraper import PickleballPlayerScraper
    from pickleball_notifier.youtube.checker import YouTubeStreamChecker

    assert PickleballApiClient is not None
    assert ConfigManager is not None
    assert NotificationHandler is not None
    assert PickleballPlayerScraper is not None
    assert YouTubeStreamChecker is not None

