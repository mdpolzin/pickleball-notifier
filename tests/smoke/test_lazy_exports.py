"""Coverage tests for lazy package exports."""

import pickleball_notifier
import pickleball_notifier.api as api
import pickleball_notifier.core as core
import pickleball_notifier.notifications as notifications
import pickleball_notifier.services as services
import pickleball_notifier.utils as utils
import pickleball_notifier.youtube as youtube


def test_root_package_lazy_exports() -> None:
    """Root package exposes expected public symbols lazily."""
    assert pickleball_notifier.MatchApiResult is not None
    assert pickleball_notifier.PickleballApiClient is not None
    assert pickleball_notifier.ConfigManager is not None
    assert pickleball_notifier.ExecutionRecord is not None
    assert pickleball_notifier.MatchInfo is not None
    assert pickleball_notifier.NotificationHandler is not None
    assert pickleball_notifier.PickleballPlayerScraper is not None
    assert pickleball_notifier.YouTubeStreamChecker is not None


def test_root_package_unknown_attribute_raises() -> None:
    """Unknown root package symbols raise AttributeError."""
    try:
        _ = pickleball_notifier.not_a_real_symbol
        assert False, "Expected AttributeError for unknown symbol"
    except AttributeError:
        pass


def test_subpackage_lazy_exports() -> None:
    """Subpackages expose expected lazy symbols."""
    assert api.MatchApiResult is not None
    assert api.PickleballApiClient is not None
    assert core.ConfigManager is not None
    assert core.ExecutionRecord is not None
    assert core.MatchInfo is not None
    assert notifications.NotificationHandler is not None
    assert services.PickleballPlayerScraper is not None
    assert utils.redact_sensitive_text is not None
    assert youtube.YouTubeStreamChecker is not None


def test_subpackage_unknown_attribute_raises() -> None:
    """Unknown subpackage symbols raise AttributeError."""
    modules = [api, core, notifications, services, utils, youtube]
    for module in modules:
        try:
            _ = module.not_a_real_symbol
            assert False, f"Expected AttributeError for unknown symbol in {module.__name__}"
        except AttributeError:
            pass
