# Sync Local Prompts to Firestore

## Quick Sync

Whenever you update prompts in `../client/prompts/`, run:

```powershell
cd D:\Experiments\screentracker\backend
$env:FIREBASE_PROJECT_ID='gen-lang-client-0772617718'
node setup-firestore-prompts.js
```

## What Gets Synced

| Local File | Firestore ID | Used For |
|------------|--------------|----------|
| `client/prompts/screenshot_analysis.txt` | `screenshot-analysis` | Real-time screenshot analysis |
| `client/prompts/session_enrichment.txt` | `session-enrichment` | Session summaries |
| `client/prompts/daily_summary.txt` | `daily-summary` | End-of-day insights |
| `client/prompts/ai_chat_system.txt` | `ai-chat-system` | AI chat queries |

## Source of Truth

✅ **Local files** = source of truth  
☁️ **Firestore** = used by deployed backend  

**Always edit local files first, then sync.**

## One-Time Setup

Create `backend/.env` (if not exists):

```bash
FIREBASE_PROJECT_ID=gen-lang-client-0772617718
GCP_PROJECT_ID=gen-lang-client-0772617718
```

Then you can just run:
```powershell
node setup-firestore-prompts.js
```

