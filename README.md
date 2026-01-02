# Telos

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

### Desktop App (Python)

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

- **Backend**: https://telos-backend-ae7k4avtpq-el.a.run.app
- **Firebase**: gen-lang-client-0772617718

## License

MIT
