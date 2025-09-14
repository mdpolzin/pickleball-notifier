#!/bin/bash
#
# Pickleball Scraper Runner Script
# This script runs the pickleball scraper with proper environment setup
# Only runs during sensible hours (8AM - 11PM Eastern Time)
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first:" >&2
    echo "  python3 -m venv venv" >&2
    echo "  source venv/bin/activate" >&2
    echo "  pip install -r requirements.txt" >&2
    exit 1
fi

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

# Activate virtual environment
source venv/bin/activate

# Run the scraper with logging
python scraper.py >> scraper.log 2>&1
