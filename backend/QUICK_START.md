# Quick Start - Telos Backend Development

Get the backend running locally in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- npm or yarn
- Google Cloud project configured (Phase 0 complete)

## Setup Steps

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp env.example .env
```

Edit `.env` and fill in your values:

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

> **Note:** Get these values from `docs/firebase-credentials.txt` in the project root.

### 3. Authenticate with Google Cloud (for local development)

```bash
# Login to Google Cloud
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set project
gcloud config set project gen-lang-client-0772617718
```

This allows your local backend to access Firestore and Secret Manager.

### 4. Start Development Server

```bash
npm run dev
```

You should see:

```
✅ Firebase Admin initialized for project: gen-lang-client-0772617718
🚀 Telos Backend running on port 8080
📍 Health check: http://localhost:8080/health
🌍 Environment: development
```

### 5. Test It!

In another terminal:

```bash
# Test health endpoint
curl http://localhost:8080/health

# Should return:
# {
#   "status": "ok",
#   "service": "telos-backend",
#   "version": "0.1.0",
#   "timestamp": "2025-01-02T..."
# }
```

## Testing with a Real Screenshot

You'll need a Firebase ID token to test the analysis endpoint.

### Option A: Quick Test with cURL (after getting a token)

```bash
# Get a Firebase token (see Firebase Auth docs or implement in Python client)
TOKEN="your-firebase-id-token-here"

# Test analysis endpoint
curl -X POST http://localhost:8080/v1/analyze/screenshot \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Client-Version: 0.1.0" \
  -F "image=@screenshot.png"
```

### Option B: Use Postman

1. Create a POST request to `http://localhost:8080/v1/analyze/screenshot`
2. Add headers:
   - `Authorization: Bearer <firebase-token>`
   - `X-Client-Version: 0.1.0`
3. In Body tab, select `form-data`
4. Add a field named `image` and select a file

## Project Structure

```
backend/
├── src/
│   ├── server.js              # Express app entry point
│   ├── config/
│   │   └── firebase.js        # Firebase Admin SDK setup
│   ├── middleware/
│   │   ├── auth.js            # Token verification
│   │   ├── rateLimit.js       # Rate limiting
│   │   ├── upload.js          # File upload handling
│   │   └── versionCheck.js    # Client version check
│   ├── routes/
│   │   └── analyze.js         # Analysis endpoints
│   └── services/
│       ├── gemini.js          # Gemini API client
│       ├── prompts.js         # Prompt management
│       └── secrets.js         # Secret Manager client
├── .env                       # Local config (gitignored)
├── .env.example               # Template
├── package.json
├── Dockerfile                 # For Cloud Run
└── README.md
```

## Common Issues

### "Cannot find module" errors

```bash
# Make sure dependencies are installed
npm install

# Check that you're using ES modules (package.json has "type": "module")
```

### "FIREBASE_PROJECT_ID is required"

Your `.env` file is missing or not loaded. Make sure:
1. File is named `.env` (not `.env.txt`)
2. Located in `backend/` directory
3. Has correct values

### "Failed to retrieve secret"

You need to authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

### "Firestore permission denied"

Your Google Cloud account needs Firestore permissions:

```bash
# Check your current account
gcloud auth list

# Make sure you're using the right project
gcloud config set project gen-lang-client-0772617718
```

## Development Workflow

```bash
# 1. Make code changes
# 2. Server auto-restarts (nodemon)
# 3. Test with curl or Postman
# 4. Check logs in terminal
# 5. Repeat!
```

## Next Steps

1. **Test all endpoints** locally
2. **Populate Firestore** with default prompts (if needed)
3. **Deploy to Cloud Run** (see `DEPLOYMENT.md`)
4. **Integrate with Python client** (Phase 2)

## Helpful Commands

```bash
# Run backend
npm run dev

# Run in production mode
npm start

# Install new dependency
npm install package-name

# Check for issues
npm run test  # (when tests are added)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth required) |
| POST | `/v1/analyze/screenshot` | Analyze screenshot (requires auth) |

Full API documentation: `../shared/api-contract.md`

---

**Happy coding!** 🚀

For deployment instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

