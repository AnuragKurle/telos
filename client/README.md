# Telos Client (Python)

This is the Telos desktop client - a Python TUI application for tracking screen activity.

## Quick Start

### Option 1: pip install (Recommended)

```bash
pip install telos-tracker
telos setup
telos
```

Your data is stored in `~/.telos/`.

### Option 2: From Source (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python main.py setup

# Start the TUI
python main.py

# Run as background service
python service.py start
```

## Development

See the main repository README for full documentation: [`../README.md`](../README.md)

## Structure

- `core/` - Core functionality (capture, analysis, database)
- `tui/` - Terminal user interface (Textual framework)
- `utils/` - Shared utilities
- `prompts/` - AI prompts for Gemini

## Configuration

Copy `config.yaml.example` to `config.yaml` and fill in your settings:

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your Gemini API key
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

## Features

- 📸 **Automatic Screenshot Capture** - Every 30 seconds (configurable)
- 🤖 **AI-Powered Analysis** - Gemini Vision understands what you're working on
- 📊 **Smart Session Building** - Groups activities into meaningful sessions
- 💬 **AI Chat Interface** - Ask questions about your work patterns
- 📧 **Daily Email Reports** - Beautiful summaries via Gmail
- 🖥️ **Terminal UI** - Clean, responsive TUI with real-time updates
- 🔒 **Privacy-First** - Screenshots analyzed and immediately deleted

## Usage

### TUI Mode (Default)
```bash
python main.py
```

**Keyboard shortcuts:**
- **D** - Dashboard (main view)
- **T** - Timeline (session view)
- **S** - Summary (daily insights)
- **C** - Settings
- **A** - AI Chat (query your data)
- **G** - Edit analysis goals
- **Q** - Quit

### CLI Commands
```bash
python main.py setup              # First-time setup
python main.py test               # Test capture loop
python main.py stats              # Show statistics
python main.py set-goals          # Configure analysis goals
python main.py build-sessions     # Manual session building
python main.py generate-summary   # Generate daily summary
python main.py test-email         # Test email configuration
```

### Background Service

**Windows:**
```bash
python main.py service-console    # Run as daemon (test mode)
python main.py install-service    # Install Windows service
python main.py start-service      # Start service
python main.py stop-service       # Stop service
```

**macOS:**
```bash
python main.py service-console    # Run as daemon (test mode)
python main.py install-service    # Install LaunchAgent
python main.py start-service      # Start service
python main.py stop-service       # Stop service
python main.py service-status     # Check service status
```

## Building Standalone Applications

### Windows Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build Windows executable and installer
python build_installer.py

# Output: dist/Telos.exe and TelosSetup-v0.1.0.exe
```

### macOS Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build macOS .app bundle and DMG
python build_macos.py

# Output: dist/Telos.app and Telos-v0.1.0-beta-macOS.dmg
```

**macOS Installation:**
1. Open the DMG file
2. Drag `Telos.app` to Applications folder
3. Right-click → Open (first time only, to bypass Gatekeeper)
4. Grant **Screen Recording** permission when prompted
5. Grant **Accessibility** permission when prompted

**macOS Permissions:**
- **Screen Recording** - Required for screenshot capture
- **Accessibility** - Required for keyboard/mouse activity detection

To grant permissions manually:
1. Open System Settings → Privacy & Security → Privacy
2. Select "Screen Recording" → Enable Telos
3. Select "Accessibility" → Enable Telos
4. Restart Telos

**Creating an Icon:**
If you want to customize the macOS icon:
```bash
cd macos
python create_icns.py your-icon.png
# This creates icon.icns, then rebuild with python build_macos.py
```

## Technical Details

- **Language:** Python 3.8+
- **UI Framework:** Textual (async TUI)
- **Database:** SQLite (3-tier architecture)
- **AI:** Google Gemini 2.5 Flash
- **Screenshot:** Pillow + ImageHash (perceptual hashing)
- **Activity Detection:** pynput (cross-platform)

## Troubleshooting

**Configuration Issues**
- Run `python main.py setup` for guided configuration
- Check `config.yaml` for correct API key

**API Quota**
- Free tier: 1500 requests/day
- Perceptual hashing reduces calls by ~50%
- Adjust `capture.interval_seconds` in config

**Activity Detection**
- **macOS**: Grant Screen Recording and Accessibility permissions in System Settings
  - System Settings → Privacy & Security → Privacy → Screen Recording
  - System Settings → Privacy & Security → Privacy → Accessibility
- **Windows**: Run as administrator if needed
- **Linux**: Check `xinput` permissions

## Status

✅ **Fully Functional** - All features complete and working

This client works standalone with your own Gemini API key. The backend (Node.js) is being built to enable SaaS features (no API key required, cloud sync, etc.).

---

**For Backend Integration:**

Once the backend is deployed, you can configure the client to use it:

```yaml
# In config.yaml (future)
backend:
  enabled: true
  url: "https://your-backend.run.app"
```

The client will then upload screenshots to your backend instead of calling Gemini directly, keeping your AI prompts proprietary.

