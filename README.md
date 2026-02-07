# Telos

[![PyPI version](https://badge.fury.io/py/telos-tracker.svg)](https://pypi.org/project/telos-tracker/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered screen time tracker. Captures screenshots, analyzes them with Gemini Vision, and shows you where your time actually goes. Screenshots are analyzed in real-time and immediately deleted — only structured insights stay, encrypted and local.

## Monorepo Structure

This is a monorepo with three independent components:

```
telos/
├── client/          # Python TUI app (pip install telos-tracker)
├── backend/         # Node.js API on Google Cloud Run
├── website/         # Next.js marketing site + admin dashboard (Firebase Hosting)
├── shared/          # API contracts, types, constants
└── docs/            # Architecture, deployment, decisions
```

### client/ — The Product

Python application with a terminal UI (Textual). This is what end users install and run.

- **Screen capture** → Gemini Vision analysis → SQLite storage
- **TUI dashboard** with timeline, heatmaps, focus scores
- **AI chat** — ask questions about your day in natural language
- **Local web dashboard** at `localhost:5555` with interactive Chart.js charts
- **Daily email reports** with embedded charts and AI-generated narratives
- **MCP server** for Claude Desktop / Cursor integration
- **Service mode** — runs headless in the background

Install: `pip install telos-tracker && telos setup && telos`

### backend/ — The API

Node.js + Express on Google Cloud Run. Handles:

- Firebase Auth token validation
- Screenshot analysis relay (Gemini via Portkey)
- Daily summary storage + email reports (SendGrid)
- Subscription management (Dodo Payments)
- Admin API for waitlist, campaigns, user management
- Slack notifications for signups, feedback, alerts

Deploy: `cd backend && bash deploy.sh`

### website/ — Marketing + Admin

Next.js static site on Firebase Hosting. Two parts:

- **Public pages** — landing page, pricing, privacy policy
- **Admin panel** (`/admin`) — waitlist management, batch invitations, user overview, campaign history

Deploy: `cd website && npm run build && npx firebase deploy --only hosting`

## Branches

| Branch | Purpose |
|--------|---------|
| `main-monorepo` | Development — all new work goes here |
| `prod-monorepo` | Production — deployed code, merged from main |

## Key Infrastructure

| Service | What |
|---------|------|
| **Google Cloud Run** | Backend API (`telos-backend`) |
| **Firebase** | Auth, Firestore, Hosting |
| **Google Cloud Secret Manager** | API keys (Gemini, SendGrid, Portkey, Dodo) |
| **SendGrid** | Transactional emails (daily reports, invitations) |
| **Dodo Payments** | Subscriptions ($3/mo Pro plan) |
| **PyPI** | Client distribution (`telos-tracker`) |

## Quick Reference

```bash
# Install & run the client
pip install telos-tracker
telos setup
telos

# Run client from source
cd client && pip install -r requirements.txt && python main.py

# Run backend locally
cd backend && npm install && npm run dev

# Deploy backend
cd backend && bash deploy.sh

# Deploy website
cd website && npm run build && npx firebase deploy --only hosting

# Publish to PyPI
cd client && python -m build && twine upload dist/*
```

## Environment Variables

### Backend (.env)

```
FIREBASE_PROJECT_ID, GCP_PROJECT_ID
GEMINI_SECRET_NAME          # GCP Secret Manager key name
SENDGRID_API_KEY            # Direct or via Secret Manager
SENDGRID_FROM_EMAIL         # Verified sender
DODO_PAYMENTS_API_KEY       # Payment processing
PORTKEY_API_KEY             # AI observability
SLACK_ALERTS_WEBHOOK        # Slack notifications
```

### Website (.env.local)

```
NEXT_PUBLIC_FIREBASE_*      # Firebase config
NEXT_PUBLIC_BACKEND_URL     # Cloud Run URL
```

### Client (config.yaml)

Created by `telos setup`. Stores Gemini API key, backend URL, user preferences. Located at `~/.telos/config.yaml`.

## License

MIT
