# Telos

AI-powered screen time tracker with intelligent activity analysis using Gemini Vision API.

## Status

### Phase 1 - Core Foundation ✓ COMPLETE
- ✓ Screenshot capture every 30 seconds (configurable)
- ✓ Activity detection (mouse/keyboard monitoring)
- ✓ Idle detection (auto-pause after 60s of inactivity)
- ✓ Perceptual hashing (skips duplicate screenshots to save API calls)
- ✓ Gemini Vision API integration with strict JSON schema
- ✓ SQLite database storage (3-tier architecture)
- ✓ Automatic screenshot deletion after analysis
- ✓ API quota tracking and rate limiting

### Phase 2 - TUI Interface ✓ COMPLETE
- ✓ Real-time Textual dashboard with 1s refresh
- ✓ Live activity tracking with running timer
- ✓ Category breakdown with progress bars
- ✓ Recent timeline (last 5 captures)
- ✓ Status indicators (🟢 Active / 🟡 Idle)
- ✓ Non-blocking background workers (smooth performance)
- ✓ Keyboard navigation (D/T/S/C/Q/G/R)
- ✓ Multiple screens (Dashboard, Timeline, Summary, Settings)

### Phase 3 - Intelligence Layer ✓ COMPLETE
- ✓ Smart session building (groups captures into sessions)
  - Triggers every 2 hours OR after 5 minutes idle
  - Groups by same category + app with <5min gaps
- ✓ AI-powered session enrichment
  - Detailed summaries and learnings
  - Focus score calculation (0.0-1.0)
- ✓ Customizable analysis goals (interactive TUI editor)
  - 4 presets: Productivity, Learning, Project Tracking, Habits
  - Custom goal support with free-text input
- ✓ Daily summaries with AI narratives
  - Productivity scoring (0-100)
  - Key learnings extraction
  - Focus blocks identification
  - On-demand generation with loading indicator
- ✓ Timeline view with sessions (not raw captures)
- ✓ API efficiency: ~60-65 calls/day (well under 1500 limit)

### Phase 5 - Rich Capture & AI Chat ✓ COMPLETE
- ✓ **Rich Context Extraction**: Granular details from every screenshot
  - File names, cursor positions, browser URLs
  - Full descriptions, progress tracking
  - AI observations and patterns
  - Dynamic categories with custom emojis/colors
- ✓ **AI Chat Interface**: Interactive query system in TUI
  - Natural language questions about your work
  - Content generation (LinkedIn posts, tweets, marketing)
  - Smart context search (7-365 days)
  - Markdown-formatted responses

### Phase 4 - Production Ready (PARTIAL)
- ✓ **Email Reports**: Automated end-of-day email summaries
  - Beautiful HTML email with daily insights
  - Configurable send time (e.g., 9 PM)
  - Gmail SMTP support with app passwords
  - Productivity score, time breakdown, learnings, focus blocks
- ✓ **Windows Service (Daemon Mode)**: Run as background service
  - Lightweight operation (~40MB memory)
  - Auto-start on Windows boot
  - Runs without user login
  - Console test mode for debugging
- ⏳ Export functionality (CSV/JSON/PDF reports)
- ⏳ Advanced error handling (retry logic, graceful degradation)
- ⏳ Performance optimization (caching, lazy loading)

**📌 See `CURRENT_STATUS.md` for detailed progress and next steps!**

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your Gemini API key:
```bash
# Option 1: Use setup wizard
python main.py setup

# Option 2: Manual configuration
cp config.yaml.example config.yaml
# Edit config.yaml and add your API key
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

## Usage

### Run TUI (default)
```bash
python main.py          # or: python main.py run
```

**Keyboard shortcuts:**
- **D** - Dashboard (main view)
- **T** - Timeline (session view with focus scores)
- **S** - Summary (daily insights with AI narrative)
- **C** - Settings (configuration)
- **A** - AI Chat (query your activity data)
- **G** - Edit analysis goals (in Settings screen)
- **R** - Regenerate summary (in Summary screen)
- **Q** - Quit

The TUI shows:
- Live status indicator (🟢 Active / 🟡 Idle / 🔴 Stopped)
- Current activity with running timer
- Today's breakdown by category (progress bars)
- Recent 5 captures with timestamps
- API quota usage (X/1500)
- Sessions today (Phase 3)
- Productivity score (Phase 3)
- AI Chat interface (Phase 5) - Query your data and generate content

### CLI Commands
```bash
# Basic commands
python main.py setup              # First-time setup wizard
python main.py test               # Run capture loop in CLI mode
python main.py stats              # Show today's statistics
python main.py help               # Show help message

