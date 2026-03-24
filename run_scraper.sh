#!/bin/bash
#
# Pickleball Scraper Runner Script
# Self-healing cron wrapper:
# - runs only during sensible hours (8AM - 11PM ET)
# - bootstraps .venv if missing
# - ensures project/dependencies are installed in the venv
#

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

PYTHON_BIN=".venv/bin/python"
PIP_BIN=".venv/bin/pip"

# Check if we're in sensible hours (8AM - 11PM Eastern Time)
# Get current time in Eastern Time (handles both EST and EDT automatically)
CURRENT_HOUR=$(TZ='America/New_York' date +%H)

# Convert to integer for comparison
CURRENT_HOUR=$((10#$CURRENT_HOUR))

# Check if current hour is between 8 (8AM) and 22 (10PM)
if [ $CURRENT_HOUR -lt 8 ] || [ $CURRENT_HOUR -gt 22 ]; then
    # Outside sensible hours - exit silently
    exit 0
fi

ensure_environment() {
    # Create venv automatically on first run.
    if [ ! -x "$PYTHON_BIN" ]; then
        python3 -m venv .venv
    fi

    # Keep packaging toolchain fresh enough for pyproject/editable installs.
    "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

    # If runtime dependencies are missing, install the project.
    if ! "$PYTHON_BIN" -c "import requests, bs4, pickleball_notifier" >/dev/null 2>&1; then
        # Try editable install first; if host packaging stack still rejects it, fall back to non-editable.
        if ! "$PIP_BIN" install -e .; then
            "$PIP_BIN" install .
        fi
    fi
}

if ! ensure_environment >> scraper.log 2>&1; then
    {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Environment bootstrap failed"
    } >> scraper.log
    exit 1
fi

# Run the scraper with logging
make run >> scraper.log 2>&1
