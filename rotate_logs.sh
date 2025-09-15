#!/bin/bash
#
# Simple Log Rotation Script for Pickleball Scraper
# Achieves the same results as logrotate without requiring the logrotate utility
# Keeps 7 days of logs with compression
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

# Function to compress a file if gzip is available
compress_file() {
    local file="$1"
    if command -v gzip >/dev/null 2>&1; then
        gzip "$file"
        echo "$(date): Compressed $file"
    else
        echo "$(date): gzip not available, keeping $file uncompressed"
    fi
}

# Rotate logs: move each existing log up by one number
# Start from the highest number and work backwards to avoid conflicts

# Remove the oldest log (scraper.log.7.gz) if it exists
if [ -f "scraper.log.7.gz" ]; then
    rm "scraper.log.7.gz"
    echo "$(date): Removed oldest log file (scraper.log.7.gz)"
fi

# Move existing compressed logs up by one number (6->7, 5->6, etc.)
for i in {6..1}; do
    if [ -f "scraper.log.$i.gz" ]; then
        mv "scraper.log.$i.gz" "scraper.log.$((i+1)).gz"
        echo "$(date): Moved scraper.log.$i.gz to scraper.log.$((i+1)).gz"
    fi
done

# Compress and move the current log to scraper.log.1.gz
if [ -f "scraper.log" ]; then
    # First compress the current log
    compress_file "scraper.log"
    
    # Then move the compressed file to .1 position
    if [ -f "scraper.log.gz" ]; then
        mv "scraper.log.gz" "scraper.log.1.gz"
        echo "$(date): Moved compressed log to scraper.log.1.gz"
    fi
fi

echo "$(date): Log rotation completed successfully"
