"""Unit tests for scraper logic with mocked dependencies."""

from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup
from pickleball_notifier.api.client import MatchApiResult
from pickleball_notifier.services.scraper import PickleballPlayerScraper

from shared.helpers import DummyResponse


class DummyConfigManager:
    """Config manager stub for scraper tests."""

    def __init__(self):
        self.saved = False
        self.recorded = None
        self.court_updates = []

    def remove_stale_matches(self, _current_uuids):
        return 1

    def update_matches(self, _urls):
        return {"new_matches": 1, "future_matches": 1, "assigned_matches": 0}

    def get_matches_needing_court_check(self):
        return [SimpleNamespace(uuid="11111111-1111-1111-1111-111111111111")]

    def update_court_assignment(self, *args):
        self.court_updates.append(args)

    def cleanup_old_execution_history(self):
        return 1

    def record_execution(self, **kwargs):
        self.recorded = kwargs

    def save_config(self):
        self.saved = True


class DummyApiClient:
    """API client stub for scraper tests."""

    def check_multiple_matches(self, _uuids):
        return [
            MatchApiResult(
                uuid="11111111-1111-1111-1111-111111111111",
                success=True,
                court_assigned=True,
                court_title="SC1",
                partner_name="Partner One",
                opponent_names=["Opp A", "Opp B"],
            )
        ]


class DummyNotificationHandler:
    """Notification handler stub for scraper tests."""

    player_slug = "jane-doe"

    def process_pending_notifications(self):
        return 2


def build_scraper() -> PickleballPlayerScraper:
    """Build scraper with fully mocked collaborators."""
    return PickleballPlayerScraper(
        config_manager=DummyConfigManager(),
        api_client=DummyApiClient(),
        notification_handler=DummyNotificationHandler(),
    )


def test_get_player_page_returns_none_on_request_error(monkeypatch) -> None:
    scraper = build_scraper()
    monkeypatch.setattr(
        scraper.session,
        "get",
        lambda *args, **kwargs: DummyResponse(raise_error=requests.RequestException("offline")),
    )

    assert scraper.get_player_page("jane-doe") is None


def test_find_and_filter_results_links() -> None:
    scraper = build_scraper()
    html = """
    <div>Tournament Results</div>
    <a href="/results/match/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa">Results</a>
    <a href="/results/match/not-a-uuid">Results</a>
    <a href="/other/path">Other</a>
    """
    soup = BeautifulSoup(html, "html.parser")

    links = scraper.find_tournament_results_links(soup)
    urls = scraper.filter_results_links(links)

    assert len(links) >= 3
    assert urls == ["/results/match/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]


def test_scrape_player_tournament_results_updates_workflow(monkeypatch) -> None:
    scraper = build_scraper()
    html = """
    <div>Tournament Results</div>
    <a href="/results/match/11111111-1111-1111-1111-111111111111">Results</a>
    """
    monkeypatch.setattr(scraper, "get_player_page", lambda _slug: BeautifulSoup(html, "html.parser"))

    urls = scraper.scrape_player_tournament_results("jane-doe")

    assert urls == ["/results/match/11111111-1111-1111-1111-111111111111"]
    assert len(scraper.config_manager.court_updates) == 1
    assert scraper.config_manager.saved is True
    assert scraper.config_manager.recorded["notifications_sent"] == 2

