#!/usr/bin/env python3
"""
Notification handler for court assignment alerts.
Handles sending notifications when matches are assigned to courts via GroupMe.
"""

import json
import os

import requests

from pickleball_notifier.core.config import ConfigManager, MatchInfo
from pickleball_notifier.utils.logging import redact_sensitive_text
from pickleball_notifier.youtube.checker import YouTubeStreamChecker


class NotificationHandler:
    """Handles notifications for court assignments via GroupMe."""

    def __init__(self, config_manager: ConfigManager, bot_id: str = None):
        self.config_manager = config_manager
        self.bot_id = bot_id or self._load_bot_id()
        self.player_slug = self._load_player_slug()
        self.groupme_api_url = "https://api.groupme.com/v3/bots/post"
        self.stream_checker = YouTubeStreamChecker()

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PickleballCourtBot/1.0'
        })

    def _load_bot_id(self) -> str:
        """Load the GroupMe bot ID from config file."""
        config_file = "config.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found. "
                f"Please copy 'config.json.template' to '{config_file}' and add your bot ID."
            )

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            bot_id = config.get('groupme', {}).get('bot_id')
            if not bot_id:
                raise KeyError("bot_id not found in config file under 'groupme' section")
            return bot_id
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Error loading bot ID from config: {exc}")

    def _load_player_slug(self) -> str:
        """Load the player slug from config file."""
        config_file = "config.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found. "
                f"Please copy 'config.json.template' to '{config_file}' and add your configuration."
            )

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            player_slug = config.get('player', {}).get('slug')
            if not player_slug:
                raise KeyError("player.slug not found in config file")
            return player_slug
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Error loading player slug from config: {exc}")

    def send_notification(self, match: MatchInfo) -> bool:
        """Send notification for a court assignment via GroupMe."""
        try:
            message = self._create_notification_message(match)
            payload = {"bot_id": self.bot_id, "text": message}
            response = self.session.post(self.groupme_api_url, json=payload, timeout=10)
            response.raise_for_status()

            player_name = self.player_slug.replace('-', ' ').title()
            print(f"🔔 GROUPME NOTIFICATION SENT: {player_name} assigned to {match.court_title}")
            print(f"   Message: {message}")
            print(f"   Match URL: {match.url}")
            return True
        except requests.RequestException as exc:
            print(f"❌ Failed to send GroupMe notification for match {match.uuid}: {redact_sensitive_text(str(exc))}")
            return False
        except Exception as exc:
            print(f"❌ Unexpected error sending notification for match {match.uuid}: {redact_sensitive_text(str(exc))}")
            return False

    def _create_notification_message(self, match: MatchInfo) -> str:
        """Create an engaging notification message for GroupMe with YouTube stream info."""
        court = match.court_title
        player_name = self.player_slug.replace('-', ' ').title()
        player_info = self._build_player_info_string(match)

        base_messages = [
            f"🏓 {player_name} has been assigned to Court {court} and will be starting soon!{player_info}",
            f"🎾 Court {court} is ready for {player_name} - match starting soon!{player_info}",
            f"⚡ {player_name} is heading to Court {court} - get ready for some action!{player_info}",
            f"🔥 {player_name} has been assigned to Court {court} - the match is about to begin!{player_info}",
            f"🏆 Court {court} awaits {player_name} - let's see what they bring!{player_info}",
            f"💪 {player_name} is on Court {court} - time to show their skills!{player_info}",
            f"🚀 {player_name} has been assigned to Court {court} - the excitement begins now!{player_info}",
            f"⭐ Court {court} is {player_name}'s stage - the performance starts soon!{player_info}"
        ]

        try:
            stream_info = self.stream_checker.check_court_stream(court)
            message_index = hash(match.uuid) % len(base_messages)
            if stream_info['is_live'] and stream_info['stream_url']:
                return f"{base_messages[message_index]}\n\n📺 LIVE STREAM: {stream_info['stream_url']}"

            pickleball_tv_msg = self.stream_checker.get_pickleball_tv_message(court)
            return f"{base_messages[message_index]}{pickleball_tv_msg}"
        except Exception as exc:
            print(
                "   ⚠️  YouTube check failed for "
                f"{court}, using fallback message: {redact_sensitive_text(str(exc))}"
            )
            message_index = hash(match.uuid) % len(base_messages)
            return base_messages[message_index]

    def _build_player_info_string(self, match: MatchInfo) -> str:
        """Build a concise string with partner and opponent information."""
        parts = []
        if match.partner_name:
            parts.append(f"Partner: {match.partner_name}")

        if match.opponent_names:
            if len(match.opponent_names) == 1:
                parts.append(f"vs {match.opponent_names[0]}")
            elif len(match.opponent_names) == 2:
                parts.append(f"vs {match.opponent_names[0]} & {match.opponent_names[1]}")
            else:
                opponents_str = ", ".join(match.opponent_names[:-1]) + f" & {match.opponent_names[-1]}"
                parts.append(f"vs {opponents_str}")

        if parts:
            return f"\n\n👥 {' | '.join(parts)}"
        return ""

    def process_pending_notifications(self) -> int:
        """Process all pending notifications."""
        pending_matches = self.config_manager.get_pending_notifications()
        if not pending_matches:
            print("No pending notifications to process.")
            return 0

        print(f"Processing {len(pending_matches)} pending notifications...")
        sent_count = 0
        for match in pending_matches:
            if self.send_notification(match):
                self.config_manager.mark_as_notified(match.uuid)
                sent_count += 1

        self.config_manager.save_config()
        print(f"Successfully sent {sent_count}/{len(pending_matches)} notifications.")
        return sent_count

    def get_notification_summary(self) -> dict:
        """Get summary of notification status."""
        court_assigned = self.config_manager.get_court_assigned_matches()
        pending = self.config_manager.get_pending_notifications()
        notified = [match for match in court_assigned if match.notified]
        return {
            'total_court_assigned': len(court_assigned),
            'pending_notifications': len(pending),
            'notifications_sent': len(notified)
        }

