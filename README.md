# Telos

[![PyPI version](https://badge.fury.io/py/telos-tracker.svg)](https://pypi.org/project/telos-tracker/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered screen time tracker with intelligent activity analysis.

## What It Does

Telos captures screenshots, analyzes them with Gemini Vision AI, and gives you insights about your productivity. All data stays local - screenshots are analyzed and immediately deleted.

## Features

- **Intelligent Tracking** - AI understands what you're working on
- **Smart Sessions** - Groups activities automatically
- **AI Chat** - Query your work patterns naturally
- **Daily Reports** - Email summaries via Gmail
- **Terminal UI** - Clean, keyboard-driven interface
- **Privacy-First** - Data never leaves your device

## Quick Start

### Option 1: pip install (Recommended)

```bash
pip install telos-tracker
telos setup
telos
```

### Option 2: From Source

```bash
cd client
pip install -r requirements.txt
python main.py setup
python main.py
```

### Backend (Node.js)

```bash
cd backend
npm install
npm run dev
```

## Repository Structure

```
telos/
├── client/      Python TUI application
├── backend/     Node.js API (Cloud Run)
├── shared/      API contracts
├── website/     Next.js waitlist site
└── docs/        Documentation
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design and tech stack |
| [Development](docs/development.md) | Local setup guide |
| [Deployment](docs/deployment.md) | Cloud deployment |
| [Roadmap](docs/roadmap.md) | Status and future plans |
| [Decisions](docs/decisions.md) | Architecture rationale |
| [API Contract](shared/api-contract.md) | Backend API spec |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Client | Python, Textual, SQLite |
| Backend | Node.js, Express, Firebase |
| AI | Google Gemini 2.5 Flash |
| Hosting | Google Cloud Run |

## Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| D | Dashboard |
| T | Timeline |
| S | Summary |
| A | AI Chat |
| G | Goals |
| H | Help |
| Q | Quit |

## Git Branches

- `main-monorepo` - Development
- `prod-monorepo` - Production

## Links

- **PyPI Package**: https://pypi.org/project/telos-tracker/
- **Backend**: https://telos-backend-ae7k4avtpq-el.a.run.app
- **Firebase**: gen-lang-client-0772617718

## For Developers

- **Publishing to PyPI**: See [client/QUICKSTART_PUBLISHING.md](client/QUICKSTART_PUBLISHING.md)
- **Release Management**: See [docs/releases.md](docs/releases.md)
- **Full Publishing Guide**: See [client/PUBLISHING.md](client/PUBLISHING.md)

## License

MIT
