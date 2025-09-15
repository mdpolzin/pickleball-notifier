# Pickleball Player Scraper

A web scraper to extract tournament results links from pickleball.com player pages with configuration-based caching for match status tracking.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
```bash
# Copy the template config file
cp config.json.template config.json

# Edit config.json and add your configuration:
# - Replace "YOUR_GROUPME_BOT_ID_HERE" with your actual GroupMe bot ID
# - Update the player slug if you want to track a different player
```

## Usage

Run the scraper to check the configured player's tournament results:

```bash
source venv/bin/activate
python scraper.py
```

The scraper will:
1. Fetch the configured player's page at `pickleball.com/players/{player_slug}`
2. Find the div containing "Tournament Results"
3. Extract only "Results" links with UUID format (`results/match/<uuid>`)
4. Check court assignments for future matches via API
5. Process notifications for newly assigned matches
6. Track match status in configuration file for future runs
7. Display filtered results and configuration summary

## Features

- **Filtered Results**: Only extracts "Results" links with valid UUID format
- **Configuration Caching**: Tracks match status across executions
- **Match Status Tracking**: Distinguishes between completed and future matches
- **Execution History**: Records each run with timestamps and statistics
- **Persistent Storage**: Saves configuration to `scraper_config.json`
- **Automatic Cleanup**: Removes stale matches and old execution history to prevent file bloat
- **Smart Court Checking**: Only checks court assignments for matches that need verification
- **Integrated Notifications**: Automatically processes notifications for court assignments
- **GroupMe Integration**: Sends engaging notifications to GroupMe group chat
- **YouTube Stream Detection**: Automatically checks for live YouTube streams and includes links
- **Smart Fallback**: Gracefully falls back to PickleballTV messages when YouTube streams aren't available
- **Race Condition Free**: Single script execution eliminates file access conflicts

## Configuration System

The scraper maintains a configuration file (`scraper_config.json`) that tracks:
- **Match Information**: UUID, URL, first/last seen timestamps, status, court assignments
- **Execution History**: Timestamp, matches found, new matches, completed matches
- **Status Tracking**: 
  - `future`: Matches currently visible but no court assigned yet (potential future matches)
  - `assigned`: Matches with court assigned (active matches, ready for notification)

## Files

- `scraper.py` - Main scraper implementation with integrated API and notifications
- `config.py` - Configuration management system with cleanup functionality
- `api_client.py` - API client for court assignment checking
- `notification_handler.py` - Notification system for court assignments
- `requirements.txt` - Python dependencies
- `scraper_config.json` - Persistent configuration storage (auto-generated)

## API Integration

The scraper now includes API integration to check court assignments:

- **Endpoint**: `https://pickleball.com/api/v1/results/getResultMatchInfos?id=<UUID>`
- **Court Detection**: Checks `data[0].court_title` field
- **Rate Limiting**: 0.5 second delay between API calls
- **Error Handling**: Graceful handling of API failures

## Integrated Workflow

- **Single Script Execution**: All processing happens in one atomic operation
- **No Race Conditions**: Eliminates file access conflicts between separate scripts
- **Automatic Notifications**: Court assignment notifications are processed immediately
- **GroupMe Integration**: Posts engaging messages to GroupMe group chat
- **YouTube Stream Detection**: Checks for live streams and includes direct links
- **Smart Fallback System**: Gracefully handles YouTube API failures
- **Efficient Processing**: Only checks court assignments for matches that need it
- **Engaging Messages**: Variety of fun, emoji-rich notification messages

## Usage Examples

### Basic Scraping
```bash
source venv/bin/activate
python scraper.py
```


### Automated Execution (Cron Job)

To run the scraper automatically every minute using cron:

#### 1. Get the absolute path to your project
```bash
# From your project directory, get the full path
pwd
# Example output: /Users/michaelpolzin/Documents/code/pickleball-notifier
```

#### 2. Test the included wrapper script
The project includes a `run_scraper.sh` script that handles environment setup and logging:

```bash
# Test the script manually first
./run_scraper.sh

# Check if it worked
tail -f scraper.log
```

**Note**: The script includes intelligent time filtering and will only run during sensible hours (8AM - 11PM Eastern Time). If you test it outside these hours, it will exit silently without running the scraper.

#### 3. Set up the cron jobs
```bash
# Edit your crontab
crontab -e

# Add these lines (replace with your actual path):
# Run scraper every minute
* * * * * /Users/michaelpolzin/Documents/code/pickleball-notifier/run_scraper.sh

# Rotate logs daily at 3AM Eastern
0 * * * * /Users/michaelpolzin/Documents/code/pickleball-notifier/rotate_logs.sh

# Save and exit (Ctrl+X in nano, :wq in vim)
```

#### 4. Verify the cron job
```bash
# Check if cron job was added
crontab -l

# Monitor the log file
tail -f scraper.log

# Check cron service status (macOS)
sudo launchctl list | grep cron
```

