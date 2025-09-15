#!/bin/bash
#
# Graceful Log Rotation Script for Pickleball Scraper
# Uses logrotate for proper log rotation with compression and better handling
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if we're in the 3AM Eastern Time hour
# Get current hour in Eastern Time (handles both EST and EDT automatically)
CURRENT_HOUR=$(TZ='America/New_York' date +%H)

# Convert to integer for comparison
CURRENT_HOUR=$((10#$CURRENT_HOUR))

# Only rotate logs at 3AM Eastern
if [ $CURRENT_HOUR -ne 3 ]; then
    # Not 3AM - exit silently
    exit 0
fi

# Check if scraper.log exists
if [ ! -f "scraper.log" ]; then
    # No log file to rotate - exit silently
    exit 0
fi

# Use logrotate for graceful rotation
# -f flag to force rotation even if not due
# Run from project directory to use relative paths in config
logrotate -f pickleball-scraper.logrotate

echo "$(date): Log rotation completed using logrotate"
