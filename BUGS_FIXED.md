# Bug Fixes - January 14, 2026

## Issue 1: Wrong Greeting ("Hello, Night Owl" in Evening)

**Root Cause:**
- Greeting was only updated every 3600 seconds (1 hour)
- If app started at night, greeting would stay "Night Owl" for up to 1 hour even if it's now afternoon/evening

**Fix:**
- Changed update interval from 3600s to 60s (1 minute)
- File: `client/tui/screens/dashboard.py` line 196

**Result:**
- Greeting now updates within 1 minute of time period change
- More accurate time-based greetings

---

## Issue 2: Extreme Activity Display Latency (Up to 30 Seconds)

**Root Cause:**
- Main capture loop waited 28 seconds (`interval - 2`) before capturing screenshot
- Window info only captured and displayed during screenshot cycle
- Even though window polling ran in background, it didn't update UI
- Result: Switch windows → wait up to 28 seconds → see update

**Fix:**
1. Added `current_window_title` as reactive property in `client/tui/app.py:34`
2. Created **continuous window polling task** that runs independently (every 1 second)
3. Polling task now updates UI immediately when window changes detected
4. Separated concerns: Fast polling (1s) for UI updates, slow cycle (30s) for LLM analysis
5. Timer starts immediately when window switches, not after LLM
   - Files: `client/tui/workers/capture_worker.py` lines 16-61, 126-130

**Architecture Change:**
```
BEFORE:
[Sleep 28s] → [Capture] → [Update UI] → [LLM] → [Repeat]
              ↑ Only point where UI updates (28s delay!)

AFTER:
Fast Loop (1s):  [Check Window] → [Update UI if changed] → [Repeat]
Slow Loop (30s): [Sleep] → [Capture] → [LLM Analysis] → [Update UI with enriched data]
                  ↑ Independent loops running in parallel
```

**Flow Now:**
1. **Instant (~1s)**: Switch windows → Shows "📄 **Brave** - LinkedIn Feed" + timer starts
2. **Next cycle (≤30s)**: LLM enrichment → "🌐 [Browsing] **Brave** - browsing LinkedIn feed"

**Result:**
- **1-second latency** instead of 28 seconds
- Continuous window monitoring independent of screenshot capture
- Progressive enhancement: Raw data → Enriched data
- Timer accurate to the second of window switch

---

## Testing

To verify fixes:

1. **Greeting Fix**:
   - Keep app running across time period boundaries (11:59 AM → 12:00 PM)
   - Greeting should update within 1 minute

2. **Latency Fix**:
   - Switch between different apps (Chrome → VSCode → Slack)
   - Window name should appear within 1 second at top
   - Timer starts immediately
   - Enriched description updates on next 30-second capture cycle

---

## Files Changed

- `client/tui/screens/dashboard.py` - Greeting update interval (line 196)
- `client/tui/app.py` - Added `current_window_title` reactive property (line 34)
- `client/tui/workers/capture_worker.py` - Continuous 1-second window polling + immediate UI updates (lines 16-61, 126-130)
- `client/utils/sentry_utils.py` - Made Sentry optional (graceful fallback if not installed)

## Architecture Improvement

**Key Change**: Separated fast UI updates (1s polling) from slow LLM analysis (30s cycle)

This allows the app to feel responsive while still doing heavy LLM analysis in the background. Users see instant feedback for window switches, then get AI-enriched descriptions when ready.
