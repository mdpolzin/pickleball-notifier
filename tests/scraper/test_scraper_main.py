"""Tests for scraper.main control-flow branches."""

from pickleball_notifier.services import scraper as scraper_module


class DummyConfigManager:
    pass


class DummyNotificationHandler:
    def __init__(self, _config_manager):
        self.player_slug = "jane-doe"


class DummyApiClient:
    def __init__(self, monitored_player_slug=None):
        self.monitored_player_slug = monitored_player_slug


def test_main_handles_no_results(monkeypatch) -> None:
    class DummyScraper:
        def __init__(self, *_args, **_kwargs):
            pass

        def scrape_player_tournament_results(self, _slug):
            return []

    monkeypatch.setattr(scraper_module, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(scraper_module, "NotificationHandler", DummyNotificationHandler)
    monkeypatch.setattr(scraper_module, "PickleballApiClient", DummyApiClient)
    monkeypatch.setattr(scraper_module, "PickleballPlayerScraper", DummyScraper)

    scraper_module.main()


def test_main_handles_results_list(monkeypatch) -> None:
    class DummyScraper:
        def __init__(self, *_args, **_kwargs):
            pass

        def scrape_player_tournament_results(self, _slug):
            return ["/results/match/11111111-1111-1111-1111-111111111111"]

    monkeypatch.setattr(scraper_module, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(scraper_module, "NotificationHandler", DummyNotificationHandler)
    monkeypatch.setattr(scraper_module, "PickleballApiClient", DummyApiClient)
    monkeypatch.setattr(scraper_module, "PickleballPlayerScraper", DummyScraper)

    scraper_module.main()

