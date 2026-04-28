#!/usr/bin/env python3
"""
Notification handler for court assignment alerts and match result posts.
Sends GroupMe messages when courts are assigned and when matches finish.
"""

import json
import os
import uuid
from typing import Optional

import requests

from pickleball_notifier.core.config import ConfigManager, MatchInfo
from pickleball_notifier.utils.logging import redact_sensitive_text
from pickleball_notifier.youtube.checker import YouTubeStreamChecker

GROUPME_API_BASE = "https://api.groupme.com/v3"


class NotificationHandler:
    """Handles court-assignment and match-result notifications via GroupMe."""

    def __init__(
        self,
        config_manager: ConfigManager,
        subgroup_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.config_manager = config_manager
        self.subgroup_id = (
            subgroup_id if subgroup_id is not None else self._load_subgroup_id()
        )
        self.access_token = (
            access_token if access_token is not None else self._load_access_token()
        )
        self.player_slug = self._load_player_slug()
        self.stream_checker = YouTubeStreamChecker()

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PickleballNotifier/1.0'
        })

    def _load_subgroup_id(self) -> str:
        """Load the GroupMe topic/subgroup ID from config (used as the group id for messages)."""
        config_file = "config.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found. "
                f"Please copy 'config.json.template' to '{config_file}' and add your credentials."
            )

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            sid = config.get('groupme', {}).get('subgroup_id')
            if not sid:
                raise KeyError(
                    "subgroup_id not found in config file under 'groupme' section"
                )
            return sid
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Error loading subgroup_id from config: {exc}")

    def _load_access_token(self) -> str:
        """Load the GroupMe user access token from config."""
        config_file = "config.json"
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file '{config_file}' not found. "
                f"Please copy 'config.json.template' to '{config_file}' and add your credentials."
            )

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            token = config.get('groupme', {}).get('access_token')
            if not token:
                raise KeyError(
                    "access_token not found in config file under 'groupme' section"
                )
            return token
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file: {exc}")
        except Exception as exc:
            raise RuntimeError(f"Error loading access_token from config: {exc}")

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

    def _post_groupme_message(self, text: str, match_uuid: str) -> bool:
        """Send text to the configured GroupMe topic."""
        try:
            url = f"{GROUPME_API_BASE}/groups/{self.subgroup_id}/messages"
            payload = {
                "message": {
                    "source_guid": str(uuid.uuid4()),
                    "text": text,
                }
            }
            response = self.session.post(
                url,
                params={"token": self.access_token},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            print(
                f"❌ Failed to send GroupMe message for match {match_uuid}: "
                f"{redact_sensitive_text(str(exc))}"
            )
            return False
        except Exception as exc:
            print(
                f"❌ Unexpected error sending GroupMe message for match {match_uuid}: "
                f"{redact_sensitive_text(str(exc))}"
            )
            return False

    def send_notification(self, match: MatchInfo) -> bool:
        """Send notification for a court assignment via GroupMe."""
        try:
            message = self._create_notification_message(match)
            if not self._post_groupme_message(message, match.uuid):
                return False

            player_name = self.player_slug.replace('-', ' ').title()
            print(f"🔔 GROUPME NOTIFICATION SENT: {player_name} assigned to {match.court_title}")
            print(f"   Message: {message}")
            print(f"   Match URL: {match.url}")
            return True
        except Exception as exc:
            print(
                f"❌ Unexpected error sending court notification for match {match.uuid}: "
                f"{redact_sensitive_text(str(exc))}"
            )
            return False

    def send_match_result_notification(self, match: MatchInfo) -> bool:
        """Send a GroupMe message summarizing a completed match."""
        try:
            message = self._create_match_result_message(match)
            if not self._post_groupme_message(message, match.uuid):
                return False

            court = match.court_title or ""
            print(f"🏁 GROUPME RESULT SENT: Court {court} — match {match.uuid}")
            print(f"   Message: {message}")
            print(f"   Match URL: {match.url}")
            return True
        except Exception as exc:
            print(
                f"❌ Unexpected error sending result notification for match {match.uuid}: "
                f"{redact_sensitive_text(str(exc))}"
            )
            return False

    def _create_match_result_message(self, match: MatchInfo) -> str:
        """Compose text for a finished match using API completion data."""
        player_name = self.player_slug.replace('-', ' ').title()
        court = match.court_title or "?"
        lines = [
            f"🏁 Match finished — Court {court}",
            "",
            f"{player_name}",
            "",
        ]

        if match.player_won is True:
            outcome = "✅ Won"
        elif match.player_won is False:
            outcome = "Lost"
        else:
            outcome = "Unable to determine win/loss (player not matched to a team in API data)"
        lines.append(f"📊 Result: {outcome}")

        if match.game_score_lines:
            lines.append("")
            lines.append("📋 Score by game:")
            for row in match.game_score_lines:
                lines.append(f"• {row}")

        info = self._build_player_info_string(match).strip()
        if info:
            lines.extend(["", info.strip()])

        lines.append("")
        lines.append(f"🔗 Match URL: {match.url}")
        return "\n".join(lines)

    @staticmethod
    def _append_pickleball_match_link(body: str, match: MatchInfo) -> str:
        """Append the results match URL line (same label as completion posts)."""
        return f"{body.rstrip()}\n\n🔗 Match URL: {match.url}"

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
                text = (
                    f"{base_messages[message_index]}\n\n"
                    f"📺 LIVE STREAM: {stream_info['stream_url']}"
                )
                return self._append_pickleball_match_link(text, match)

            pickleball_tv_msg = self.stream_checker.get_pickleball_tv_message(court)
            text = f"{base_messages[message_index]}{pickleball_tv_msg}"
            return self._append_pickleball_match_link(text, match)
        except Exception as exc:
            print(
                "   ⚠️  YouTube check failed for "
                f"{court}, using fallback message: {redact_sensitive_text(str(exc))}"
            )
            message_index = hash(match.uuid) % len(base_messages)
            return self._append_pickleball_match_link(base_messages[message_index], match)

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

    def process_pending_completion_notifications(self) -> int:
        """Post GroupMe summaries for matches that finished and have not been posted yet."""
        pending = self.config_manager.get_pending_completion_notifications()
        if not pending:
            print("No pending match result notifications to process.")
            return 0

        print(f"Processing {len(pending)} pending match result notification(s)...")
        sent_count = 0
        for match in pending:
            if self.send_match_result_notification(match):
                self.config_manager.mark_completion_notified(match.uuid)
                sent_count += 1

        self.config_manager.save_config()
        print(
            f"Successfully sent {sent_count}/{len(pending)} match result notification(s)."
        )
        return sent_count

    def get_notification_summary(self) -> dict:
        """Get summary of notification status."""
        court_assigned = self.config_manager.get_court_assigned_matches()
        pending = self.config_manager.get_pending_notifications()
        notified = [match for match in court_assigned if match.notified]
        pending_completion = self.config_manager.get_pending_completion_notifications()
        completion_sent = sum(1 for m in court_assigned if m.completion_notified)

        return {
            'total_court_assigned': len(court_assigned),
            'pending_notifications': len(pending),
            'notifications_sent': len(notified),
            'pending_completion_notifications': len(pending_completion),
            'completion_notifications_sent': completion_sent,
        }

