#!/usr/bin/env python3
"""
YouTube stream checker for PPA court assignments.
Checks if a court assignment has a live YouTube stream available.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import time


class YouTubeStreamChecker:
    """Checks for live YouTube streams for court assignments."""
    
    def __init__(self):
        self.base_youtube_url = "https://www.youtube.com/@PPAStreamedCourts/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.request_delay = 1.0  # seconds to prevent rate limiting
    
    def check_court_stream(self, court_assignment: str) -> Dict[str, any]:
        """
        Check if a court assignment has a live YouTube stream.
        
        Args:
            court_assignment: The court assignment (e.g., "SC1", "GS", "CC")
            
        Returns:
            Dict with:
            - is_live: bool - whether stream is live
            - stream_url: Optional[str] - full YouTube URL if live
            - error: Optional[str] - error message if check failed
        """
        try:
            # Construct search URL
            search_url = f"{self.base_youtube_url}?query={court_assignment}"
            
            print(f"🔍 Checking YouTube for live stream: {court_assignment}")
            print(f"   Search URL: {search_url}")
            
            # Fetch the search page
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the first ytd-item-section-renderer
            item_section = soup.find('ytd-item-section-renderer')
            
            if not item_section:
                print(f"   ⚠️  No search results found for {court_assignment}")
                return {
                    'is_live': False,
                    'stream_url': None,
                    'error': None
                }
            
            # Check if any result is live by looking for "watching" in metadata-line
            metadata_lines = item_section.find_all('div', {'id': 'metadata-line'})
            is_live = False
            
            for metadata_line in metadata_lines:
                if metadata_line and 'watching' in metadata_line.get_text().lower():
                    is_live = True
                    print(f"   ✅ Live stream detected for {court_assignment}")
                    break
            
            if not is_live:
                print(f"   ⚪ No live stream found for {court_assignment}")
                return {
                    'is_live': False,
                    'stream_url': None,
                    'error': None
                }
            
            # If live, find the stream URL
            thumbnail_link = item_section.find('a', {'id': 'thumbnail'})
            
            if thumbnail_link and thumbnail_link.get('href'):
                # Extract the video ID from the href
                href = thumbnail_link.get('href')
                if href.startswith('/watch?v='):
                    video_id = href.split('v=')[1].split('&')[0]
                    stream_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"   🎥 Live stream URL: {stream_url}")
                    return {
                        'is_live': True,
                        'stream_url': stream_url,
                        'error': None
                    }
                else:
                    print(f"   ⚠️  Unexpected href format: {href}")
                    return {
                        'is_live': True,
                        'stream_url': None,
                        'error': f"Unexpected href format: {href}"
                    }
            else:
                print(f"   ⚠️  Live stream detected but no thumbnail link found")
                return {
                    'is_live': True,
                    'stream_url': None,
                    'error': "Live stream detected but no thumbnail link found"
                }
                
        except requests.RequestException as e:
            error_msg = f"Network error checking YouTube: {e}"
            print(f"   ❌ {error_msg}")
            return {
                'is_live': False,
                'stream_url': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error parsing YouTube results: {e}"
            print(f"   ❌ {error_msg}")
            return {
                'is_live': False,
                'stream_url': None,
                'error': error_msg
            }
        finally:
            # Add delay to prevent rate limiting
            time.sleep(self.request_delay)
    
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
