VENV_BIN ?= .venv/bin
PYTHON ?= $(VENV_BIN)/python
PIP ?= $(VENV_BIN)/pip
COV_FAIL_UNDER ?= 100

.PHONY: help install run lint lint-fix test coverage ci

help:
	@echo "Available targets:"
	@echo "  install  - Install project in editable mode"
	@echo "  run      - Run scraper via package module"
	@echo "  lint     - Run Ruff Python linter"
	@echo "  lint-fix - Run Ruff linter with auto-fixes"
	@echo "  test     - Run test suite"
	@echo "  coverage - Run tests with coverage (fails under $(COV_FAIL_UNDER)%)"
	@echo "  ci       - Run lint and coverage checks"

install:
	$(PIP) install -e .

run:
	$(PYTHON) -m pickleball_notifier.services.scraper

lint:
	$(PYTHON) -m ruff check .

lint-fix:
	$(PYTHON) -m ruff check . --fix

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=pickleball_notifier --cov-report=term-missing --cov-fail-under=$(COV_FAIL_UNDER)

ci: lint coverage

