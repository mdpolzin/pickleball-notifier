"""Notification layer modules."""

__all__ = ["NotificationHandler"]


def __getattr__(name: str):
    """Lazily expose notification handler symbols."""
    if name == "NotificationHandler":
        from pickleball_notifier.notifications.handler import NotificationHandler

        return NotificationHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