# Phase 3 commands (Intelligence Layer)
python main.py set-goals          # Set analysis goals (CLI mode)
python main.py build-sessions     # Manually trigger session building
python main.py generate-summary   # Generate daily summary (CLI mode)

# Phase 4 commands (Production Ready)
python main.py test-email         # Test email configuration
python main.py service-console    # Run as daemon in console (test mode)
python main.py install-service    # Install Windows service (requires admin)
python main.py uninstall-service  # Uninstall Windows service (requires admin)
python main.py start-service      # Start Windows service
python main.py stop-service       # Stop Windows service
python main.py service-status     # Check service status
```

**Note:** You can now edit analysis goals directly from the TUI by pressing **G** in the Settings screen!

## AI Chat - Query Your Activity Data (Phase 5)

The AI Chat feature lets you interact with your captured activity data using natural language. Press **A** in the TUI to open the chat interface.

### What You Can Do

**Ask Questions:**
- "What did I work on yesterday afternoon?"
- "Show me everything I did on the email reporter feature"
- "What have I learned this week about Python async?"
- "When did I last work on database migrations?"

**Generate Content:**
- "Generate a LinkedIn post about how I built this app"
- "Write a tweet about my productivity tracker"
- "Create marketing copy for this app"
- "Summarize my work this week for a status update"

**Extract Insights:**
- "What were my most productive days this week?"
- "What patterns do you see in my work habits?"
- "Which features took the most time to build?"
- "What did I spend most time on today?"

### How It Works

The AI Chat:
1. **Searches your rich capture data** - file names, cursor positions, browser URLs, detailed descriptions
2. **Analyzes your sessions** - AI summaries, learnings, focus scores
3. **References daily summaries** - productivity scores, narratives, key insights
4. **Uses Gemini AI** to synthesize responses from your data

All queries are processed locally using your Gemini API key. Your data never leaves your device except for the API call to Gemini.

### Tips for Best Results

- **Be specific** with time ranges ("yesterday", "this week", "last Tuesday")
- **Mention projects or features** by name for focused searches
- **Ask for specific formats** when generating content ("LinkedIn post", "bullet points", "timeline")
- The chat searches the last 7 days by default, but automatically adjusts based on your query

## Configuration

Edit `config.yaml` to customize:

```yaml
gemini:
  api_key: "YOUR_API_KEY"
  model: "gemini-2.5-flash"      # Gemini 2.5 Flash with strict JSON schema

capture:
  interval_seconds: 30           # Time between screenshots
  idle_timeout_seconds: 60       # Pause after inactivity
  screenshot_quality: 85         # JPEG quality (1-100)
  max_daily_requests: 1500       # API quota limit

storage:
  database_path: "~/.telos/tracker.db"
  captures_retention_days: 1
  sessions_retention_days: 90

display:
  refresh_rate_ms: 1000          # TUI refresh rate
  theme: "dark"                  # TUI theme

intelligence:
  session_trigger_hours: 2          # Auto-build sessions every N hours
  session_trigger_idle_minutes: 5   # Or after N minutes idle
  check_interval_seconds: 60        # How often to check for triggers
  max_enrichment_per_trigger: 3     # API quota management
  min_session_captures: 2           # Minimum captures to form a session
  session_gap_seconds: 300          # Max gap within session (5 minutes)

email:
  enabled: false                    # Enable automated email reports
  smtp_host: "smtp.gmail.com"       # SMTP server hostname
  smtp_port: 587                    # SMTP port (587 for TLS)
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"  # Gmail app password (not regular password!)
  recipient_email: "your-email@gmail.com"
  send_time: "21:00"                # Daily send time (24-hour format)
