# Package Architecture

This project uses a layered package structure under `pickleball_notifier/`:

- `api`: external API client integrations
- `core`: domain models and configuration persistence
- `notifications`: notification orchestration and message composition
- `services`: application workflows and runnable entrypoints
- `youtube`: YouTube stream lookup integration
- `utils`: shared cross-cutting helpers

## Layer Responsibilities

- Keep I/O boundaries in `api`, `youtube`, and `notifications`.
- Keep state and records in `core`.
- Keep orchestration in `services`.
- Keep reusable helper logic in `utils`.

## Where New Code Goes

- New pickleball.com API calls or response parsing: `pickleball_notifier/api/`
- New config fields, match state, or persisted execution data: `pickleball_notifier/core/`
- New GroupMe/notification channels or message templates: `pickleball_notifier/notifications/`
- New workflow steps, scheduling flow, or top-level execution behavior: `pickleball_notifier/services/`
- New YouTube detection or stream-matching behavior: `pickleball_notifier/youtube/`
- Shared utility functions used by multiple layers: `pickleball_notifier/utils/`
- Tests should mirror this layering under `tests/` to keep ownership clear.

## Runtime Flow

```mermaid
flowchart TD
    serviceScraper["services.scraper.main"] --> configCore["core.config.ConfigManager"]
    serviceScraper --> notifyHandler["notifications.handler.NotificationHandler"]
    serviceScraper --> apiClient["api.client.PickleballApiClient"]
    notifyHandler --> ytChecker["youtube.checker.YouTubeStreamChecker"]
    apiClient --> pickleballApi["pickleball.com API"]
    ytChecker --> youtubeApi["YouTube Data API"]
    notifyHandler --> groupmeApi["GroupMe Bot API"]
```

## Entry Point

Use:

`make run`
