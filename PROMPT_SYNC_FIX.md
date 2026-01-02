# Prompt Sync Fix - Jan 2, 2026

## Issue
The tracker was showing "Unknown - Activity detected" because:
1. **Cloud prompts were outdated** - Using old basic prompt from `setup-firestore-prompts.js`
2. **Backend was overriding AI values** - Hardcoded emoji/color mappings in `gemini.js`
3. **Missing new fields** - `simple_category`, AI-generated emoji/color not passed through

## What Was Fixed

### 1. Synced Local Prompts to Firestore ✅
Updated `backend/setup-firestore-prompts.js` to read from local files:
- `screenshot_analysis.txt` → `screenshot-analysis`
- `session_enrichment.txt` → `session-enrichment`
- `daily_summary.txt` → `daily-summary`
- `ai_chat_system.txt` → `ai-chat-system`

**Result:** All 4 prompts uploaded to Firestore with latest content

### 2. Fixed Backend to Respect AI Autonomy ✅
Updated `backend/src/services/gemini.js`:
- **Before:** Hardcoded emoji/color based on old category names
- **After:** Uses AI-generated `category_emoji` and `category_color` directly
- **Added:** `simple_category` field for statistics mapping
- **Changed:** `detailed_context` now passed as object (not string)

### 3. Updated Prompt Service ✅
Added helper functions in `backend/src/services/prompts.js`:
- `getSessionEnrichmentPrompt()`
- `getDailySummaryPrompt()`
- `getAiChatSystemPrompt()`

## Files Modified
1. `backend/setup-firestore-prompts.js` - Reads from local prompt files
2. `backend/src/services/gemini.js` - Respects AI-generated values
3. `backend/src/services/prompts.js` - Added new prompt getters
4. `backend/SYNC_PROMPTS.md` - Quick reference guide

## Deployment Status
🔄 **Backend deployment in progress** (Cloud Build running)

Once deployed, the backend will:
- Use your latest prompts from Firestore
- Respect AI-generated emoji, colors, and categories
- Include `simple_category` for dashboard statistics

## Testing
After deployment completes, test with:
```bash
# Check backend health
curl https://telos-backend-761085171876.us-central1.run.app/health

# Watch your tracker - should show proper categories now
```

## Going Forward
To update prompts in the future:
```powershell
cd D:\Experiments\screentracker\backend
$env:FIREBASE_PROJECT_ID='gen-lang-client-0772617718'
node setup-firestore-prompts.js
```

Then redeploy backend to pick up changes.

