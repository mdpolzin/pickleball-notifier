#!/usr/bin/env python3
"""
API client for pickleball.com match information endpoints.
Handles court assignment checking and match status queries.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests

from pickleball_notifier.utils.logging import redact_sensitive_text


@dataclass
class MatchApiResult:
    """Result from match API call."""
    uuid: str
    success: bool
    court_assigned: bool
    court_title: Optional[str] = None
    match_completed: Optional[str] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    partner_name: Optional[str] = None
    opponent_names: Optional[List[str]] = None


class PickleballApiClient:
    """Client for pickleball.com API endpoints."""

    def __init__(
        self,
        base_url: str = "https://pickleball.com",
        delay_between_requests: float = 0.5,
        monitored_player_slug: Optional[str] = None
    ):
        self.base_url = base_url
        self.delay_between_requests = delay_between_requests
        self.monitored_player_slug = monitored_player_slug
        self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })

    def get_match_info(self, uuid: str) -> MatchApiResult:
        """Get match information for a specific UUID."""
        url = f"{self.base_url}/api/v1/results/getResultMatchInfos?id={uuid}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                match_data = data['data'][0]
                court_title = match_data.get('court_title', '')
                match_completed = match_data.get('match_completed')
                court_assigned = bool(court_title and court_title.strip())
                partner_name, opponent_names = self._extract_player_names(match_data)

                return MatchApiResult(
                    uuid=uuid,
                    success=True,
                    court_assigned=court_assigned,
                    court_title=court_title if court_assigned else None,
                    match_completed=match_completed,
                    response_data=data,
                    partner_name=partner_name,
                    opponent_names=opponent_names
                )

            return MatchApiResult(
                uuid=uuid,
                success=False,
                court_assigned=False,
                error_message="No data found in API response"
            )

        except requests.RequestException as exc:
            return MatchApiResult(
                uuid=uuid,
                success=False,
                court_assigned=False,
                error_message=f"Request failed: {str(exc)}"
            )
        except (KeyError, IndexError, ValueError) as exc:
            return MatchApiResult(
                uuid=uuid,
                success=False,
                court_assigned=False,
                error_message=f"Data parsing error: {str(exc)}"
            )

    def check_multiple_matches(self, uuids: List[str]) -> List[MatchApiResult]:
        """Check court assignments for multiple matches with rate limiting."""
        results = []
        for i, uuid in enumerate(uuids):
            print(f"Checking court assignment for match {i+1}/{len(uuids)}: {uuid}")
            result = self.get_match_info(uuid)
            results.append(result)

            if result.success:
                if result.court_assigned:
                    completion_status = " (COMPLETED)" if result.match_completed else ""
                    print(f"  ✅ Court assigned: {result.court_title}{completion_status}")
                else:
                    print("  ⏳ No court assigned yet")
            else:
                print(f"  ❌ Error: {redact_sensitive_text(result.error_message or '')}")

            if i < len(uuids) - 1:
                time.sleep(self.delay_between_requests)

        return results

    def _extract_player_names(self, match_data: Dict) -> Tuple[Optional[str], Optional[List[str]]]:
        """Extract partner and opponent names from match data."""
        partner_name = None
        opponent_names: List[str] = []
        team_one_players: List[str] = []
        team_two_players: List[str] = []

        for player_num in ['one', 'two']:
            key = f'team_one_player_{player_num}_name'
            if key in match_data:
                name = match_data[key].strip() if match_data[key] else ''
                if name:
                    team_one_players.append(name)

        for player_num in ['one', 'two']:
            key = f'team_two_player_{player_num}_name'
            if key in match_data:
                name = match_data[key].strip() if match_data[key] else ''
                if name:
                    team_two_players.append(name)

        monitored_team = None
        if any(self._name_matches_monitored_player(player) for player in team_one_players):
            monitored_team = 'one'
        elif any(self._name_matches_monitored_player(player) for player in team_two_players):
            monitored_team = 'two'

        if monitored_team is None:
            return None, None

        if monitored_team == 'one':
            for player in team_one_players:
                if not self._name_matches_monitored_player(player):
                    partner_name = player
                    break
            opponent_names = team_two_players
        else:
            for player in team_two_players:
                if not self._name_matches_monitored_player(player):
                    partner_name = player
                    break
            opponent_names = team_one_players

        return partner_name, opponent_names if opponent_names else None

    def _name_matches_monitored_player(self, player_name: str) -> bool:
        """Check whether a player name matches the configured monitored player."""
        if not self.monitored_player_slug or not player_name:
            return False

        normalized_name = player_name.lower()
        slug_tokens = [token for token in self.monitored_player_slug.lower().split('-') if token]
        return any(len(token) >= 3 and token in normalized_name for token in slug_tokens)

    def get_court_assigned_from_api(self, uuids: List[str]) -> List[MatchApiResult]:
        """Get only matches that have been assigned to a court from API calls."""
        all_results = self.check_multiple_matches(uuids)
        return [result for result in all_results if result.success and result.court_assigned]

