#!/usr/bin/env python3
"""
API client for pickleball.com match information endpoints.
Handles court assignment checking and match status queries.
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


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


class PickleballApiClient:
    """Client for pickleball.com API endpoints."""
    
    def __init__(self, base_url: str = "https://pickleball.com", delay_between_requests: float = 0.5):
        self.base_url = base_url
        self.delay_between_requests = delay_between_requests
        self.session = requests.Session()
        
        # Set realistic headers to avoid being blocked
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
        """
        Get match information for a specific UUID.
        
        Args:
            uuid: The match UUID
            
        Returns:
            MatchApiResult with court assignment information
        """
        url = f"{self.base_url}/api/v1/results/getResultMatchInfos?id={uuid}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have the expected data structure
            if 'data' in data and len(data['data']) > 0:
                match_data = data['data'][0]
                court_title = match_data.get('court_title', '')
                match_completed = match_data.get('match_completed')
                
                # Court is assigned if court_title is not empty
                court_assigned = bool(court_title and court_title.strip())
                
                return MatchApiResult(
                    uuid=uuid,
                    success=True,
                    court_assigned=court_assigned,
                    court_title=court_title if court_assigned else None,
                    match_completed=match_completed,
                    response_data=data
                )
            else:
                return MatchApiResult(
                    uuid=uuid,
                    success=False,
                    court_assigned=False,
                    error_message="No data found in API response"
                )
                
        except requests.RequestException as e:
            return MatchApiResult(
                uuid=uuid,
                success=False,
                court_assigned=False,
                error_message=f"Request failed: {str(e)}"
            )
        except (KeyError, IndexError, ValueError) as e:
            return MatchApiResult(
                uuid=uuid,
                success=False,
                court_assigned=False,
                error_message=f"Data parsing error: {str(e)}"
            )
    
    def check_multiple_matches(self, uuids: List[str]) -> List[MatchApiResult]:
        """
        Check court assignments for multiple matches with rate limiting.
        
        Args:
            uuids: List of match UUIDs to check
            
        Returns:
            List of MatchApiResult objects
        """
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
                    print(f"  ⏳ No court assigned yet")
            else:
                print(f"  ❌ Error: {result.error_message}")
            
            # Rate limiting - delay between requests
            if i < len(uuids) - 1:  # Don't delay after the last request
                time.sleep(self.delay_between_requests)
        
        return results
    
    def get_court_assigned_from_api(self, uuids: List[str]) -> List[MatchApiResult]:
        """
        Get only matches that have been assigned to a court from API calls.
        
        Args:
            uuids: List of match UUIDs to check
            
        Returns:
            List of MatchApiResult objects for matches with court assignments
        """
        all_results = self.check_multiple_matches(uuids)
        return [result for result in all_results if result.success and result.court_assigned]
