"""Coverage for scraper edge branches that need synthetic soup objects."""

from pickleball_notifier.services.scraper import PickleballPlayerScraper


class _FakeDiv:
    def get_text(self, strip=True):
        return "Tournament Results"


class _FakeSoupNoPosition:
    def __init__(self):
        self._target = _FakeDiv()

    def find_all(self, name=None):
        if name == "div":
            return [self._target]
        if name == "a":
            return []
        return []


def _build_scraper(monkeypatch) -> PickleballPlayerScraper:
    class DummyConfigManager:
        pass

    class DummyNotificationHandler:
        player_slug = "jane-doe"

    class DummyApiClient:
        pass

    return PickleballPlayerScraper(
        config_manager=DummyConfigManager(),
        api_client=DummyApiClient(),
        notification_handler=DummyNotificationHandler(),
    )


def test_find_tournament_results_links_handles_missing_position(monkeypatch) -> None:
    scraper = _build_scraper(monkeypatch)
    links = scraper.find_tournament_results_links(_FakeSoupNoPosition())
    assert links == []


def test_scrape_player_tournament_results_returns_empty_if_page_fetch_fails(monkeypatch) -> None:
    scraper = _build_scraper(monkeypatch)
    monkeypatch.setattr(scraper, "get_player_page", lambda _slug: None)

    assert scraper.scrape_player_tournament_results("jane-doe") == []