#### Important Notes:
- **Replace the path**: Update `/Users/michaelpolzin/Documents/code/pickleball-notifier` with your actual project path
- **Log file**: The script automatically redirects output to `scraper.log`
- **Virtual environment**: The script ensures the virtual environment is activated
- **Self-contained**: The script automatically finds its own directory
- **Testing**: Always test the script manually before setting up the cron job

### Log Rotation

The project includes a `rotate_logs.sh` script that uses the standard `logrotate` utility for proper log management:

#### Features:
- **Compression** - Old logs are compressed to save space
- **Proper file handling** - Uses Unix standard log rotation
- **7-day retention** - Keeps a full week of logs for debugging
- **Better performance** - More efficient than manual rotation
- **3AM Eastern rotation** - Only rotates logs at 3AM to avoid disrupting active monitoring

#### Setup:
```bash
# The logrotate config uses relative paths - no changes needed!
# Just use the rotation script in cron:
0 3 * * * /path/to/rotate_logs.sh
```

#### Manual Testing:
```bash
# Test logrotate configuration
logrotate -d pickleball-scraper.logrotate

# Test the rotation script
./rotate_logs.sh
```

#### Log Files:
- **`scraper.log`** - Current day's log file
- **`scraper.log.1.gz`** - Yesterday's compressed log file
- **`scraper.log.2.gz`** - 2 days ago compressed log file
- **`scraper.log.3.gz`** - 3 days ago compressed log file
- **`scraper.log.4.gz`** - 4 days ago compressed log file
- **`scraper.log.5.gz`** - 5 days ago compressed log file
- **`scraper.log.6.gz`** - 6 days ago compressed log file
- **`scraper.log.7.gz`** - 7 days ago compressed log file (oldest)

## Automatic Cleanup

The system automatically prevents file bloat by:

- **Removing Stale Matches**: Matches that no longer appear on Adam Harvey's page are automatically removed
- **Cleaning Execution History**: Keeps only the last 100 execution records
- **Smart Detection**: Only removes matches that are truly no longer relevant
- **Preservation**: Maintains notification status and court assignment data for active matches

This ensures the configuration file stays lean and relevant, even with long-running minute-by-minute execution.

## GroupMe Notifications

The system automatically sends engaging notifications to a GroupMe group when court assignments are detected:

- **API Endpoint**: `https://api.groupme.com/v3/bots/post`
- **Bot ID**: `[REDACTED]`
- **Message Format**: Engaging messages with emojis and variety
- **Example Messages**:
  - "🏓 Adam Harvey has been assigned to Court SC5 and will be starting soon!"
  - "🚀 Adam Harvey is heading to Court GS - get ready for some action!"
  - "⭐ Court SC8 is Adam Harvey's stage - the performance starts soon!"

The system ensures each match gets a consistent message style and prevents duplicate notifications.

## YouTube Stream Integration

The system automatically checks for live YouTube streams when court assignments are detected:

- **Stream Detection**: Searches `https://www.youtube.com/@PPAStreamedCourts/search?query=<court_assignment>`
- **Live Stream Detection**: Looks for "watching" text in metadata to identify live streams
- **Direct Links**: Includes full YouTube URLs when live streams are found
- **Smart Fallback**: Falls back to PickleballTV messages when no YouTube streams are available
- **Court-Specific Messages**:
  - **CC Courts**: "free to watch on PickleballTV"
  - **Other Courts**: "on PickleballTV - login required"

### Example Messages:

**With Live YouTube Stream:**
```
🏓 Adam Harvey has been assigned to Court SC5 and will be starting soon!

📺 LIVE STREAM: https://www.youtube.com/watch?v=abc123def456
```

**Without Live Stream (PickleballTV):**
```
🔥 Adam Harvey has been assigned to Court SC1 - the match is about to begin! (on PickleballTV - login required)
```

**CC Court (Free):**
```
⚡ Adam Harvey is heading to Court CC - get ready for some action! (free to watch on PickleballTV)
```

The system gracefully handles YouTube API failures and always provides useful information to users.

## Configuration

The system uses a configuration file (`config.json`) to store sensitive data like API keys and bot IDs. This file is excluded from version control for security.

### Configuration File Structure

```json
{
  "groupme": {
    "bot_id": "your_groupme_bot_id_here"
  },
  "player": {
    "slug": "adam-harvey"
  }
}
```

### Setup Instructions

1. Copy the template: `cp config.json.template config.json`
2. Edit `config.json` and:
   - Replace `YOUR_GROUPME_BOT_ID_HERE` with your actual GroupMe bot ID
   - Update the `player.slug` if you want to track a different player
3. The `config.json` file is automatically ignored by git to prevent committing sensitive data

### Security Notes

- Never commit `config.json` to version control
- The template file (`config.json.template`) is safe to commit
- Bot IDs and API keys should be kept private
