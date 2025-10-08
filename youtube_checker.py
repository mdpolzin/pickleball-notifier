#!/usr/bin/env python3
"""
YouTube stream checker for PPA court assignments.
Checks if a court assignment has a live YouTube stream available.
"""

import requests
from typing import Optional, Dict
import time
import xml.etree.ElementTree as ET


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
    
    def _check_rss_feed(self, court_assignment: str) -> Dict[str, any]:
        """
        Primary method: Check YouTube RSS feed for live streams.
        RSS feeds are more reliable and faster than web scraping.
        Finding a result here indicates it's a live stream.
        
        Args:
            court_assignment: The court assignment (e.g., "SC1", "GS", "CC")
            
        Returns:
            Dict with stream information
        """
        try:
            # YouTube channel RSS feed URL for PPA Streamed Courts
            rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCwxrKD60cB__M6nhdH0UW0w"
            
            print(f"   📡 Checking RSS feed for {court_assignment}...")
            
            response = self.session.get(rss_url, timeout=10)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            # Look for recent videos that might match our court assignment
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('.//{http://www.w3.org/2005/Atom}title')
                link = entry.find('.//{http://www.w3.org/2005/Atom}link')
                
                if title is not None and link is not None:
                    title_text = title.text.lower()
                    video_url = link.get('href')
                    
                    # Check if this video mentions our court assignment
                    # Since RSS feeds typically only show recent/active content,
                    # finding a match here indicates it's likely a live stream
                    if court_assignment.lower() in title_text:
                        print(f"   ✅ Found live stream in RSS: {title.text}")
                        print(f"   🎥 Live stream URL: {video_url}")
                        return {
                            'is_live': True,
                            'stream_url': video_url,
                            'error': None
                        }
            
            print(f"   ⚪ No live stream found for {court_assignment} in RSS feed")
            return {
                'is_live': False,
                'stream_url': None,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"RSS feed error: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {
                'is_live': False,
                'stream_url': None,
                'error': error_msg
            }
    
    def check_court_stream(self, court_assignment: str) -> Dict[str, any]:
        """
        Check if a court assignment has a live YouTube stream.
        Uses RSS feed as the primary method for reliability and speed.
        
        Args:
            court_assignment: The court assignment (e.g., "SC1", "GS", "CC")
            
        Returns:
            Dict with:
            - is_live: bool - whether stream is live
            - stream_url: Optional[str] - full YouTube URL if live
            - error: Optional[str] - error message if check failed
        """
        print(f"🔍 Checking YouTube for live stream: {court_assignment}")
        
        # Use RSS feed as primary method - it's more reliable and faster
        return self._check_rss_feed(court_assignment)
    
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
