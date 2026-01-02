# Telos

AI-powered screen time tracker with intelligent activity analysis using Gemini Vision API.

> **Note:** This repository is now a monorepo containing both the Python client and Node.js backend.

---

## 🚀 Quick Start

### For Users (Desktop App)

```bash
cd client
pip install -r requirements.txt
python main.py setup
python main.py
```

**Full documentation:** [`client/README.md`](client/README.md)

### For Developers (Backend)

```bash
cd backend
npm install
npm run dev
```

**Full documentation:** [`backend/README.md`](backend/README.md)

---

## 📂 Repository Structure

```
telos/
├─ client/         → Python TUI application (fully functional)
├─ backend/        → Node.js Express API (in development)
├─ shared/         → API contracts and shared resources
└─ docs/           → Documentation and setup guides
```

---

## ✨ Features

- 🎯 **Intelligent Tracking** - AI understands what you're working on
- 🤖 **Gemini Vision** - Analyzes screenshots with context
- 📊 **Smart Sessions** - Groups activities automatically  
- 💬 **AI Chat** - Query your work patterns naturally
- 📧 **Daily Reports** - Email summaries via Gmail
- 🖥️ **Terminal UI** - Clean, responsive TUI
- 🔒 **Privacy-First** - Screenshots analyzed and deleted immediately

---

## 🏗️ Architecture (Beta)

**Current:** Python client works standalone (local Gemini calls)  
**Building:** Node.js backend for SaaS (proxy Gemini calls, keep prompts proprietary)

```
Client (Python TUI) → Backend (Cloud Run) → Gemini API
        ↓                      ↓
    SQLite              Firestore
```

**Status:**
- ✅ Client v0.9 - Fully functional
- 🚧 Backend v0.1 - Phase 1 in progress
- 📋 Cloud Deploy - Phase 0 next (Firebase setup)

---

## 📚 Documentation

- **[Client README](client/README.md)** - Usage, features, troubleshooting
- **[Backend README](backend/README.md)** - Development, deployment
- **[API Contract](shared/api-contract.md)** - Client-backend specification
- **[Phase 0 Guide](docs/PHASE_0_FIREBASE_SETUP.md)** - Firebase/GCP setup (20-30 min)
- **[Monorepo Guide](MONOREPO_MIGRATION_GUIDE.md)** - Repository structure

---

## 🛠️ Development

### Run Client
```bash
cd client
python main.py
```

### Run Backend (local)
```bash
cd backend
npm run dev
```

### Run Both (docker-compose)
```bash
docker-compose up -d
```

---

## 🗺️ Roadmap

### ✅ Phase 0: Foundation (Complete)
- Python client with full local functionality
- TUI interface, session building, AI insights

### 🚧 Phase 1: Backend MVP (In Progress)
- Node.js Express API
- Firebase Authentication
- Screenshot upload endpoint
- Server-side Gemini calls

### 📋 Phase 2: Client Integration (Next)
- Firebase Auth in Python client
- Backend screenshot upload
- Fallback to local analysis

### 📋 Phase 3: Beta Launch
- Cloud Run deployment
- Public beta testing
- Onboarding flow

---

## 📄 License

MIT License

---

## 🔗 Quick Links

- [Client Documentation](client/README.md)
- [Backend Documentation](backend/README.md)
- [API Contract](shared/api-contract.md)
- [Firebase Setup Guide](docs/PHASE_0_FIREBASE_SETUP.md)
- [Build Plan](.cursor/plans/telos_beta_build_(firebase+cloudrun)_c3e9f41c.plan.md)

---

**Questions?** Check the docs or open an issue!
