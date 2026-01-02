# Development Guide

Get the client and backend running locally for development.

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.8+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 8+ | `npm --version` |
| Google Cloud SDK | Latest | `gcloud --version` |

## Client Setup (Python)

### 1. Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml`:

```yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY"  # Get from https://aistudio.google.com/app/apikey

capture:
  interval_seconds: 30
  idle_threshold: 300

email:
  enabled: false  # Set true and configure for daily reports
```

### 3. Run Setup Wizard

```bash
python main.py setup
```

### 4. Start the App

```bash
python main.py
```

**Keyboard shortcuts in TUI:**
- `D` - Dashboard
- `T` - Timeline
- `S` - Summary
- `A` - AI Chat
- `C` - Settings
- `G` - Goals
- `H` - Help
- `Q` - Quit

## Backend Setup (Node.js)

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Environment

```bash
cp env.example .env
```

Edit `.env`:

```env
PORT=8080
NODE_ENV=development
FIREBASE_PROJECT_ID=gen-lang-client-0772617718
GCP_PROJECT_ID=gen-lang-client-0772617718
GEMINI_SECRET_NAME=GEMINI_API_KEY
MIN_CLIENT_VERSION=0.1.0
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=2000
```

### 3. Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project gen-lang-client-0772617718
```

### 4. Start Development Server

```bash
npm run dev
```

Server runs at `http://localhost:8080`

### 5. Test Health Endpoint

```bash
curl http://localhost:8080/health
```

## Running Both Together

**Terminal 1 - Backend:**
```bash
cd backend
npm run dev
```

**Terminal 2 - Client:**
```bash
cd client
python main.py
```

The client will auto-detect local backend if configured.

## Environment Variables Reference

### Client (`client/config.yaml`)

| Key | Description | Default |
|-----|-------------|---------|
| `gemini.api_key` | Your Gemini API key | Required |
| `capture.interval_seconds` | Screenshot interval | 30 |
| `capture.idle_threshold` | Idle detection timeout | 300 |
| `email.enabled` | Enable daily reports | false |
| `backend.enabled` | Use cloud backend | false |
| `backend.url` | Backend URL | - |

### Backend (`.env`)

| Key | Description | Required |
|-----|-------------|----------|
| `FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `GCP_PROJECT_ID` | Google Cloud project ID | Yes |
| `GEMINI_SECRET_NAME` | Secret Manager key name | Yes |
| `MIN_CLIENT_VERSION` | Minimum client version | Yes |
| `RATE_LIMIT_PER_HOUR` | Requests per hour limit | Yes |
| `RATE_LIMIT_PER_DAY` | Requests per day limit | Yes |

## Common Tasks

### Update AI Prompts

Edit files in `client/prompts/`:
- `screenshot_analysis.txt` - How screenshots are analyzed
- `session_enrichment.txt` - How sessions are summarized
- `daily_summary.txt` - Daily narrative generation
- `ai_chat_system.txt` - AI Chat personality

### Sync Prompts to Firestore

```bash
cd backend
node setup-firestore-prompts.js
```

### Run as Background Service (Windows)

```bash
cd client
python main.py service-console    # Test mode
python main.py install-service    # Install
python main.py start-service      # Start
```

### Build Executable

```bash
cd client
python build_installer.py         # Windows
python build_macos.py             # macOS
```

## Troubleshooting

### "Module not found" in Python

```bash
pip install -r requirements.txt
```

### "FIREBASE_PROJECT_ID is required"

Make sure `.env` file exists and is properly formatted.

### "Failed to retrieve secret"

```bash
gcloud auth application-default login
```

### Firestore permission denied

```bash
gcloud config set project gen-lang-client-0772617718
```

### Client can't connect to local backend

Check backend is running on port 8080 and `backend.enabled: true` in client config.

