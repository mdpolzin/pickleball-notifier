"""API layer modules."""

__all__ = ["MatchApiResult", "PickleballApiClient"]


def __getattr__(name: str):
    """Lazily expose API client symbols."""
    if name in {"MatchApiResult", "PickleballApiClient"}:
        from pickleball_notifier.api.client import MatchApiResult, PickleballApiClient

        return {"MatchApiResult": MatchApiResult, "PickleballApiClient": PickleballApiClient}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
