# macOS Testing Guide for Telos

This guide provides comprehensive testing steps for the macOS build of Telos.

## Prerequisites

- macOS 10.13 (High Sierra) or later
- Python 3.8+ installed
- Terminal access

## Phase 1: Development Testing (Python)

Test the app running directly from Python before building the standalone bundle.

### 1.1 Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

### 1.2 Initial Setup

```bash
python main.py setup
```

Expected:
- ✅ Prompts for Gemini API key
- ✅ Creates `config.yaml`
- ✅ Shows success message

### 1.3 Permission Checks

```bash
python -c "from core.macos_permissions import check_and_request_permissions; check_and_request_permissions()"
```

Expected:
- ✅ Checks Screen Recording permission
- ✅ Checks Accessibility permission
- ✅ Opens System Settings if permissions missing
- ✅ Waits for permissions to be granted

### 1.4 Test TUI Mode

```bash
python main.py
```

Expected:
- ✅ Shows permission prompt if not granted
- ✅ Launches TUI interface
- ✅ Can navigate with keyboard shortcuts (D, T, S, C, A, Q)
- ✅ Shows live activity tracking
- ✅ Press Q to quit cleanly

### 1.5 Test Capture Loop

```bash
python main.py test
```

Expected:
- ✅ Captures screenshots every 30 seconds
- ✅ Detects idle state
- ✅ Analyzes with Gemini API
- ✅ Stores in database
- ✅ Deletes screenshots after analysis
- ✅ Press Ctrl+C to stop

### 1.6 Test Background Service

```bash
# Test in console mode first
python main.py service-console
```

Expected:
- ✅ Starts capture worker
- ✅ Starts session worker
- ✅ Starts email worker (if enabled)
- ✅ Logs activity to console
- ✅ Press Ctrl+C to stop

## Phase 2: LaunchAgent Testing

Test the macOS background service functionality.

### 2.1 Install LaunchAgent

```bash
python main.py install-service
```

Expected:
- ✅ Creates `~/Library/LaunchAgents/dev.telos.tracker.plist`
- ✅ Loads LaunchAgent with `launchctl`
- ✅ Shows success message

### 2.2 Check Service Status

```bash
python main.py service-status
```

Expected:
- ✅ Shows "Service Status: RUNNING" or "INSTALLED"
- ✅ Displays service details

### 2.3 Start Service

```bash
python main.py start-service
```

Expected:
- ✅ Service starts successfully
- ✅ Can verify with: `launchctl list | grep telos`
- ✅ Logs appear in `/tmp/telos.log`

### 2.4 Check Logs

```bash
tail -f /tmp/telos.log
```

Expected:
- ✅ Shows capture worker activity
- ✅ Shows session building activity
- ✅ No errors (or only benign warnings)

### 2.5 Stop Service

```bash
python main.py stop-service
```

Expected:
- ✅ Service stops cleanly
- ✅ Logs stop updating

### 2.6 Uninstall Service

```bash
python main.py uninstall-service
```

Expected:
- ✅ Unloads LaunchAgent
- ✅ Removes plist file
- ✅ Shows success message

## Phase 3: Build Testing

Test the PyInstaller build process.

### 3.1 Prepare Icon (Optional)

```bash
cd macos

# If you have a PNG icon:
python create_icns.py your-icon.png

# Otherwise, the build will work without an icon
cd ..
```

### 3.2 Run Build Script

```bash
python build_macos.py
```

Expected:
- ✅ Checks dependencies
- ✅ Cleans previous builds
- ✅ Runs PyInstaller
- ✅ Creates `dist/Telos.app`
- ✅ Creates distribution README
- ✅ Creates DMG file
- ✅ Shows build summary with file sizes

### 3.3 Verify Build Output

```bash
ls -lh dist/
```

Expected files:
- `Telos.app` - macOS application bundle
- `Telos-v0.1.0-beta-macOS.dmg` - Disk image installer
- `README.txt` - Distribution readme

### 3.4 Inspect App Bundle

```bash
ls -R dist/Telos.app/Contents/
```

Expected structure:
```
Contents/
├── Info.plist
├── MacOS/
│   └── Telos (executable)
└── Resources/
    ├── prompts/
    ├── config.yaml.example
    └── ...
```

### 3.5 Check App Signature

```bash
codesign -dv dist/Telos.app
```

Note: If unsigned, macOS will show security warning on first launch.
This is normal for development builds.

## Phase 4: Standalone App Testing

Test the built .app bundle.

### 4.1 Test Direct Launch

```bash
open dist/Telos.app
```

Expected:
- ⚠️  macOS shows "cannot be opened because the developer cannot be verified"
- This is expected for unsigned apps

### 4.2 Bypass Gatekeeper

```bash
# Option 1: Right-click → Open in Finder
# Option 2: Command line
xattr -cr dist/Telos.app
open dist/Telos.app
```

Expected:
- ✅ App launches
- ✅ Shows permission requests
- ✅ TUI interface appears

### 4.3 Test App Functionality

With the .app running:
- ✅ Test all TUI screens (D, T, S, C, A)
- ✅ Test capture functionality
- ✅ Test database operations
- ✅ Test quitting (Q)

### 4.4 Test Service Installation from App

```bash
/Applications/Telos.app/Contents/MacOS/Telos install-service
```

Expected:
- ✅ Installs LaunchAgent pointing to .app bundle
- ✅ Can start/stop service
- ✅ Logs work correctly

## Phase 5: DMG Testing

Test the disk image installer.

### 5.1 Mount DMG

```bash
open dist/Telos-v0.1.0-beta-macOS.dmg
```

Expected:
- ✅ DMG mounts successfully
- ✅ Shows Telos.app

### 5.2 Install via Drag-to-Applications

