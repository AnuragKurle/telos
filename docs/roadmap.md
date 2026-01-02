# Roadmap

Current status, completed phases, and future plans.

## Current Status

**Version:** 0.1.0-beta  
**Last Updated:** January 2026

### What's Working

| Feature | Status |
|---------|--------|
| Screenshot capture (30s interval) | Done |
| Gemini Vision analysis | Done |
| Session building + AI enrichment | Done |
| Daily summaries with productivity scores | Done |
| TUI dashboard | Done |
| AI Chat interface | Done |
| Email reports (Gmail) | Done |
| Windows service (background) | Done |
| Firebase Auth integration | Done |
| Cloud Run backend | Deployed |
| Onboarding flow | Done |
| Trial management (7-day) | Done |
| macOS support | Done |

### Known Limitations

- No export functionality (CSV/JSON/PDF)
- No cross-device sync
- No web dashboard
- Basic error handling (no retry logic)
- Windows-first (macOS needs permissions setup)

## Completed Phases

### Phase 0: Cloud Infrastructure
- Firebase project setup
- Firestore database
- Secret Manager
- Authentication providers

### Phase 1: Backend MVP
- Express API server
- Firebase token verification
- Gemini API integration
- Rate limiting (100/hr, 2000/day)
- Cloud Run deployment

### Phase 2: Client Integration
- Firebase Auth in Python
- Backend screenshot upload
- Automatic fallback to local
- Token management

### Phase 3: Onboarding
- Welcome screen
- Privacy notice
- Trial system (7 days)
- Goal setup
- Email configuration

## In Progress

### Phase 4: Beta Polish
- [ ] Export functionality (CSV/JSON)
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] User feedback system

## Future Plans

### Phase 5: Public Launch
- Code signing certificate
- Auto-update system
- Marketing website
- Product Hunt launch

### Phase 6: Pro Features
- Cloud data sync (opt-in)
- Web dashboard
- Team features
- Advanced analytics

## Feature Ideas

### High Value (Text-Only, Low Storage)

| Feature | Storage/Year | Effort | Value |
|---------|--------------|--------|-------|
| Window titles | 2 MB | 1 hour | High |
| Git context (branch, changes) | 4 MB | 3 hours | High |
| Clipboard history | 50 MB | 2 hours | High |
| Terminal command history | 50 MB | 3 hours | High |

### Medium Value

| Feature | Storage/Year | Effort | Value |
|---------|--------------|--------|-------|
| Browser tabs (titles) | 10 MB | 6 hours | Medium |
| IDE/Editor context | 4 MB | 6 hours | Medium |
| Meeting metadata | 0.5 MB | 6 hours | Medium |

### Future Expansion (High Storage)

| Feature | Storage/Year | Notes |
|---------|--------------|-------|
| Screenshot archive | ~100 GB | Visual proof, re-analysis |
| OCR text extraction | ~3 GB | Full-text search |
| Browser history | ~100 MB | Research tracking |

### Privacy Features (If Screenshots Saved)

- Auto-blur after 30 days
- Sensitive app detection
- Encryption at rest
- On-demand delete
- Emergency wipe command

## Technical Debt

- [ ] Add proper retry logic for API failures
- [ ] Implement query caching
- [ ] Lazy loading for timeline/summary
- [ ] Database query optimization
- [ ] Reduce TUI refresh overhead

## Marketing Positioning

**Tagline:** "Your AI work journal - remember everything you did"

**Key Messages:**
1. Privacy-first: Screenshots deleted instantly, data stays local
2. AI-powered: Understands what you're doing, not just time tracking
3. Chat with data: Ask questions, generate content
4. Lightweight: Runs silently, doesn't slow you down

**Target Audience:**
- Developers tracking coding sessions
- Remote workers needing activity logs
- Privacy-conscious productivity enthusiasts
- Anyone who asks "what did I do yesterday?"

## Success Metrics (Beta)

- [ ] 10+ active beta testers
- [ ] 3+ days average usage
- [ ] No critical crashes
- [ ] Positive feedback on accuracy
- [ ] Feature requests documented

