# Architecture Decisions

Key technical decisions and their rationale.

## [2026-01-03] Firebase Config in Client (v0.1.5)

**Decision:** Embed Firebase Web API Key directly in client config templates.

**Why:**
- Firebase Web API Keys are public by design (used in all web/mobile apps)
- Security comes from backend token verification + Firestore Security Rules
- Actual Gemini API key stays in Secret Manager on backend (never exposed)
- Fixes v0.1.4 bug where missing Firebase config broke backend authentication

**Implementation:** Added Firebase section with Web API Key to `cli.py`, `config.yaml.example`, and auto-migration in `config_manager.py`.

## Authentication: Firebase Anonymous-First

**Decision:** Users start with anonymous Firebase auth, no signup required.

**Why:**
- Zero friction to try the app
- Users see value before committing
- Can link email later without data loss
- Firebase handles token management

**Tradeoffs:**
- Anonymous users can't recover accounts
- Requires careful upgrade flow design

**Implementation:**
```
First launch → Anonymous sign-in → Full app access
Later → Upgrade to email → Data preserved
```

## Backend: Cloud Run (Mumbai Region)

**Decision:** Deploy backend to Cloud Run in `asia-south1` (Mumbai).

**Why:**
- Low latency for Indian users (primary target)
- Auto-scales to zero when not in use
- Pay-per-request pricing
- Managed SSL and deployment

**Tradeoffs:**
- Higher latency for users outside India
- Cold starts (~1-2s) when scaling from zero

**Alternative considered:** Vercel Edge Functions (rejected due to timeout limits)

## Data Storage: Local-First (SQLite)

**Decision:** All user activity data stored locally in SQLite, never uploaded.

**Why:**
- Privacy is core differentiator
- No GDPR concerns
- Works offline
- User owns their data

**Tradeoffs:**
- No cross-device sync
- User must backup manually
- Can't do server-side analytics

**What IS uploaded:**
- Screenshots (for analysis only, deleted immediately)
- Firebase auth tokens (for rate limiting)

**What is NOT uploaded:**
- Activity database
- Session summaries
- Personal insights

## Prompts: Server-Side in Firestore

**Decision:** Store AI prompts in Firestore, not in client code.

**Why:**
- Update prompts without app release
- Keep prompt engineering proprietary
- A/B test different prompt versions
- Consistent analysis across client versions

**Implementation:**
```
Firestore/prompts/screenshot-analysis
  ├── activeVersion: "v2"
  └── versions/v2/content: "<prompt text>"
```

**Fallback:** Client has basic fallback prompt if backend unavailable.

## Rate Limiting: Firestore-Based

**Decision:** Track API usage in Firestore per user UID.

**Why:**
- Distributed (works across Cloud Run instances)
- Atomic transactions (accurate counting)
- Easy to adjust limits
- Can implement quotas per plan later

**Limits:**
- 100 requests/hour (prevents runaway clients)
- 2000 requests/day (generous for normal use)

**Alternative considered:** Redis (rejected - overkill for beta scale)

## UI Framework: Textual (Python TUI)

**Decision:** Build terminal UI with Textual framework.

**Why:**
- Fast development in Python
- Works over SSH
- Low resource usage (~40MB)
- Unique differentiation (not another Electron app)
- Keyboard-first is productivity-focused

**Tradeoffs:**
- Limited visual customization
- Can't embed images
- Learning curve for Textual widgets

**Alternative considered:** Electron (rejected - too heavy, ~200MB+)

## Screenshot Analysis: Gemini Vision

**Decision:** Use Gemini 2.5 Flash for screenshot analysis.

**Why:**
- Best price/performance for vision tasks
- Generous free tier (1500/day)
- Fast responses (~2-3s)
- Good at understanding UI context

**Cost estimate:** ~$20-40/month for 10 active users

**Alternative considered:** GPT-4 Vision (more expensive), local LLM (too slow)

## Session Building: Similarity-Based Grouping

**Decision:** Group captures into sessions based on app/task similarity.

**Why:**
- More meaningful than time-based chunks
- Enables richer AI summaries
- Reflects actual work patterns

**Algorithm:**
```
Similar app + similar task + gap < 10min → Same session
Different app or task or gap > 10min → New session
```

## Perceptual Hashing: Skip Duplicates

**Decision:** Use perceptual hash to skip analyzing duplicate screenshots.

**Why:**
- Reduces API calls by ~50%
- Saves money
- Faster processing
- Same screen = same analysis

**Implementation:** ImageHash library, threshold of 5 for similarity.

## Monorepo: Single Repository

**Decision:** Keep client, backend, shared, website in one repo.

**Why:**
- Easier to keep API contract in sync
- Single PR for client+backend changes
- Simpler for solo developer
- Can split later if needed

**Structure:**
```
telos/
├── client/     (Python)
├── backend/    (Node.js)
├── shared/     (API contract)
├── website/    (Next.js)
└── docs/
```

## Key Learnings

### What Worked Well

1. **Anonymous-first auth** - Users try app immediately
2. **Local-first data** - Privacy as feature, not limitation
3. **Server-side prompts** - Iterate without releases
4. **Perceptual hashing** - 50% API cost reduction
5. **Fallback to local** - App works when backend is down

### What Was Tricky

1. **Textual's Static widget** doesn't handle markdown (use Markdown widget)
2. **Firebase token refresh** requires background task
3. **Cold starts** on Cloud Run need health check warming
4. **Windows service** needs careful error handling
5. **macOS permissions** must be granted manually

### Future Considerations

1. **If scaling:** Consider Redis for rate limiting
2. **If team grows:** Split into separate repos
3. **If going global:** Multi-region Cloud Run
4. **If adding web:** Share auth with Firebase

