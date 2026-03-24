"""Reusable helpers for concise unit tests."""

from typing import Any, Dict, List, Optional

from pickleball_notifier.core.config import MatchInfo


class DummyResponse:
    """Simple HTTP response stand-in for request mocking."""

    def __init__(self, payload: Optional[Dict[str, Any]] = None, raise_error: Optional[Exception] = None):
        self._payload = payload or {}
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def json(self) -> Dict[str, Any]:
        return self._payload


def build_match(
    uuid: str = "11111111-1111-1111-1111-111111111111",
    court_title: str = "SC1",
    partner_name: Optional[str] = None,
    opponent_names: Optional[List[str]] = None,
    notified: bool = False,
    match_completed: Optional[str] = None,
) -> MatchInfo:
    """Build MatchInfo with sensible defaults for tests."""
    return MatchInfo(
        uuid=uuid,
        url=f"https://pickleball.com/results/match/{uuid}",
        first_seen="2026-01-01T00:00:00+00:00",
        last_seen="2026-01-01T00:00:00+00:00",
        status="assigned",
        court_assigned=True,
        court_title=court_title,
        partner_name=partner_name,
        opponent_names=opponent_names,
        notified=notified,
        match_completed=match_completed,
    )

