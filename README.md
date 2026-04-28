# Pickleball Player Scraper

A web scraper to extract tournament results links from pickleball.com player pages with configuration-based caching for match status tracking.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
make install
```

For a full local/dev toolchain (tests + lint), install dev extras:
```bash
.venv/bin/pip install -e .[dev]
```

3. Configure the application:
```bash
# Copy the template config file
cp config.json.template config.json

# Edit config.json and add your configuration:
# - Set groupme.access_token (user token) and groupme.subgroup_id (topic/channel id)
# - Add your YouTube Data API v3 key under youtube.api_key
# - Update the player slug if you want to track a different player
```

## Usage

Run the scraper to check the configured player's tournament results:

```bash
make run
```

### Linux deployment bootstrap

For cron-based deployments, `run_scraper.sh` now bootstraps automatically on first run:

- Creates `.venv` if missing
- Upgrades `pip`, `setuptools`, and `wheel`
- Installs project dependencies (tries `pip install -e .`, then falls back to `pip install .`)

So your cron can call only:

```bash
/path/to/pickleball-notifier/run_scraper.sh
```

If you want to run manually instead of the wrapper:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/pip install .  # or .venv/bin/pip install -e .
make run
```

## Testing

Run tests and lint checks:
```bash
make test
make lint
```

## Make Targets

You can use `make` shortcuts for common actions:
```bash
make install
make run
make lint
make test
make coverage
```

`make coverage` enforces a minimum of 100% coverage. Override with:
```bash
make coverage COV_FAIL_UNDER=98
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
- **GroupMe Integration**: Sends engaging notifications to a GroupMe topic
- **YouTube Stream Detection**: Automatically checks for live YouTube streams and includes links
- **Smart Fallback**: Gracefully falls back to PickleballTV messages when YouTube streams aren't available
- **Race Condition Free**: Single script execution eliminates file access conflicts

## Package Architecture

The codebase follows a layered package layout under `pickleball_notifier/`:

- `api/`: outbound API client integrations (pickleball.com result API)
- `core/`: core state/configuration models and persistence logic
- `notifications/`: notification orchestration and message generation
- `services/`: application workflow services and CLI entry module
- `youtube/`: YouTube-specific stream discovery logic
- `utils/`: shared helper utilities (for example, safe log redaction)

Package exports are loaded lazily from `__init__.py` modules to avoid import-time side effects and keep `python -m ...` entrypoint behavior predictable.

Primary entry point:

- `make run`
- Detailed architecture: [`docs/architecture.md`](docs/architecture.md)

## Configuration System

The scraper maintains a configuration file (`scraper_config.json`) that tracks:
- **Match Information**: UUID, URL, first/last seen timestamps, status, court assignments
- **Execution History**: Timestamp, matches found, new matches, completed matches
- **Status Tracking**: 
  - `future`: Matches currently visible but no court assigned yet (potential future matches)
  - `assigned`: Matches with court assigned (active matches, ready for notification)

## Files

- `pickleball_notifier/` - Layered package (`api`, `core`, `notifications`, `services`, `youtube`, `utils`)
- `tests/` - Test suite (currently includes smoke test stubs)
- `pyproject.toml` - Project metadata and pytest configuration
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
- **GroupMe Integration**: Posts engaging messages to a GroupMe topic
- **YouTube Stream Detection**: Checks for live streams and includes direct links
- **Smart Fallback System**: Gracefully handles YouTube API failures
- **Efficient Processing**: Only checks court assignments for matches that need it
- **Engaging Messages**: Variety of fun, emoji-rich notification messages

## Usage Examples

### Basic Scraping
```bash
make run
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
The project includes a `run_scraper.sh` script that handles full environment bootstrap and logging automatically:

```bash
# Test the script manually first
./run_scraper.sh

# Check if it worked
tail -f scraper.log
```

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
```

#### Important Notes:
- **Replace the path**: Update `/Users/michaelpolzin/Documents/code/pickleball-notifier` with your actual project path
- **Log file**: The script automatically redirects output to `scraper.log`
- **Virtual environment**: The script creates and manages `.venv` automatically
- **Dependencies**: The script auto-installs/repairs runtime dependencies when missing
- **Self-contained**: The script automatically finds its own directory
- **Testing**: Always test the script manually before setting up the cron job

### Log Rotation

The project includes a `rotate_logs.sh` script that provides log rotation without requiring external utilities:

#### Features:
- **No dependencies** - Works on any Unix-like system without logrotate
- **Compression** - Old logs are compressed with gzip (if available)
- **7-day retention** - Keeps a full week of logs for debugging
- **3AM Eastern rotation** - Only rotates logs at 3AM to avoid disrupting active monitoring
- **Graceful fallback** - Works even if gzip is not available

#### Setup:
```bash
# No external dependencies needed!
# Just use the rotation script in cron:
0 3 * * * /path/to/rotate_logs.sh
```

#### Manual Testing:
```bash
# Test the rotation script
./rotate_logs.sh

# Check if rotation worked (only works at 3AM Eastern)
ls -la *.log*
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

- **Removing Stale Matches**: Matches that no longer appear on the configured player's page are automatically removed
- **Cleaning Execution History**: Keeps only the last 100 execution records
- **Smart Detection**: Only removes matches that are truly no longer relevant
- **Preservation**: Maintains notification status and court assignment data for active matches

This ensures the configuration file stays lean and relevant, even with long-running minute-by-minute execution.

## GroupMe Notifications

