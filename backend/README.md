# Telos Backend

Node.js + Express backend for Telos screenshot analysis service.

## Architecture

- **Framework:** Express.js
- **Auth:** Firebase Admin SDK (token verification)
- **AI:** Google Gemini API (server-side calls)
- **Database:** Firestore (prompts, users, usage tracking)
- **Secrets:** Google Secret Manager
- **Deployment:** Google Cloud Run

## Local Development

### Prerequisites

- Node.js 18+ and npm
- Firebase project set up (see `../docs/PHASE_0_FIREBASE_SETUP.md`)
- Gemini API key stored in Secret Manager

### Setup

```bash
cd backend
npm install
cp .env.example .env
# Fill in .env with your Firebase/GCP credentials
npm run dev
```

Server will run at `http://localhost:8080`

### Environment Variables

```
PORT=8080
FIREBASE_PROJECT_ID=your-project-id
GCP_PROJECT_ID=your-project-id
GEMINI_SECRET_NAME=GEMINI_API_KEY
NODE_ENV=development
```

## API Endpoints

See `../shared/api-contract.md` for full API documentation.

### Health Check
```
GET /health
```

### Screenshot Analysis
```
POST /v1/analyze/screenshot
Authorization: Bearer <firebase-id-token>
Content-Type: multipart/form-data

Body:
  image: <screenshot file>
```

## Project Structure

```
backend/
├── src/
│   ├── server.js           # Express app entry point
│   ├── routes/
│   │   └── analyze.js      # Analysis endpoints
│   ├── middleware/
│   │   ├── auth.js         # Firebase token verification
│   │   ├── rateLimit.js    # Rate limiting
│   │   └── logger.js       # Request logging
│   ├── services/
│   │   ├── gemini.js       # Gemini API client
│   │   ├── prompts.js      # Prompt management
│   │   └── secrets.js      # Secret Manager client
│   └── utils/
│       └── validation.js   # Input validation
├── Dockerfile              # For Cloud Run deployment
├── .dockerignore
├── package.json
└── README.md
```

## Testing Locally

```bash
# Start backend
npm run dev

# In another terminal, test with curl
curl -X POST http://localhost:8080/v1/analyze/screenshot \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -F "image=@test-screenshot.png"
```

## Deployment

See Phase 1 deployment docs for Cloud Run deployment instructions.

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/telos-backend

# Deploy to Cloud Run
gcloud run deploy telos-backend \
  --image gcr.io/PROJECT_ID/telos-backend \
  --platform managed \
  --region us-central1
```

## Security Notes

- Never log request bodies (images are sensitive)
- Firebase tokens are verified on every request
- Rate limits enforced per user and per IP
- Secrets loaded from Secret Manager (never hardcoded)

## Phase 1 Implementation - COMPLETE ✅

All Phase 1 features have been implemented:

- ✅ Firebase Admin SDK integration
- ✅ Token verification middleware
- ✅ Client version checking (426 responses)
- ✅ Firestore-based rate limiting (100/hour, 2000/day)
- ✅ Secret Manager integration
- ✅ Gemini API integration
- ✅ Screenshot upload endpoint
- ✅ Deployment scripts and documentation

## Quick Start

See [`QUICK_START.md`](QUICK_START.md) for local development setup.

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for Cloud Run deployment instructions.

Use the deployment scripts:
- **Linux/Mac:** `./deploy.sh`
- **Windows:** `.\deploy.ps1`

## Status

✅ **Phase 1 Complete** - Ready for deployment and integration with Python client

