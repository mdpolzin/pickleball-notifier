#!/usr/bin/env python3
"""
Configuration management for the pickleball scraper.
Handles caching of match status and execution history.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class MatchInfo:
    """Information about a match."""
    uuid: str
    url: str
    first_seen: str
    last_seen: str
    status: str  # 'future', 'assigned'
    last_checked: Optional[str] = None
    court_assigned: bool = False
    court_title: Optional[str] = None
    match_completed: Optional[str] = None
    notified: bool = False
    notification_timestamp: Optional[str] = None


@dataclass
class ExecutionRecord:
    """Record of a script execution."""
    timestamp: str
    matches_found: int
    new_matches: int
    future_matches: int
    assigned_matches: int
    court_assignments_checked: int = 0
    court_assignments_found: int = 0
    notifications_sent: int = 0
    stale_matches_removed: int = 0


class ConfigManager:
    """Manages configuration and caching for the scraper."""
    
    def __init__(self, config_file: str = "scraper_config.json"):
        self.config_file = config_file
        self.matches: Dict[str, MatchInfo] = {}
        self.execution_history: List[ExecutionRecord] = []
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            self.save_config()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load matches
            self.matches = {}
            for uuid, match_data in data.get('matches', {}).items():
                # Handle old status values
                if match_data.get('status') == 'current':
                    match_data['status'] = 'assigned'
                elif match_data.get('status') == 'unknown':
                    match_data['status'] = 'future'
                
                self.matches[uuid] = MatchInfo(**match_data)
            
            # Load execution history
            self.execution_history = []
            for record_data in data.get('execution_history', []):
                # Handle old format with 'completed_matches' field
                if 'completed_matches' in record_data:
                    # Convert old format to new format
                    new_record_data = {
                        'timestamp': record_data['timestamp'],
                        'matches_found': record_data['matches_found'],
                        'new_matches': record_data['new_matches'],
                        'future_matches': record_data.get('unknown_matches', 0),
                        'assigned_matches': record_data.get('completed_matches', 0)
                    }
                    self.execution_history.append(ExecutionRecord(**new_record_data))
                else:
                    # New format
                    self.execution_history.append(ExecutionRecord(**record_data))
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading config: {e}")
            print("Starting with empty configuration")
            self.matches = {}
            self.execution_history = []
    
    def save_config(self) -> None:
        """Save configuration to file."""
        data = {
            'matches': {uuid: asdict(match) for uuid, match in self.matches.items()},
            'execution_history': [asdict(record) for record in self.execution_history],
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def update_matches(self, match_urls: List[str]) -> Dict[str, int]:
        """
        Update match information with new URLs.
        
        Args:
            match_urls: List of match URLs found in current execution
            
        Returns:
            Dictionary with counts of new, existing, completed, and future matches
        """
        current_time = self.get_current_timestamp()
        new_matches = 0
        existing_matches = 0
        
        # Extract UUIDs from URLs
        current_uuids = set()
        for url in match_urls:
            if '/results/match/' in url:
                uuid = url.split('/results/match/')[-1]
                current_uuids.add(uuid)
        
        # Update existing matches
        for uuid in current_uuids:
            url = f"https://pickleball.com/results/match/{uuid}"
            if uuid in self.matches:
                # Update last_seen for existing matches
                self.matches[uuid].last_seen = current_time
                existing_matches += 1
            else:
                # Add new match
                self.matches[uuid] = MatchInfo(
                    uuid=uuid,
                    url=url,
                    first_seen=current_time,
                    last_seen=current_time,
                    status='future'
                )
                new_matches += 1
        
        # Remove matches that are no longer found (they were completed)
        # This is handled by remove_stale_matches method
        
        return {
            'new_matches': new_matches,
            'existing_matches': existing_matches,
            'total_matches': len(self.matches),
            'future_matches': len([m for m in self.matches.values() if m.status == 'future']),
            'assigned_matches': len([m for m in self.matches.values() if m.status == 'assigned'])
        }
    
    def record_execution(self, matches_found: int, match_counts: Dict[str, int], 
                        court_assignments_checked: int = 0, court_assignments_found: int = 0,
                        notifications_sent: int = 0, stale_matches_removed: int = 0) -> None:
        """Record this execution in the history."""
        record = ExecutionRecord(
            timestamp=self.get_current_timestamp(),
            matches_found=matches_found,
            new_matches=match_counts['new_matches'],
            future_matches=match_counts['future_matches'],
            assigned_matches=match_counts['assigned_matches'],
            court_assignments_checked=court_assignments_checked,
            court_assignments_found=court_assignments_found,
            notifications_sent=notifications_sent,
            stale_matches_removed=stale_matches_removed
        )
        
        self.execution_history.append(record)
        
        # Keep only last 100 executions to prevent file from growing too large
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def get_match_summary(self) -> Dict[str, any]:
        """Get a summary of all matches."""
        return {
            'total_matches': len(self.matches),
            'future_matches': len([m for m in self.matches.values() if m.status == 'future']),
            'assigned_matches': len([m for m in self.matches.values() if m.status == 'assigned']),
            'recent_executions': len([e for e in self.execution_history 
                                    if (datetime.now(timezone.utc) - datetime.fromisoformat(e.timestamp)).days < 1])
        }
    
    def get_future_matches(self) -> List[MatchInfo]:
        """Get all future matches (no court assigned yet)."""
        return [match for match in self.matches.values() if match.status == 'future']
    
    def get_assigned_matches(self) -> List[MatchInfo]:
        """Get all assigned matches (court assigned)."""
        return [match for match in self.matches.values() if match.status == 'assigned']
    
    def get_matches_needing_court_check(self) -> List[MatchInfo]:
        """Get matches that need court assignment checking (future status)."""
        return [match for match in self.matches.values() if match.status == 'future']
    
    def update_court_assignment(self, uuid: str, court_title: str, assigned: bool, match_completed: Optional[str] = None) -> None:
        """Update court assignment information for a match."""
        if uuid in self.matches:
            self.matches[uuid].court_assigned = assigned
            self.matches[uuid].court_title = court_title if assigned else None
            self.matches[uuid].match_completed = match_completed
            self.matches[uuid].last_checked = self.get_current_timestamp()
            
            # Update status based on court assignment
            if assigned and self.matches[uuid].status == 'future':
                self.matches[uuid].status = 'assigned'
            
            # If match is completed, mark as notified to prevent future notifications
            if match_completed:
                self.matches[uuid].notified = True
                self.matches[uuid].notification_timestamp = self.get_current_timestamp()
    
    def mark_as_notified(self, uuid: str) -> None:
        """Mark a match as notified."""
        if uuid in self.matches:
            self.matches[uuid].notified = True
            self.matches[uuid].notification_timestamp = self.get_current_timestamp()
    
    def get_court_assigned_matches(self) -> List[MatchInfo]:
        """Get all matches that have been assigned to a court."""
        return [match for match in self.matches.values() if match.court_assigned]
    
    def get_pending_notifications(self) -> List[MatchInfo]:
        """Get matches with court assignments that haven't been notified yet and aren't completed."""
        return [match for match in self.matches.values() 
                if match.court_assigned and not match.notified and not match.match_completed]
    
    def remove_stale_matches(self, current_uuids: Set[str]) -> int:
        """
        Remove matches that are no longer present on the page.
        
        Args:
            current_uuids: Set of UUIDs currently found on the page
            
        Returns:
            Number of matches removed
        """
        # Find matches that are no longer on the page
        stale_uuids = set(self.matches.keys()) - current_uuids
        
        if not stale_uuids:
            return 0
        
        print(f"Removing {len(stale_uuids)} stale matches from configuration...")
        
        # Log removed matches for debugging
        for uuid in stale_uuids:
            match = self.matches[uuid]
            print(f"  - Removing stale match: {uuid} (status: {match.status}, court: {match.court_title or 'none'})")
        
        # Remove stale matches
        for uuid in stale_uuids:
            del self.matches[uuid]
        
        return len(stale_uuids)
    
    def cleanup_old_execution_history(self, max_records: int = 100) -> int:
        """
        Remove old execution history records to prevent file bloat.
        
        Args:
            max_records: Maximum number of execution records to keep
            
        Returns:
            Number of records removed
        """
        if len(self.execution_history) <= max_records:
            return 0
        
        records_to_remove = len(self.execution_history) - max_records
        print(f"Removing {records_to_remove} old execution history records...")
        
        # Keep the most recent records
        self.execution_history = self.execution_history[-max_records:]
        
        return records_to_remove
    
    def get_cleanup_summary(self) -> Dict[str, int]:
        """Get summary of cleanup operations that could be performed."""
        return {
            'total_matches': len(self.matches),
            'future_matches': len([m for m in self.matches.values() if m.status == 'future']),
            'assigned_matches': len([m for m in self.matches.values() if m.status == 'assigned']),
            'notified_matches': len([m for m in self.matches.values() if m.notified]),
            'execution_history_records': len(self.execution_history)
        }
    
    def get_recent_execution_summary(self, hours: int = 24) -> Dict[str, any]:
        """Get summary of recent executions with meaningful activity."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        
        recent_executions = [
            e for e in self.execution_history 
            if datetime.fromisoformat(e.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_executions:
            return {
                'total_executions': 0,
                'active_executions': 0,
                'total_court_assignments_found': 0,
                'total_notifications_sent': 0,
                'total_stale_removed': 0
            }
        
        # Count executions that had meaningful activity
        active_executions = [
            e for e in recent_executions 
            if (e.court_assignments_found > 0 or e.notifications_sent > 0 or 
                e.stale_matches_removed > 0 or e.new_matches > 0)
        ]
        
        return {
            'total_executions': len(recent_executions),
            'active_executions': len(active_executions),
            'total_court_assignments_found': sum(e.court_assignments_found for e in recent_executions),
            'total_notifications_sent': sum(e.notifications_sent for e in recent_executions),
            'total_stale_removed': sum(e.stale_matches_removed for e in recent_executions)
        }
