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
- ☁️ **Cloud Backend** - Server-side analysis with local fallback
- 📊 **Smart Sessions** - Groups activities automatically  
- 💬 **AI Chat** - Query your work patterns naturally
- 📧 **Daily Reports** - Email summaries via Gmail
- 🖥️ **Terminal UI** - Clean, responsive TUI
- 🔒 **Privacy-First** - Screenshots analyzed and deleted immediately
- 🔐 **Firebase Auth** - Secure authentication with Google
- 🌏 **Mumbai Deployment** - Low-latency for Indian users

---

## 🏗️ Architecture

**Cloud-Integrated Architecture** (with local fallback)

```
Client (Python TUI) → Backend (Cloud Run - Mumbai) → Gemini API
        ↓                      ↓
    SQLite              Firestore (Prompts)
```

**Backend Features:**
- 🔒 Server-side prompts (proprietary intelligence)
- 🔐 Firebase Authentication
- 🌏 Deployed to Mumbai (asia-south1)
- 🔄 Auto-fallback to local analysis
- 📊 Rate limiting & usage tracking

**Status:**
- ✅ Client v1.0 - Production ready
- ✅ Backend v1.0 - Deployed to Cloud Run
- ✅ Firebase Auth - Integrated
- ✅ Prompt Sync - Local → Firestore

---

## 📚 Documentation

### User Guides
- **[Client README](client/README.md)** - Usage, features, troubleshooting
- **[Quick Start (Phase 1)](START_PHASE_1.md)** - Local-only setup
- **[Phase 2 Setup](START_PHASE_2.md)** - Cloud backend integration

### Developer Guides
- **[Backend README](backend/README.md)** - Development, deployment
- **[Deployment Guide](backend/DEPLOY_MANUALLY.md)** - Deploy to Cloud Run
- **[Prompt Sync](backend/SYNC_PROMPTS.md)** - Update cloud prompts
- **[API Contract](shared/api-contract.md)** - Client-backend specification
- **[Firebase Setup](docs/PHASE_0_FIREBASE_SETUP.md)** - Firebase/GCP setup
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
- Local Gemini API integration

### ✅ Phase 1: Backend MVP (Complete)
- Node.js Express API on Cloud Run
- Firebase Authentication
- Screenshot upload endpoint
- Server-side Gemini calls
- Firestore prompt management

### ✅ Phase 2: Client Integration (Complete)
- Firebase Auth in Python client
- Backend screenshot upload
- Automatic fallback to local analysis
- Health checks and rate limiting
- Mumbai region deployment

### 🚧 Phase 3: Intelligence & Polish (In Progress)
- Session enrichment with AI summaries
- Daily email reports
- AI chat interface improvements
- Goal tracking system

### 📋 Phase 4: Beta Launch (Next)
- Public beta testing
- User onboarding flow
- Marketing website
- Documentation polish

---

## 📄 License

MIT License

---

## 🔗 Quick Links

### Getting Started
- [Client Documentation](client/README.md)
- [Phase 1 Setup (Local)](START_PHASE_1.md)
- [Phase 2 Setup (Cloud)](START_PHASE_2.md)

### Development
- [Backend Documentation](backend/README.md)
- [Deploy Backend](backend/DEPLOY_MANUALLY.md)
- [Sync Prompts](backend/SYNC_PROMPTS.md)
- [API Contract](shared/api-contract.md)

### Reference
- [Firebase Setup Guide](docs/PHASE_0_FIREBASE_SETUP.md)
- [Recent Fixes](PROMPT_SYNC_FIX.md)
- [Phase 1 Summary](PHASE_1_SUMMARY.md)

---

**Questions?** Check the docs or open an issue!
