"""Application services."""

__all__ = ["PickleballPlayerScraper"]


def __getattr__(name: str):
    """Lazily expose scraper service to avoid runpy pre-import warnings."""
    if name == "PickleballPlayerScraper":
        from pickleball_notifier.services.scraper import PickleballPlayerScraper

        return PickleballPlayerScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