1. Drag `Telos.app` from DMG to `/Applications`
2. Eject the DMG
3. Launch from Applications folder

Expected:
- ✅ App copies to Applications
- ✅ Launches successfully from Applications
- ✅ All functionality works

### 5.3 Test as End User

Pretend you're a fresh user:
1. Download DMG
2. Open DMG
3. Drag to Applications
4. Launch app (Right-click → Open for unsigned apps)
5. Grant permissions when prompted
6. Go through onboarding
7. Use the app normally

Expected:
- ✅ Smooth installation experience
- ✅ Clear permission instructions
- ✅ Onboarding works
- ✅ App functions normally

## Phase 6: Clean System Testing

Test on a fresh macOS system (VM or separate machine).

### 6.1 Fresh Install Test

On a clean macOS system:
1. Copy only the DMG file
2. Install without Python or any dependencies
3. Launch and test

Expected:
- ✅ Works without Python installed
- ✅ All dependencies bundled
- ✅ No missing libraries errors

### 6.2 Different macOS Versions

Test on:
- macOS 13 (Ventura) - Latest
- macOS 12 (Monterey)
- macOS 11 (Big Sur)
- macOS 10.15 (Catalina) - Min supported with Screen Recording

### 6.3 Different Architectures

Test on:
- Apple Silicon (M1/M2/M3) - arm64
- Intel - x86_64

Note: PyInstaller builds architecture-specific. Build on the architecture you want to support.

## Phase 7: Edge Cases & Stress Testing

### 7.1 Permission Denial

1. Launch app
2. Deny Screen Recording permission
3. Verify app handles gracefully

Expected:
- ✅ Clear error message
- ✅ Instructions to enable
- ✅ Option to retry

### 7.2 Network Issues

1. Disconnect from internet
2. Launch app
3. Try to analyze screenshot

Expected:
- ✅ Shows connection error
- ✅ Retries with exponential backoff
- ✅ Doesn't crash

### 7.3 API Quota Exceeded

1. Set low daily limit in config
2. Let it hit the limit
3. Verify behavior

Expected:
- ✅ Stops making API calls
- ✅ Shows quota exceeded message
- ✅ Continues on next day

### 7.4 Service Restart

1. Install service
2. Force kill the process: `killall Telos`
3. Check if LaunchAgent restarts it

Expected:
- ✅ LaunchAgent detects crash
- ✅ Restarts service automatically
- ✅ Logs show restart

### 7.5 Upgrade Path

1. Install v0.1.0
2. Use it for a while (generate data)
3. Build v0.2.0 with different version
4. Install over existing

Expected:
- ✅ Preserves user data
- ✅ Preserves config
- ✅ Doesn't break database

## Common Issues & Solutions

### "Telos.app is damaged and can't be opened"

**Cause:** Gatekeeper quarantine attribute

**Solution:**
```bash
xattr -cr /Applications/Telos.app
```

### "Screen Recording permission not granted"

**Cause:** Permission not enabled in System Settings

**Solution:**
1. System Settings → Privacy & Security → Privacy
2. Screen Recording → Enable Telos
3. Restart Telos

### "LaunchAgent not starting"

**Cause:** Incorrect plist or permissions

**Solution:**
```bash
# Check plist syntax
plutil -lint ~/Library/LaunchAgents/dev.telos.tracker.plist

# Check LaunchAgent status
launchctl list | grep telos

# Check logs
cat /tmp/telos.error.log
```

### "PyInstaller build fails"

**Cause:** Missing dependencies or incorrect spec

**Solution:**
```bash
# Clean and retry
rm -rf build dist
python build_macos.py

# Check for missing modules
python -m PyInstaller --collect-all textual Telos_macos.spec
```

### "App crashes on launch"

**Cause:** Missing runtime dependencies

**Solution:**
```bash
# Run from terminal to see errors
/Applications/Telos.app/Contents/MacOS/Telos

# Check console logs
log show --predicate 'process == "Telos"' --last 5m
```

## Success Criteria

Before considering macOS support complete:

- [x] ✅ App runs from Python source
- [x] ✅ Permission checks work
- [x] ✅ TUI interface functions
- [x] ✅ Capture and analysis work
- [x] ✅ LaunchAgent installs/uninstalls
- [x] ✅ Background service runs
- [x] ✅ PyInstaller builds successfully
- [x] ✅ .app bundle launches
- [x] ✅ DMG installs correctly
- [ ] ⏸️  Works on fresh macOS system (requires testing)
- [ ] ⏸️  Works without Python installed (requires testing)
- [ ] ⏸️  Handles permission denials gracefully (requires testing)
- [ ] ⏸️  Service auto-restarts on crash (requires testing)

## Automated Testing Script

For quick smoke testing:

```bash
#!/bin/bash
# macos_smoke_test.sh

echo "=== Telos macOS Smoke Test ==="

# Test 1: Build
echo "Test 1: Building app..."
python build_macos.py || exit 1

# Test 2: App structure
echo "Test 2: Checking app structure..."
test -d dist/Telos.app || exit 1
test -f dist/Telos.app/Contents/MacOS/Telos || exit 1

# Test 3: Executable
echo "Test 3: Checking executable..."
test -x dist/Telos.app/Contents/MacOS/Telos || exit 1

# Test 4: DMG
echo "Test 4: Checking DMG..."
test -f dist/Telos-v0.1.0-beta-macOS.dmg || exit 1

echo "✅ All smoke tests passed!"
```

## Notes

- Testing requires an actual macOS machine (VM or hardware)
- Screen Recording permission testing requires GUI
- Some tests require restarting the app
- LaunchAgent testing requires admin permissions
- Code signing testing requires Apple Developer account ($99/year)

