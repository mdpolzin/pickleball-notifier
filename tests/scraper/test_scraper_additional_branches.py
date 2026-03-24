"""Additional branch tests for scraper module."""


from bs4 import BeautifulSoup
from pickleball_notifier.api.client import MatchApiResult
from pickleball_notifier.services.scraper import PickleballPlayerScraper

from shared.helpers import DummyResponse


class DummyConfigManager:
    def update_court_assignment(self, *args):
        return None

    def remove_stale_matches(self, _current_uuids):
        return 0

    def update_matches(self, _urls):
        return {"new_matches": 0, "future_matches": 0, "assigned_matches": 0}

    def get_matches_needing_court_check(self):
        return []

    def cleanup_old_execution_history(self):
        return 0

    def record_execution(self, **kwargs):
        return None

    def save_config(self):
        return None


class DummyApiClient:
    def check_multiple_matches(self, _uuids):
        return [MatchApiResult(uuid="x", success=False, court_assigned=False, error_message="bad")]


class DummyNotificationHandler:
    player_slug = "jane-doe"

    def process_pending_notifications(self):
        return 0


def _scraper() -> PickleballPlayerScraper:
    return PickleballPlayerScraper(
        config_manager=DummyConfigManager(),
        api_client=DummyApiClient(),
        notification_handler=DummyNotificationHandler(),
    )


def test_get_player_page_success(monkeypatch) -> None:
    scraper = _scraper()
    monkeypatch.setattr(scraper.session, "get", lambda *args, **kwargs: DummyResponse(payload={}))
    monkeypatch.setattr(DummyResponse, "content", b"<html></html>", raising=False)

    soup = scraper.get_player_page("jane-doe")

    assert isinstance(soup, BeautifulSoup)


def test_find_tournament_results_links_missing_div_returns_empty() -> None:
    scraper = _scraper()
    soup = BeautifulSoup("<div>Other</div>", "html.parser")
    assert scraper.find_tournament_results_links(soup) == []


def test_check_court_assignments_empty_and_error_paths() -> None:
    scraper = _scraper()

    assert scraper.check_court_assignments([]) == {"checked": 0, "court_assigned": 0, "errors": 0}
    assert scraper.check_court_assignments(["x"]) == {"checked": 1, "court_assigned": 0, "errors": 1}