The system posts as a GroupMe **user** to a **topic** (subgroup). Bots cannot target topics, so the app uses the GroupMe user messages API with your access token and the topic’s subgroup id.

- **API**: `POST https://api.groupme.com/v3/groups/{subgroup_id}/messages` (token as query parameter)
- **subgroup_id**: For a topic, this is the topic’s id (same value you would use as the group id for that channel)
- **Message format**: Engaging messages with emojis and variety
- **Example Messages**:
  - "🏓 Your Player has been assigned to Court SC5 and will be starting soon!"
  - "🚀 Your Player is heading to Court GS - get ready for some action!"
  - "⭐ Court SC8 is Your Player's stage - the performance starts soon!"

The system ensures each match gets a consistent message style for court assignments and prevents duplicate pings. **Court assignment** messages end with **`🔗 Match URL:`** pointing at the **`results/match/<uuid>`** URL (the same match page the scraper tracks), after any live-stream or PickleballTV lines. When the pickleball.com API reports **`match_completed`**, a **follow-up topic message** summarizes the match: **won or lost** for the configured `player.slug` (from the **`winner`** field vs your team), **each game’s score** as **team-one vs team-two** (`team_one_game_one_score` … `team_five` fields), lineup text when parsed, and **`🔗 Match URL:`** with that same pickleball URL.
## YouTube Stream Integration

The system automatically checks for live YouTube streams when court assignments are detected, using the YouTube Data API v3:

- **Primary Detection (YouTube API)**: Queries the PPA Streamed Courts channel for live videos matching the assigned court (e.g., "court 9").
- **Accurate Matching**: Matches against live video titles that include the court identifier.
- **Direct Links**: Includes full YouTube URLs when a live stream is found.
- **Smart Fallback**: If no live stream is found or an API error occurs, falls back to PickleballTV messaging.
- **Court-Specific Messages**:
  - **CC Courts**: "free to watch on PickleballTV"
  - **Other Courts**: "on PickleballTV - login required"

### Example Messages:

**With Live YouTube Stream (API Detection):**
```
🏓 Your Player has been assigned to Court 9 and will be starting soon!

📺 LIVE STREAM: https://www.youtube.com/watch?v=VIDEO_ID

🔗 Match URL: https://pickleball.com/results/match/<uuid>
```

**Without Live Stream (PickleballTV):**
```
🔥 Your Player has been assigned to Court SC1 - the match is about to begin! (on PickleballTV - login required)

🔗 Match URL: https://pickleball.com/results/match/<uuid>
```

**CC Court (Free):**
```
⚡ Your Player is heading to Court CC - get ready for some action! (free to watch on PickleballTV)
```

### Technical Details

- **Channel ID**: `UCwxrKD60cB__M6nhdH0UW0w` (PPA Streamed Courts)
- **API Endpoint**: `https://www.googleapis.com/youtube/v3/search`
- **Query Parameters**: `part=snippet`, `channelId=<CHANNEL_ID>`, `eventType=live`, `type=video`, `q="court {court}"`
- **Authentication**: Requires a YouTube Data API v3 key configured in `config.json`
- **Rate Limiting**: Requests are throttled to avoid limits

### Getting a YouTube API Key

1. Go to the Google Cloud Console and create/select a project.
2. Enable the "YouTube Data API v3" for your project.
3. Create an API key (API & Services → Credentials → Create credentials → API key).
4. Restrict the key appropriately (optional but recommended).
5. Add the key to `config.json` under `youtube.api_key`.

## Configuration

The system uses a configuration file (`config.json`) to store sensitive data like API keys and GroupMe tokens. This file is excluded from version control for security.

### Configuration File Structure

```json
{
  "groupme": {
    "access_token": "your_groupme_user_access_token",
    "subgroup_id": "your_topic_subgroup_id"
  },
  "player": {
    "slug": "your-player-slug"
  },
  "youtube": {
    "api_key": "your_youtube_api_key_here"
  },
  "pickleball_tv": {
    "free_court_codes": ["CC"]
  }
}
```

### Setup Instructions

1. Copy the template: `cp config.json.template config.json`
2. Edit `config.json` and:
   - Set `groupme.access_token` to a GroupMe user access token for an account that can post in the target topic
   - Set `groupme.subgroup_id` to the topic’s subgroup id (see GroupMe API / dev tools if you need to discover it)
   - Replace `YOUR_YOUTUBE_API_KEY_HERE` with your YouTube Data API key
   - Update the `player.slug` if you want to track a different player
3. The `config.json` file is automatically ignored by git to prevent committing sensitive data

### Security Notes

- Never commit `config.json` to version control
- The template file (`config.json.template`) is safe to commit
- Access tokens and API keys should be kept private

### Troubleshooting YouTube Integration

- **Missing API Key**: If `youtube.api_key` is not set, live stream detection will fail and messages will fall back to PickleballTV text.
- **Quota Exceeded**: If you hit YouTube API quota, detection will temporarily fail; fallback messaging remains in place.
- **No Live Match Found**: Not all courts are streamed on YouTube at all times; absence of a link is expected in that case.

### Troubleshooting startup/import errors

- **`ModuleNotFoundError: No module named 'requests'`**:
  - If using cron wrapper: run `./run_scraper.sh` again and check `scraper.log` (it auto-bootstraps `.venv` and dependencies).
  - If installing manually: run
    - `.venv/bin/python -m pip install --upgrade pip setuptools wheel`
    - `.venv/bin/pip install .` (or `.venv/bin/pip install -e .` when editable install is supported)
