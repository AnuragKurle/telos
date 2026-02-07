# Client

Python desktop application with a terminal UI. Distributed via PyPI as `telos-tracker`.

**Install:** `pip install telos-tracker && telos setup && telos`

## What It Does

- Captures screenshots every 30 seconds
- Analyzes them with Gemini Vision AI to determine what you're working on
- Stores structured insights locally in SQLite (screenshots are deleted immediately)
- Shows a terminal dashboard with timeline, heatmaps, focus scores, and AI chat
- Syncs data to Firestore for daily email reports (cloud mode)
- Runs as a background service or interactive TUI

Two modes:
- **Cloud mode** -- 7-day free trial, then $3/month. No API key needed.
- **BYOK mode** -- Free forever. Bring your own Gemini API key.

## Project Structure

```
client/
├── main.py                    # Entry point (dev), CLI commands, onboarding flow
├── mcp_server.py              # MCP server for Claude Desktop / Cursor
├── service.py                 # Windows background service daemon
├── service_macos.py           # macOS LaunchAgent service
├── core/
│   ├── analyzer.py            # Gemini Vision API integration
│   ├── backend_client.py      # Backend API client (cloud mode)
│   ├── capture.py             # Screenshot capture + activity monitoring
│   ├── daily_aggregator.py    # Daily summary generation, productivity scoring
│   ├── dashboard_server.py    # Local web dashboard (Flask, localhost:5555)
│   ├── database.py            # SQLite operations
│   ├── email_reporter.py      # Legacy email reporter (SMTP)
│   ├── fallback_handler.py    # Backend → local Gemini → offline fallback
│   ├── firebase_auth.py       # Firebase authentication
│   ├── firestore_sync.py      # Background sync: SQLite → Firestore
│   ├── goal_manager.py        # Analysis goals management
│   ├── onboarding.py          # First-run state management
│   ├── query_engine.py        # AI chat engine
│   ├── session_builder.py     # Group captures into work sessions
│   └── trial_manager.py       # Trial period tracking
├── tui/
│   ├── app.py                 # Main Textual TUI application
│   ├── screens/               # All TUI screens (dashboard, timeline, chat, etc.)
│   ├── widgets/               # Custom widgets (heatmap, waveform, breakdown)
│   ├── workers/               # Background workers (capture, sync, email)
│   └── models/                # TUI state management
├── utils/
│   ├── config_manager.py      # YAML config loading and saving
│   ├── hash_utils.py          # Perceptual hashing for duplicate detection
│   ├── prompt_loader.py       # AI prompt template loading
│   └── sentry_utils.py        # Sentry error tracking
├── telos_tracker/
│   ├── __init__.py            # Package version
│   └── cli.py                 # CLI entry point (telos command)
├── prompts/                   # AI prompt templates (editable)
│   ├── screenshot_analysis.txt
│   ├── session_enrichment.txt
│   ├── daily_summary.txt
│   └── ai_chat_system.txt
├── pyproject.toml             # PyPI package config
├── requirements.txt           # Python dependencies
├── publish.ps1                # Windows PyPI publish script
├── publish.sh                 # Linux/macOS PyPI publish script
├── build_installer.py         # Windows executable builder (PyInstaller)
├── build_macos.py             # macOS .app bundle builder
└── config.yaml.example        # Configuration template
```

## Local Development

```bash
cd client
pip install -r requirements.txt
python main.py setup           # Interactive setup wizard
python main.py                 # Launch TUI
```

Other commands:

```bash
python main.py test            # Test capture loop
python main.py stats           # Show statistics
python main.py service-console # Run as background daemon
```

## TUI Keyboard Shortcuts

| Key | Screen |
|-----|--------|
| `D` | Dashboard |
| `T` | Timeline |
| `S` | Summary |
| `A` | AI Chat |
| `C` | Settings |
| `E` | Email settings (from settings) |
| `G` | Goals |
| `H` | Help |
| `Q` | Quit |

## Configuration

Created by `telos setup` at `~/.telos/config.yaml`. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `capture.interval_seconds` | 30 | Screenshot interval |
| `capture.idle_threshold` | 300 | Seconds before marking idle |
| `backend.enabled` | true (cloud) | Use cloud backend for analysis |
| `backend.url` | Cloud Run URL | Backend API endpoint |
| `email.enabled` | true | Daily email reports |
| `email.send_time` | 21:00 | When to send daily report |

## Publishing to PyPI

```bash
# Automated (handles version bump, build, upload, tag)
.\publish.ps1 0.2.7 "Description of changes"

# Manual
python -m build
twine upload dist/*
```

## Building Desktop Apps

```bash
python build_installer.py      # Windows → dist/Telos.exe
python build_macos.py          # macOS → dist/Telos.app
```
