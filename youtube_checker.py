#!/usr/bin/env python3
"""
YouTube stream checker for PPA court assignments.
Checks if a court assignment has a live YouTube stream available.
"""

import requests
from typing import Optional, Dict
import time
import xml.etree.ElementTree as ET
import json
import os


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
        self.request_delay = 1.0  # seconds to prevent rate limiting
    
    def _check_youtube_api(self, court_assignment: str) -> Dict[str, any]:
        """
        Check for live streams using YouTube Data API v3.
        This is the most reliable method for detecting live streams.
        
        Args:
            court_assignment: The court assignment (e.g., "SC1", "GS", "CC")
            
        Returns:
            Dict with stream information
        """
        try:
            # YouTube Data API v3 endpoint for searching live streams
            # Channel ID for PPA Streamed Courts
            channel_id = "UCwxrKD60cB__M6nhdH0UW0w"
            
            print(f"   🔍 Checking YouTube API for {court_assignment}...")
            
            # Search for live streams in the channel
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'eventType': 'live',  # Only search for live streams
                'type': 'video',
                'q': f"court {court_assignment}",  # Search for "court 9" etc.
                'key': self._get_api_key()  # We'll need to add this method
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we found any live streams
            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                    title = item['snippet']['title'].lower()
                    video_id = item['id']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Check if this video matches our court assignment
                    if f" {court_assignment} ".lower() in title:
                        print(f"   ✅ Found live stream via API: {item['snippet']['title']}")
                        print(f"   🎥 Live stream URL: {video_url}")
                        return {
                            'is_live': True,
                            'stream_url': video_url,
                            'error': None
                        }
            
            print(f"   ⚪ No live stream found for {court_assignment} via YouTube API")
            return {
                'is_live': False,
                'stream_url': None,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"YouTube API error: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {
                'is_live': False,
                'stream_url': None,
                'error': error_msg
            }
    
    def _get_api_key(self) -> str:
        """
        Get YouTube API key from config file.
        
        Returns:
            YouTube API key string
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If API key is not found in config
        """
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
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading YouTube API key from config: {e}")
    
    def check_court_stream(self, court_assignment: str) -> Dict[str, any]:
        """
        Check if a court assignment has a live YouTube stream.
        Uses YouTube Data API v3 as the primary method for accuracy.
        
        Args:
            court_assignment: The court assignment (e.g., "SC1", "GS", "CC")
            
        Returns:
            Dict with:
            - is_live: bool - whether stream is live
            - stream_url: Optional[str] - full YouTube URL if live
            - error: Optional[str] - error message if check failed
        """
        print(f"🔍 Checking YouTube for live stream: {court_assignment}")
        
        # Use YouTube API as primary method - most reliable for live stream detection
        return self._check_youtube_api(court_assignment)
    
    def get_pickleball_tv_message(self, court_assignment: str) -> str:
        """
        Get the appropriate PickleballTV message based on court assignment.
        
        Args:
            court_assignment: The court assignment
            
        Returns:
            Message about PickleballTV availability
        """
        if court_assignment == "CC":
            return " (free to watch on PickleballTV)"
        else:
            return " (on PickleballTV - login required)"
