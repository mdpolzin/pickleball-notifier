#!/usr/bin/env python3
"""
Web scraper for pickleball.com player pages.
Specifically designed to extract tournament results links for Adam Harvey.
"""

import requests
from bs4 import BeautifulSoup
import sys
import re
from typing import List, Dict, Optional
from config import ConfigManager
from api_client import PickleballApiClient
from notification_handler import NotificationHandler


class PickleballPlayerScraper:
    """Scraper for pickleball.com player pages."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, api_client: Optional[PickleballApiClient] = None, notification_handler: Optional[NotificationHandler] = None):
        self.base_url = "https://pickleball.com"
        self.session = requests.Session()
        # Set a realistic user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.config_manager = config_manager or ConfigManager()
        self.api_client = api_client or PickleballApiClient()
        self.notification_handler = notification_handler or NotificationHandler(self.config_manager)
    
    def get_player_page(self, player_slug: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a player's page.
        
        Args:
            player_slug: The player's slug (e.g., 'adam-harvey')
            
        Returns:
            BeautifulSoup object of the parsed HTML, or None if failed
        """
        url = f"{self.base_url}/players/{player_slug}"
        print(f"Fetching: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None
    
    def find_tournament_results_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Find all <a> tags after the div containing 'Tournament Results'.
        
        Args:
            soup: BeautifulSoup object of the parsed HTML
            
        Returns:
            List of dictionaries containing link information
        """
        links = []
        
        # Find the div containing 'Tournament Results'
        tournament_results_div = None
        for div in soup.find_all('div'):
            if div.get_text(strip=True) == 'Tournament Results':
                tournament_results_div = div
                break
        
        if not tournament_results_div:
            print("Could not find 'Tournament Results' div")
            return links
        
        print(f"Found 'Tournament Results' div at: {tournament_results_div}")
        
        # Find all <a> tags that come after this div
        # We'll search through all <a> tags and check if they come after our target div
        all_links = soup.find_all('a')
        tournament_div_position = None
        
        # Find the position of our target div in the document
        for i, element in enumerate(soup.find_all()):
            if element == tournament_results_div:
                tournament_div_position = i
                break
        
        if tournament_div_position is None:
            print("Could not determine position of Tournament Results div")
            return links
        
        # Collect all <a> tags that come after the Tournament Results div
        for link in all_links:
            link_position = None
            for i, element in enumerate(soup.find_all()):
                if element == link:
                    link_position = i
                    break
            
            if link_position is not None and link_position > tournament_div_position:
                link_info = {
                    'text': link.get_text(strip=True),
                    'href': link.get('href', ''),
                    'title': link.get('title', ''),
                    'class': ' '.join(link.get('class', []))
                }
                links.append(link_info)
        
        return links
    
    def filter_results_links(self, links: List[Dict[str, str]]) -> List[str]:
        """
        Filter links to only include 'Results' links with UUID format.
        
        Args:
            links: List of link dictionaries from find_tournament_results_links
            
        Returns:
            List of URLs for Results links only
        """
        results_urls = []
        
        for link in links:
            # Check if this is a "Results" link
            if link['text'].strip() == 'Results':
                href = link['href']
                # Check if it matches the expected format: results/match/<uuid>
                if '/results/match/' in href:
                    # Extract and validate UUID format
                    uuid_part = href.split('/results/match/')[-1]
                    # Basic UUID validation (8-4-4-4-12 hex digits)
                    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    if re.match(uuid_pattern, uuid_part):
                        results_urls.append(href)
        
        return results_urls
    
    def check_court_assignments(self, uuids: List[str]) -> Dict[str, int]:
        """
        Check court assignments for the given UUIDs and update configuration.
        
        Args:
            uuids: List of match UUIDs to check
            
        Returns:
            Dictionary with counts of court assignments found
        """
        if not uuids:
            return {'checked': 0, 'court_assigned': 0, 'errors': 0}
        
        print(f"\nChecking court assignments for {len(uuids)} matches...")
        results = self.api_client.check_multiple_matches(uuids)
        
        court_assigned_count = 0
        error_count = 0
        
        for result in results:
            if result.success:
                # Update configuration with court assignment info
                self.config_manager.update_court_assignment(
                    result.uuid, 
                    result.court_title or '', 
                    result.court_assigned
                )
                
                if result.court_assigned:
                    court_assigned_count += 1
            else:
                error_count += 1
        
        return {
            'checked': len(uuids),
            'court_assigned': court_assigned_count,
            'errors': error_count
        }
    
    def process_notifications(self) -> int:
        """
        Process all pending notifications for court assignments.
        
        Returns:
            Number of notifications sent
        """
        return self.notification_handler.process_pending_notifications()
    
    def scrape_player_tournament_results(self, player_slug: str) -> List[str]:
        """
        Main method to scrape tournament results for a player.
        
        Args:
            player_slug: The player's slug (e.g., 'adam-harvey')
            
        Returns:
            List of Results URLs with UUID format
        """
        soup = self.get_player_page(player_slug)
        if not soup:
            return []
        
        all_links = self.find_tournament_results_links(soup)
        results_urls = self.filter_results_links(all_links)
        
        # Extract UUIDs for cleanup and court assignment checking
        uuids = [url.split('/results/match/')[-1] for url in results_urls]
        current_uuids = set(uuids)
        
        # Remove stale matches that are no longer on the page
        stale_removed = self.config_manager.remove_stale_matches(current_uuids)
        
        # Update configuration with new matches
        match_counts = self.config_manager.update_matches(results_urls)
        
        # Check court assignments for matches that need checking
        matches_needing_check = self.config_manager.get_matches_needing_court_check()
        uuids_to_check = [match.uuid for match in matches_needing_check if match.uuid in uuids]
        
        court_stats = self.check_court_assignments(uuids_to_check)
        
        # Clean up old execution history to prevent file bloat
        history_cleaned = self.config_manager.cleanup_old_execution_history()
        
        # Process notifications for newly assigned matches
        notifications_sent = self.process_notifications()
        
        # Record this execution
        self.config_manager.record_execution(len(results_urls), match_counts)
        
        # Save configuration
        self.config_manager.save_config()
        
        # Log cleanup and notification results
        if stale_removed > 0:
            print(f"✅ Cleaned up {stale_removed} stale matches from configuration")
        if history_cleaned > 0:
            print(f"✅ Cleaned up {history_cleaned} old execution history records")
        if notifications_sent > 0:
            print(f"✅ Sent {notifications_sent} court assignment notifications")
        
        return results_urls


def main():
    """Main function to run the scraper."""
    # Initialize configuration manager, API client, and notification handler
    config_manager = ConfigManager()
    api_client = PickleballApiClient()
    notification_handler = NotificationHandler(config_manager)
    scraper = PickleballPlayerScraper(config_manager, api_client, notification_handler)
    
    # Scrape Adam Harvey's page
    player_slug = "adam-harvey"
    print(f"Scraping tournament results for player: {player_slug}")
    
    results_urls = scraper.scrape_player_tournament_results(player_slug)
    
    if results_urls:
        print(f"\nFound {len(results_urls)} 'Results' links with UUID format:")
        print("-" * 60)
        for i, url in enumerate(results_urls, 1):
            uuid = url.split('/results/match/')[-1]
            print(f"{i}. UUID: {uuid}")
            print(f"   URL: {url}")
            print()
        
        # Display configuration summary
        summary = config_manager.get_match_summary()
        cleanup_summary = config_manager.get_cleanup_summary()
        
        print("Configuration Summary:")
        print("-" * 30)
        print(f"Total matches tracked: {summary['total_matches']}")
        print(f"Future matches (no court yet): {summary['future_matches']}")
        print(f"Assigned matches (court assigned): {summary['assigned_matches']}")
        print(f"Recent executions (last 24h): {summary['recent_executions']}")
        
        print(f"\nCleanup Summary:")
        print("-" * 20)
        print(f"Notified matches: {cleanup_summary['notified_matches']}")
        print(f"Execution history records: {cleanup_summary['execution_history_records']}")
        
        # Show court assignment information
        court_assigned_matches = config_manager.get_court_assigned_matches()
        
        print(f"\nCourt Assignment Status:")
        print("-" * 30)
        print(f"Matches with court assignments: {len(court_assigned_matches)}")
        
        if court_assigned_matches:
            print(f"\nMatches with court assignments:")
            for match in court_assigned_matches:
                status = "✅ NOTIFIED" if match.notified else "🔔 PENDING NOTIFICATION"
                print(f"  - {match.uuid}: {match.court_title} ({status})")
        
        # Show future matches (no court assigned yet)
        future_matches = config_manager.get_future_matches()
        if future_matches:
            print(f"\nFuture matches (no court assigned yet):")
            for match in future_matches:
                print(f"  - {match.uuid} (no court assigned yet)")
        
        # Show assigned matches (court assigned)
        assigned_matches = config_manager.get_assigned_matches()
        if assigned_matches:
            print(f"\nAssigned matches (court assigned):")
            for match in assigned_matches:
                print(f"  - {match.uuid}: {match.court_title}")
    else:
        print("No 'Results' links found after 'Tournament Results' div")


if __name__ == "__main__":
    main()