```

## Project Structure

```
telos/
├── main.py                 # Entry point with TUI and CLI commands
├── config.yaml            # User configuration
├── requirements.txt       # Dependencies
│
├── core/                  # Core functionality
│   ├── capture.py         # Screenshot capture + activity detection
│   ├── analyzer.py        # Gemini Vision API integration (with rich context)
│   ├── database.py        # SQLite operations (3-tier schema)
│   ├── query_engine.py    # AI chat data search and context builder
│   ├── session_builder.py # Session grouping and enrichment
│   ├── daily_aggregator.py # Daily summary generation
│   ├── goal_manager.py    # Analysis goals management
│   └── email_reporter.py  # Email report generation
│
├── tui/                   # TUI interface
│   ├── app.py             # Main Textual application
│   ├── workers/           # Background async workers
│   │   ├── capture_worker.py   # Non-blocking capture loop
│   │   ├── db_poller.py        # Database polling (1s refresh)
│   │   ├── session_worker.py   # Session building worker
│   │   └── email_worker.py     # Email scheduling worker
│   ├── screens/           # TUI screens
│   │   ├── dashboard.py   # Main dashboard
│   │   ├── timeline.py    # Timeline view
│   │   ├── summary.py     # Summary view
│   │   ├── settings.py    # Settings view
│   │   ├── chat.py        # AI Chat interface (Phase 5)
│   │   └── goal_editor.py # Goal editor modal
│   └── widgets/           # Reusable UI components
│       ├── status_banner.py    # Status indicator
│       ├── current_activity.py # Live activity with timer
│       ├── category_breakdown.py # Progress bars
│       └── recent_timeline.py   # Recent 5 captures
│
├── prompts/               # Editable AI prompt templates
│   ├── screenshot_analysis.txt  # Rich capture analysis
│   ├── session_enrichment.txt   # Session summarization
│   └── daily_summary.txt        # Daily narrative generation
│
└── utils/
    ├── config_manager.py  # Config loading/saving
    ├── hash_utils.py      # Perceptual hashing
    └── time_utils.py      # Time formatting helpers
```

## Database Schema

### Captures Table (Tier 3 - 24h retention)
Stores individual screenshot analysis results:
- `timestamp` - When screenshot was taken
- `category` - work/learning/browsing/entertainment/idle
- `app_name` - Application detected
- `task` - Brief description of activity
- `confidence` - AI confidence score (0.0-1.0)

### Sessions Table (Tier 2 - 90 day retention)
Groups similar consecutive activities into sessions:
- `start_time`, `end_time` - Session time range
- `duration_seconds` - Session duration
- `category` - Primary category
- `primary_task` - Main task description
- `apps_used` - JSON array of apps used
- `detailed_summary` - AI-generated summary (from Gemini)
- `learnings` - Extracted learnings (from Gemini)
- `focus_score` - Focus quality metric (0.0-1.0)

### Daily Summaries Table (Tier 1 - permanent)
Stores aggregated daily insights:
- `date` - Summary date (unique)
- `work_seconds`, `learning_seconds`, etc. - Time per category
- `key_learnings_json` - JSON array of key insights
- `productivity_score` - Daily productivity (0-100)
- `context_switches` - Number of activity changes
- `focus_blocks_json` - JSON array of focus periods
- `daily_narrative` - AI-generated summary of the day

## How It Works

### Backend (runs in background workers)

**Capture Worker** (every 30s):
1. **Activity Monitor** tracks mouse/keyboard input continuously
2. **Idle Detection** pauses capturing after 60s of inactivity
3. **Screenshot Capture** takes a screenshot every 30s (when active)
4. **Perceptual Hashing** compares to previous screenshot (skips duplicates)
5. **Gemini Vision API** analyzes screenshots with strict JSON schema
6. **Database Storage** saves capture to Tier 3 (24h retention)
7. **Screenshot Deletion** immediately removes images

**Session Worker** (every 60s, triggers on 2hr OR 5min idle):
1. **Smart Grouping** combines captures into sessions (same category+app, <5min gaps)
2. **AI Enrichment** uses Gemini to generate session summaries and extract learnings
3. **Focus Scoring** calculates focus quality based on consistency
4. **Database Storage** saves sessions to Tier 2 (90 day retention)

**DB Polling Worker** (every 1s):
1. Fetches today's stats from database
2. Updates reactive UI state
3. Refreshes API quota display

### Frontend (TUI)
- **Dashboard** displays live activity with 1-second refresh
- **Timeline** shows sessions (not raw captures) with focus scores
- **Summary** generates AI-powered daily insights on-demand (with loading indicator)
- **Settings** allows editing analysis goals interactively (press G)
- **Background Workers** run non-blocking async tasks (capture + session + DB polling)
- All operations use asyncio.to_thread() to keep UI responsive

## Email Reports (Phase 4)

Get beautiful daily summaries delivered to your inbox automatically!

### Setup Gmail Email Reports

1. **Enable 2-Step Verification** on your Google Account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification if not already enabled

2. **Create Gmail App Password**:
   - Visit https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Configure in config.yaml**:
```yaml
email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "xxxx xxxx xxxx xxxx"  # Your 16-char app password
  recipient_email: "your-email@gmail.com"
  send_time: "21:00"  # 9 PM daily
