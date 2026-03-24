#!/usr/bin/env python3
"""
Web scraper for pickleball.com player pages.
Extracts tournament results links for the configured player.
"""

import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from pickleball_notifier.api.client import PickleballApiClient
from pickleball_notifier.core.config import ConfigManager
from pickleball_notifier.notifications.handler import NotificationHandler
from pickleball_notifier.utils.logging import redact_sensitive_text


class PickleballPlayerScraper:
    """Scraper for pickleball.com player pages."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        api_client: Optional[PickleballApiClient] = None,
        notification_handler: Optional[NotificationHandler] = None
    ):
        self.base_url = "https://pickleball.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.config_manager = config_manager or ConfigManager()
        self.notification_handler = notification_handler or NotificationHandler(self.config_manager)
        self.api_client = api_client or PickleballApiClient(
            monitored_player_slug=self.notification_handler.player_slug
        )

    def get_player_page(self, player_slug: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a player's page."""
        url = f"{self.base_url}/players/{player_slug}"
        print(f"Fetching: {url}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as exc:
            print(f"Error fetching page: {redact_sensitive_text(str(exc))}")
            return None

    def find_tournament_results_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Find all anchor tags after the section containing Tournament Results."""
        links = []
        tournament_results_div = None
        for div in soup.find_all('div'):
            if div.get_text(strip=True) == 'Tournament Results':
                tournament_results_div = div
                break

        if not tournament_results_div:
            print("Could not find 'Tournament Results' div")
            return links

        print(f"Found 'Tournament Results' div at: {tournament_results_div}")
        all_links = soup.find_all('a')
        tournament_div_position = None

        for i, element in enumerate(soup.find_all()):
            if element == tournament_results_div:
                tournament_div_position = i
                break

        if tournament_div_position is None:
            print("Could not determine position of Tournament Results div")
            return links

        for link in all_links:
            link_position = None
            for i, element in enumerate(soup.find_all()):
                if element == link:
                    link_position = i
                    break

            if link_position is not None and link_position > tournament_div_position:
                links.append({
                    'text': link.get_text(strip=True),
                    'href': link.get('href', ''),
                    'title': link.get('title', ''),
                    'class': ' '.join(link.get('class', []))
                })

        return links

    def filter_results_links(self, links: List[Dict[str, str]]) -> List[str]:
        """Filter links to include only Results links with UUID format."""
        results_urls = []
        for link in links:
            if link['text'].strip() == 'Results':
                href = link['href']
                if '/results/match/' in href:
                    uuid_part = href.split('/results/match/')[-1]
                    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    if re.match(uuid_pattern, uuid_part):
                        results_urls.append(href)
        return results_urls

    def check_court_assignments(self, uuids: List[str]) -> Dict[str, int]:
        """Check court assignments for UUIDs and update configuration."""
        if not uuids:
            return {'checked': 0, 'court_assigned': 0, 'errors': 0}

        print(f"\nChecking court assignments for {len(uuids)} matches...")
        results = self.api_client.check_multiple_matches(uuids)
        court_assigned_count = 0
        error_count = 0

        for result in results:
            if result.success:
                self.config_manager.update_court_assignment(
                    result.uuid,
                    result.court_title or '',
                    result.court_assigned,
                    result.match_completed,
                    result.partner_name,
                    result.opponent_names
                )
                if result.court_assigned:
                    court_assigned_count += 1
            else:
                error_count += 1

        return {'checked': len(uuids), 'court_assigned': court_assigned_count, 'errors': error_count}

    def process_notifications(self) -> int:
        """Process all pending notifications for court assignments."""
        return self.notification_handler.process_pending_notifications()

    def scrape_player_tournament_results(self, player_slug: str) -> List[str]:
        """Scrape tournament results for a player slug."""
        soup = self.get_player_page(player_slug)
        if not soup:
            return []

        all_links = self.find_tournament_results_links(soup)
        results_urls = self.filter_results_links(all_links)
        uuids = [url.split('/results/match/')[-1] for url in results_urls]
        current_uuids = set(uuids)

        stale_removed = self.config_manager.remove_stale_matches(current_uuids)
        match_counts = self.config_manager.update_matches(results_urls)

        matches_needing_check = self.config_manager.get_matches_needing_court_check()
        uuids_to_check = [match.uuid for match in matches_needing_check if match.uuid in uuids]
        court_stats = self.check_court_assignments(uuids_to_check)

        history_cleaned = self.config_manager.cleanup_old_execution_history()
        notifications_sent = self.process_notifications()

        self.config_manager.record_execution(
            matches_found=len(results_urls),
            match_counts=match_counts,
            court_assignments_checked=court_stats['checked'],
            court_assignments_found=court_stats['court_assigned'],
            notifications_sent=notifications_sent,
            stale_matches_removed=stale_removed
        )
        self.config_manager.save_config()

        if stale_removed > 0:
            print(f"✅ Cleaned up {stale_removed} stale matches from configuration")
        if history_cleaned > 0:
            print(f"✅ Cleaned up {history_cleaned} old execution history records")
        if notifications_sent > 0:
            print(f"✅ Sent {notifications_sent} court assignment notifications")

        return results_urls


def main():
    """Main function to run the scraper."""
    config_manager = ConfigManager()
    notification_handler = NotificationHandler(config_manager)
    api_client = PickleballApiClient(monitored_player_slug=notification_handler.player_slug)
    scraper = PickleballPlayerScraper(config_manager, api_client, notification_handler)

    player_slug = notification_handler.player_slug
    print(f"Scraping tournament results for player: {player_slug}")
    results_urls = scraper.scrape_player_tournament_results(player_slug)

    if results_urls:
        print(f"\nFound {len(results_urls)} 'Results' links with UUID format:")
        print("-" * 60)
        for i, url in enumerate(results_urls, 1):
            uuid = url.split('/results/match/')[-1]
            print(f"{i}. UUID: {uuid}")
            print(f"   URL: {url}\n")
    else:
        print("No 'Results' links found after 'Tournament Results' div")


if __name__ == "__main__":  # pragma: no cover
    main()

