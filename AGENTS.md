# Pickleball Notifier - Agent Guidelines

This file defines default expectations for AI agents operating in this repository. Prefer being safe, minimal, and consistent with the existing codebase.

## Core Principles
- Be conservative: avoid large refactors unless explicitly requested.
- Be correct: if requirements are ambiguous, ask clarifying questions before changing code.
- Be secure: never expose or commit secrets (e.g., `config.json`, API keys, tokens). Treat any credentials as sensitive.
- Be consistent: follow existing patterns, naming conventions, and architecture already used in this repo.

## Change Management
- Make the smallest change that satisfies the request.
- If a change affects behavior, call out expected impact and any edge cases.
- Do not create git commits or push to remotes unless the user explicitly asks.
- Avoid destructive git operations (e.g., resets, force pushes) unless explicitly requested.

## Tool Usage Expectations
- Prefer read-only exploration (`ReadFile`, `Glob`, `rg`) to understand the current implementation before editing.
- Use `ApplyPatch` for targeted code edits.
- Use shell commands only when necessary for running scripts, installing dependencies, or inspecting runtime behavior.
- After substantive edits, run lints (and tests if present) and address any newly introduced issues.

## Python Conventions
- Follow PEP 8 style.
- Prefer explicitness over cleverness; keep functions small and focused.
- Use type hints where they improve clarity, especially for public functions and key data structures.
- Maintain graceful error handling for network/API calls and file I/O.

## Contribution Placement
- Put new pickleball.com HTTP integration code in `pickleball_notifier/api/`.
- Put configuration/state dataclasses and persistence logic in `pickleball_notifier/core/`.
- Put notification delivery/message composition in `pickleball_notifier/notifications/`.
- Put cross-module orchestration and runnable workflows in `pickleball_notifier/services/`.
- Put YouTube-specific stream lookup code in `pickleball_notifier/youtube/`.
- Put generic helpers reused across layers in `pickleball_notifier/utils/`.
- Keep unit tests aligned with package layers under `tests/` (e.g., `tests/api`, `tests/core`, `tests/services`).

## Documentation Requirements
- When behavior, workflow, architecture, or package layout changes, update `README.md` in the same change.
- When layering or module responsibility changes, update `docs/architecture.md` in the same change.
- When contributor/agent expectations change, update `AGENTS.md` in the same change.
- Keep run instructions normalized to Make targets (`make run`, `make test`, `make coverage`, `make lint`) instead of direct module commands.

## Verification Checklist (Typical)
- Code compiles / runs (where applicable).
- No new lint errors are introduced.
- `make lint` passes as written.
- `make coverage` passes as written.
- If relevant, run the main workflow using Make targets (e.g., `make run`) with a safe, non-secret config.