```

4. **Test the configuration**:
```bash
python main.py test-email
```

### Email Features

- 📊 **Productivity Score**: Daily score (0-100) with color-coded badge
- ⏱️ **Time Breakdown**: Visual progress bars by category
- 🎓 **Key Learnings**: AI-extracted insights from your day
- 🎯 **Focus Blocks**: Deep work sessions highlighted
- 📝 **Daily Narrative**: AI-generated summary of your day
- 📈 **Context Switches**: Track how often you change tasks

The email is sent automatically at your configured time (default: 9 PM) when running in TUI mode or as a Windows Service.

## Windows Service (Daemon Mode)

Run Telos as a background Windows Service - always running, lightweight, and invisible!

### Installation

**Important**: You need Administrator privileges to install Windows services.

1. **Test in Console Mode First** (recommended):
```bash
python main.py service-console
```
This runs the daemon in the console so you can see logs and verify everything works. Press Ctrl+C to stop.

2. **Install as Windows Service**:
```bash
# Run as Administrator
python main.py install-service
```

3. **Start the Service**:
```bash
python main.py start-service
```

4. **Check Status**:
```bash
python main.py service-status
```

### Service Management

```bash
# Stop the service
python main.py stop-service

# Uninstall the service (run as Administrator)
python main.py uninstall-service

# View status
python main.py service-status
```

You can also manage the service through Windows Services Manager (`services.msc`):
- Service Name: `Telos`
- Display Name: `Telos`

### Service Features

- **Auto-start on Boot**: Optionally configured to start automatically
- **Background Operation**: Runs without console window
- **Lightweight**: ~40MB memory footprint
- **Resilient**: Continues running after user logout
- **Event Logging**: Logs to Windows Event Viewer
- **No TUI Overhead**: Service mode skips UI components

### What Runs in Service Mode?

1. **Capture Worker**: Takes screenshots every 30s, analyzes with Gemini
2. **Session Worker**: Builds and enriches sessions every 2 hours or after 5min idle
3. **Email Worker**: Sends daily reports at configured time (if enabled)

All workers run independently with their own error handling, so if one fails, others continue.

## Roadmap

### Phase 4 - Production Ready (In Progress)
- ✓ **Email Reports**: Automated daily summaries via Gmail SMTP
- ✓ **Windows Service**: Background daemon mode
- ⏳ **Export**: CSV/JSON/PDF reports for daily/weekly/monthly data
- ⏳ **Advanced Error Handling**: Retry logic, graceful degradation
- ⏳ **Performance**: Further optimization, caching, lazy loading
- ⏳ **Testing**: Unit tests, integration tests, CI/CD pipeline

### Phase 5 - Cross-Platform (Future)
- **Linux Support**: systemd service for Linux
- **macOS Support**: launchd agent for macOS
- **Web Dashboard**: Optional web interface for remote viewing

## Technical Details

- **Screenshots**: Stored temporarily in `temp_screenshots/`, deleted after analysis
- **Database**: SQLite at `~/.telos/tracker.db` (expandable path)
- **Perceptual Hashing**: ImageHash library (phash algorithm) for duplicate detection
- **Activity Detection**: pynput for cross-platform mouse/keyboard monitoring
- **API**: Gemini 2.5 Flash with strict JSON schema enforcement
- **TUI**: Textual framework with reactive properties and async workers
- **Performance**: Non-blocking operations using `asyncio.to_thread()`
- **Quota**: Resets daily at midnight, tracked in database

## Troubleshooting

**Configuration Issues**
- `Config not found`: Run `python main.py setup`
- `API key error`: Edit `config.yaml` and add key from https://aistudio.google.com/app/apikey

**API Quota**
- `QUOTA EXCEEDED`: Wait until midnight or adjust `max_daily_requests` in config
- Perceptual hashing reduces API calls by ~50% (skips duplicate screenshots)

**Activity Detection**
- macOS: Grant accessibility permissions to Terminal/Python
- Windows: Run as administrator if keyboard/mouse events not detected
- Linux: Check `xinput` permissions

**TUI Issues**
- `TUI freezing`: Should not happen - all operations are non-blocking
- `Slow refresh`: Check `display.refresh_rate_ms` in config (default 1000ms)
- Navigation not working: Use D/T/S/C/Q keys (not Tab)

**Email Issues**
- `Authentication failed`: Make sure you're using Gmail App Password, not regular password
- `Connection timeout`: Check SMTP host (smtp.gmail.com) and port (587)
- `Email not received`: Check spam folder, verify recipient_email in config
- `Test email works but daily email doesn't`: Check send_time format (HH:MM in 24-hour)

**Windows Service Issues**
- `Access denied`: Run install/uninstall commands as Administrator
- `Service won't start`: Test first with `python main.py service-console` to see errors
- `Service not found`: Make sure you installed it first with `install-service`
- `Service crashes`: Check Windows Event Viewer (Application logs) for error details
