# Firestore Sync Worker

## Problem Statement

The backend email scheduler requires data in Firestore to generate daily reports, but the client was only storing data locally in SQLite. This caused a critical gap where:

1. **Client captures data locally** → SQLite database at `~/.telos/tracker.db`
2. **Backend generates emails** → Expects data in Firestore at `usage/{userId}/dayBucket/{date}`
3. **Missing bridge** → No mechanism to sync SQLite → Firestore

**Result**: No emails sent since data was never uploaded to Firestore.

---

## Solution: Firestore Sync Worker

A new background worker that automatically syncs local SQLite captures to Firestore once per day.

### Architecture

```
┌─────────────────┐
│  Client (TUI)   │
│                 │
│  ┌───────────┐  │
│  │  Capture  │  │ → Stores captures
│  │  Worker   │  │   in SQLite
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │ Firestore │  │ → Syncs SQLite
│  │   Sync    │  │   to Firestore
│  │  Worker   │  │   daily
│  └───────────┘  │
└─────────────────┘
         │
         ↓ (REST API)
┌─────────────────┐
│   Firestore     │
│                 │
│  usage/{uid}/   │
│    dayBucket/   │
│      2026-01-13 │
│      2026-01-14 │
└─────────────────┘
         │
         ↓
┌─────────────────┐
│    Backend      │
│                 │
│  Email          │
│  Scheduler      │
└─────────────────┘
```

---

## Features

### ✅ Automatic Daily Sync
- Runs every 24 hours in the background
- Syncs data from previous days (not today, to ensure complete data)
- Tracks last sync date to avoid duplicates

### ✅ Smart Date Selection
- Only syncs dates with actual capture data
- Syncs last 3 days by default on first run
- Incremental sync after first run (only new dates)
- Maximum lookback: 7 days (prevents very stale data)

### ✅ Long-Running Session Support
- Works correctly even if client runs for days without restart
- Properly buckets captures by date
- Generates missing daily data automatically

### ✅ Firestore REST API
- Uses Firestore REST API (no Firebase Admin SDK required on client)
- Handles authentication via Firebase ID tokens
- Properly merges with existing data in Firestore

### ✅ Error Handling
- Continues running even if individual syncs fail
- Retries on network errors
- Detailed logging for debugging

---

## How It Works

### 1. Initialization

When TUI app starts and backend is enabled:
```python
firestore_sync = FirestoreSync(
    db=db,
    firebase_auth=firebase_auth,
    firebase_project_id=firebase_project_id,
    sync_interval_hours=24
)
asyncio.create_task(firestore_sync.start())
```

### 2. Sync Cycle

Every 24 hours:
1. **Determine dates to sync**
   - Get last sync date from config
   - Find all dates with capture data between last sync and yesterday
   - Skip today (data incomplete)

2. **For each date:**
   - Query SQLite for all captures on that date
   - Transform to Firestore format
   - Upload via REST API to `usage/{userId}/dayBucket/{date}`

3. **Update tracking**
   - Save latest synced date to config
   - Continue even if some dates fail

### 3. Data Format

**SQLite Capture:**
```python
{
    'timestamp': '2026-01-13 14:30:00',
    'category': 'Work',
    'simple_category': 'work',
    'app_name': 'VS Code',
    'task': 'Editing code',
    'confidence': 0.95
}
```

**Firestore Format:**
```json
{
  "dayBucket": {
    "2026-01-13": {
      "captures": [
        {
          "timestamp": "2026-01-13 14:30:00",
          "category": "Work",
          "simple_category": "work",
          "app_name": "VS Code",
          "task": "Editing code",
          "confidence": 0.95
        }
      ]
    }
  }
}
```

---

## Manual Sync

Use the manual sync script for testing or recovery:

### Sync All Pending Dates
```bash
cd client
python manual_firestore_sync.py
```

Output:
```
============================================================
MANUAL FIRESTORE SYNC
============================================================
Database: /Users/you/.telos/tracker.db
Firebase Project: gen-lang-client-0772617718

Last sync: 2026-01-10

Syncing all pending dates...
------------------------------------------------------------
[Firestore Sync] Found 3 date(s) to sync: 2026-01-11, 2026-01-12, 2026-01-13
[Firestore Sync] Syncing 45 captures for 2026-01-11
[Firestore Sync] ✓ Synced 2026-01-11
[Firestore Sync] Syncing 52 captures for 2026-01-12
[Firestore Sync] ✓ Synced 2026-01-12
[Firestore Sync] Syncing 48 captures for 2026-01-13
[Firestore Sync] ✓ Synced 2026-01-13

============================================================
SYNC COMPLETE
============================================================
```

