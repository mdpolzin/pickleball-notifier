#!/usr/bin/env python3
"""
YouTube stream checker for PPA court assignments.
Checks if a court assignment has a live YouTube stream available.
"""

import json
import os
from typing import Dict

import requests

from pickleball_notifier.utils.logging import redact_sensitive_text


class YouTubeStreamChecker:
    """Checks for live YouTube streams for court assignments."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/atom+xml,application/xml,text/xml',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        })
        self.request_delay = 1.0
        self.free_court_codes = self._load_free_court_codes()

    def _check_youtube_api(self, court_assignment: str) -> Dict[str, any]:
        """Check for live streams using YouTube Data API v3."""
        try:
            channel_id = "UCwxrKD60cB__M6nhdH0UW0w"
            print(f"   🔍 Checking YouTube API for {court_assignment}...")
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'eventType': 'live',
                'type': 'video',
                'q': f"court {court_assignment}",
                'key': self._get_api_key()
            }

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                    title = item['snippet']['title'].lower()
                    video_id = item['id']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    if f" {court_assignment} ".lower() in title:
                        print(f"   ✅ Found live stream via API: {item['snippet']['title']}")
                        print(f"   🎥 Live stream URL: {video_url}")
                        return {'is_live': True, 'stream_url': video_url, 'error': None}

            print(f"   ⚪ No live stream found for {court_assignment} via YouTube API")
            return {'is_live': False, 'stream_url': None, 'error': None}
        except Exception as exc:
            safe_exc = redact_sensitive_text(str(exc))
            error_msg = f"YouTube API error: {safe_exc}"
            print(f"   ❌ {error_msg}")
            return {'is_live': False, 'stream_url': None, 'error': error_msg}

    def _get_api_key(self) -> str:
        """Get YouTube API key from config file."""
        config_file = "config.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found. "
                f"Please copy 'config.json.template' to '{config_file}' and add your API key."
            )

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            api_key = config.get('youtube', {}).get('api_key')
            if not api_key or api_key == "YOUR_YOUTUBE_API_KEY_HERE":
                raise KeyError("youtube.api_key not found or not configured in config file")
            return api_key
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Error loading YouTube API key from config: {exc}")

    def check_court_stream(self, court_assignment: str) -> Dict[str, any]:
        """Check if a court assignment has a live YouTube stream."""
        print(f"🔍 Checking YouTube for live stream: {court_assignment}")
        return self._check_youtube_api(court_assignment)

    def get_pickleball_tv_message(self, court_assignment: str) -> str:
        """Get PickleballTV watchability text for a court assignment."""
        if court_assignment in self.free_court_codes:
            return " (free to watch on PickleballTV)"
        return " (on PickleballTV - login required)"

    def _load_free_court_codes(self) -> set:
        """Load free-to-watch PickleballTV court codes from config."""
        default_codes = {"CC"}
        config_file = "config.json"
        if not os.path.exists(config_file):
            return default_codes

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            configured_codes = config.get('pickleball_tv', {}).get('free_court_codes', [])
            if not isinstance(configured_codes, list):
                return default_codes

            normalized_codes = {
                str(code).strip().upper()
                for code in configured_codes
                if str(code).strip()
            }
            return normalized_codes or default_codes
        except Exception:
            return default_codes

