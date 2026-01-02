# Telos - AI-Powered Activity Tracker

> **Note:** This repository has been reorganized into a monorepo structure to support both the Python client and Node.js backend.

---

## 🏗️ Repository Structure

```
telos/
├─ client/         → Python TUI application (desktop app)
├─ backend/        → Node.js Express API (Cloud Run backend)
├─ shared/         → API contracts and shared resources
├─ docs/           → Documentation and setup guides
└─ README.md       → This file
```

---

## 🚀 Quick Start

### For Users (Desktop App)

```bash
# Navigate to client
cd client

# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python main.py setup

# Start the TUI
python main.py
```

**Full client documentation:** See [`client/README.md`](client/README.md)

### For Developers (Backend)

```bash
# Navigate to backend
cd backend

# Install dependencies
npm install

# Set up environment
cp env.example .env
# Edit .env with your credentials

# Run locally
npm run dev
```

**Full backend documentation:** See [`backend/README.md`](backend/README.md)

---

## 📚 What is Telos?

Telos is an AI-powered screen time tracker that uses **Gemini Vision AI** to analyze what you're working on and help you understand your productivity patterns.

### Key Features

- **🎯 Intelligent Activity Tracking** - Automatically captures and analyzes your screen activity
- **🤖 AI-Powered Insights** - Gemini Vision understands what you're working on
- **📊 Session Building** - Groups similar activities into meaningful work sessions
- **💬 AI Chat Interface** - Ask questions about your work patterns
- **📧 Daily Email Reports** - Beautiful summaries delivered to your inbox
- **🖥️ Terminal UI** - Clean, responsive TUI built with Textual
- **🔒 Privacy-First** - Screenshots analyzed and immediately deleted

### Architecture (Beta)

```
┌─────────────┐       ┌──────────────┐       ┌──────────────┐
│   Python    │       │   Node.js    │       │    Gemini    │
│   Client    │──────▶│   Backend    │──────▶│  Vision API  │
│    (TUI)    │       │ (Cloud Run)  │       │              │
└─────────────┘       └──────────────┘       └──────────────┘
      │                      │
      │                      │
      ▼                      ▼
┌─────────────┐       ┌──────────────┐
│   SQLite    │       │  Firestore   │
│   (Local)   │       │   (Cloud)    │
└─────────────┘       └──────────────┘
```

**Current Status:** 🚧 **Beta Architecture in Development**

- ✅ **Client (v0.9)** - Fully functional Python TUI (works standalone)
- 🚧 **Backend (v0.1)** - In development (Phase 1)
- 📋 **Cloud Deploy** - Not yet available

For now, the client works completely locally with your own Gemini API key. The backend is being built to enable SaaS features (no API key required, cloud sync, etc.).

---

## 📖 Documentation

### Getting Started
- **[Client Setup & Usage](client/README.md)** - How to use the Python desktop app
- **[Backend Development](backend/README.md)** - How to work on the Node.js API
- **[Phase 0: Firebase Setup](docs/PHASE_0_FIREBASE_SETUP.md)** - Cloud infrastructure setup guide

### Architecture & Design
- **[API Contract](shared/api-contract.md)** - Client-backend API specification
- **[Monorepo Migration Guide](MONOREPO_MIGRATION_GUIDE.md)** - How this repo was reorganized
- **[Beta Build Plan](.cursor/plans/telos_beta_build_(firebase+cloudrun)_c3e9f41c.plan.md)** - Full deployment roadmap

### Current Status
- **[Current Status](CURRENT_STATUS.md)** - Detailed feature progress
- **[Quick Start](QUICK_START.md)** - Fast setup guide
- **[Session Summary](SESSION_SUMMARY.md)** - Recent development summary

---

## 🛠️ Development

### Prerequisites

**For Client:**
- Python 3.8+
- pip

**For Backend:**
- Node.js 18+
- npm
- Google Cloud account (for deployment)

### Local Development Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/telos.git
cd telos
```

**2. Set up client (Python)**
```bash
cd client
pip install -r requirements.txt
python main.py setup
```

**3. Set up backend (Node.js)**
```bash
cd ../backend
npm install
cp env.example .env
# Edit .env with your Firebase/GCP credentials
npm run dev
```

**4. Run both together** (once backend is complete)
```bash
# Terminal 1: Backend
cd backend && npm run dev

# Terminal 2: Client (pointing to local backend)
cd client && python main.py --backend-url http://localhost:8080
```

---

## 🗺️ Roadmap

### ✅ Phase 0: Foundation (Complete)
- Python client with full local functionality
- Screenshot capture and analysis
- SQLite database
- TUI interface
- Session building and AI insights

### 🚧 Phase 1: Backend MVP (In Progress)
- Node.js Express API
- Firebase Authentication
- Screenshot upload endpoint
- Gemini proxy (server-side API calls)
- Rate limiting and security

### 📋 Phase 2: Client Integration (Next)
- Firebase Auth in Python client
- Backend screenshot upload
- Fallback to local analysis
- Token management

### 📋 Phase 3: Beta Launch (Future)
- Cloud Run deployment
- Public beta testing
- Onboarding flow
- Email capture

### 📋 Phase 4: Pro Features (Future)
- Cloud data sync (opt-in)
- Cross-device support
- Web dashboard
- Team features

---

## 🤝 Contributing

This is currently a personal project in active development. The codebase will be open-sourced after the beta launch.

If you're interested in contributing or testing early:
- Check the [Beta Build Plan](.cursor/plans/telos_beta_build_(firebase+cloudrun)_c3e9f41c.plan.md)
- Read the [API Contract](shared/api-contract.md)
- Reach out if you'd like to help!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **Documentation:** [`docs/`](docs/)
- **API Contract:** [`shared/api-contract.md`](shared/api-contract.md)
- **Client README:** [`client/README.md`](client/README.md)
- **Backend README:** [`backend/README.md`](backend/README.md)

---

**Questions?** Check the documentation in [`docs/`](docs/) or open an issue!