### Sync Specific Date
```bash
python manual_firestore_sync.py 2026-01-13
```

---

## Configuration

Firestore sync is automatically enabled when backend is enabled:

```ini
[backend]
enabled = true
url = https://your-backend.run.app

[firebase]
api_key = your_firebase_web_api_key
project_id = your-firebase-project-id
```

---

## Troubleshooting

### Sync Not Running

**Check backend enabled:**
```bash
grep "backend.enabled" ~/.telos/config.ini
```

Should show: `enabled = true`

**Check worker started:**
Look for this log on app startup:
```
[APP] Firestore sync worker started
```

**Check last sync date:**
```python
from core.database import Database
db = Database('~/.telos/tracker.db')
print(db.get_config_value('last_firestore_sync_date'))
```

### Authentication Errors

**Error: "Failed to get Firebase token"**

Solution:
1. Check Firebase API key is correct in config
2. Delete `~/.telos/auth.json` and restart app
3. App will re-authenticate automatically

### No Data to Sync

**Check if captures exist:**
```python
from core.database import Database
db = Database('~/.telos/tracker.db')
captures = db.get_captures_for_date('2026-01-13')
print(f"Found {len(captures)} captures")
```

### Firestore Upload Fails

**Error: "Failed to upload to Firestore: 403"**

Possible causes:
1. Firestore rules too restrictive
2. Invalid authentication token
3. Project ID mismatch

**Check Firestore document:**
```bash
# Using Firebase CLI
firebase firestore:get usage/YOUR_USER_ID
```

---

## Testing

### 1. Verify Sync Worker Starts
```bash
# Start TUI app and check logs
python -m tui.main
```

Look for: `[APP] Firestore sync worker started`

### 2. Manual Sync Test
```bash
# Run manual sync
cd client
python manual_firestore_sync.py

# Check for success messages
```

### 3. Verify Data in Firestore
```bash
# Use Firebase console or CLI
firebase firestore:get usage/YOUR_USER_ID
```

Should see `dayBucket` with dates and captures.

### 4. Verify Backend Can Read Data
```bash
# Run backend debug script
cd backend
node debug-email-scheduler.js
```

Should show captures found for recent dates.

---

## File Structure

```
client/
├── core/
│   ├── firestore_sync.py          # New: Sync worker implementation
│   └── database.py                 # Updated: get_captures_for_date() accepts string dates
├── tui/
│   └── app.py                      # Updated: Starts sync worker
├── manual_firestore_sync.py        # New: Manual sync script
└── FIRESTORE_SYNC_README.md        # This file
```

---

## Implementation Details

### Date Handling

The sync worker properly handles date boundaries:
- **Today (2026-01-14)**: Not synced (data incomplete)
- **Yesterday (2026-01-13)**: Synced (complete day)
- **2026-01-12**: Synced if not already synced
- **Older dates**: Only if within 7-day lookback window

### Concurrent Safety

- Only one sync runs at a time
- Uses `asyncio` for non-blocking operation
- Safe to run manual sync while worker is active (they share same config lock)

### Performance

- Batches all captures for a date into single Firestore write
- Uses REST API (lightweight, no Admin SDK overhead)
- Minimal impact on client performance (runs once per 24h)

---

## Future Improvements

1. **Configurable sync interval**: Allow users to set sync frequency
2. **Progress notifications**: Show sync progress in TUI
3. **Retry logic**: Exponential backoff for failed syncs
4. **Compression**: Compress captures before upload for large datasets
5. **Differential sync**: Only sync new captures, not entire day
6. **Background sync on shutdown**: Sync immediately when app closes

---

## Related Files

- `backend/src/services/summaryGenerator.js` - Reads from Firestore dayBucket
- `backend/src/services/email.js` - Email scheduler that needs this data
- `backend/EMAIL_SCHEDULER_FIXES.md` - Related backend timing fixes

---

## Summary

The Firestore Sync Worker solves the critical gap between local SQLite storage and backend email generation by automatically syncing data daily. This enables the backend email scheduler to function correctly and ensures users receive their daily reports.

**Key Points:**
- ✅ Automatic daily sync (runs in background)
- ✅ Works with long-running sessions
- ✅ Manual sync available for testing/recovery
- ✅ Smart date selection (incremental, no duplicates)
- ✅ Robust error handling
