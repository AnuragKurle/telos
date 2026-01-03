# Telos Backend

Node.js backend for Telos screen time tracker. Handles screenshot analysis with Gemini Vision and user feedback collection.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Slack (Required)

Slack webhooks are stored in GCP Secret Manager for security:

```bash
npm run setup:slack
```

This interactive wizard will:
- Create secrets in GCP Secret Manager
- Keep credentials out of Git
- Show you commands to grant Cloud Run access

**See:** `SLACK_SETUP.md` for detailed instructions

### 3. Set Environment Variables

For local development, create `.env` (not committed to Git):

```bash
# .env
GCP_PROJECT_ID=gen-lang-client-0772617718
SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH
PORT=8080

# Optional: Local overrides (use Secret Manager in production)
# SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

### 4. Run Locally

```bash
npm run dev
```

Backend will start on http://localhost:8080

### 5. Test

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test Slack integration
npm run test:slack
```

## Deployment

Deploy to Google Cloud Run:

```bash
# Windows
.\deploy-anywhere.ps1

# Linux/Mac
./deploy.sh
```

**Production URL:** https://telos-backend-ae7k4avtpq-el.a.run.app

## API Endpoints

See `../shared/api-contract.md` for full API specification.

### Health Check

```http
GET /health
```

No authentication required.

### Analyze Screenshot

```http
POST /v1/analyze/screenshot
Authorization: Bearer <firebase-token>
Content-Type: multipart/form-data

Body: image file (PNG/JPEG/WebP)
```

Returns AI analysis of screenshot.

### Submit Feedback

```http
POST /v1/feedback
Authorization: Bearer <firebase-token>
Content-Type: application/json

{
  "feedback_type": "summary",
  "feedback_text": "Category should be Learning",
  "context": { "summary_id": 123 },
  "metadata": { "app_version": "0.1.0" }
}
```

Returns: `{ success: true, feedback_id: "...", slack_notified: true }`

## Architecture

```
backend/
├── src/
│   ├── config/
│   │   └── firebase.js          # Firebase Admin SDK setup
│   ├── middleware/
│   │   ├── auth.js              # Firebase token verification
│   │   ├── rateLimit.js         # Rate limiting per user
│   │   ├── upload.js            # Multer image upload
│   │   └── versionCheck.js      # Client version check
│   ├── routes/
│   │   ├── analyze.js           # Screenshot analysis endpoint
│   │   ├── auth.js              # Authentication endpoints
│   │   └── feedback.js          # Feedback submission
│   ├── services/
│   │   ├── gemini.js            # Gemini Vision API client
│   │   ├── prompts.js           # Load prompts from Firestore
│   │   ├── secrets.js           # GCP Secret Manager client
│   │   └── slack.js             # Slack notifications
│   └── server.js                # Express app entry point
├── setup-firestore-prompts.js   # Sync prompts to Firestore
├── setup-slack-secrets.js       # Configure Slack secrets
└── deploy-anywhere.ps1          # Deployment script
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GCP_PROJECT_ID` | Yes | Google Cloud project ID | `gen-lang-client-0772617718` |
| `PORT` | No | Server port (default: 8080) | `8080` |
| `SLACK_FEEDBACK_CHANNEL_ID` | Yes | Slack channel for feedback | `C0A6VF5PBUH` |
| `GEMINI_SECRET_NAME` | No | Secret Manager secret name | `GEMINI_API_KEY` |
| `SLACK_WEBHOOK_SECRET_NAME` | No | Secret Manager secret name | `SLACK_WEBHOOK` |

## Secrets (GCP Secret Manager)

| Secret Name | Purpose | How to Set |
|-------------|---------|------------|
| `GEMINI_API_KEY` | Gemini Vision API key | Already configured |
| `SLACK_WEBHOOK` | Slack webhook URL | `npm run setup:slack` |
| `SLACK_BOT_TOKEN` | Slack bot token (alternative) | `npm run setup:slack` |

**Important:** Secrets are loaded from GCP Secret Manager, NOT from environment variables in production. Use `.env` only for local development.

## Key Features

### 1. Privacy-First Design

- Screenshots are **never stored** permanently
- Analysis happens in-memory only
- User data stays in client SQLite

### 2. Server-Side Prompts

AI prompts are stored in Firestore, not code:

```bash
npm run setup  # Syncs client/prompts/ to Firestore
```

Update prompts without redeploying the backend.

### 3. Rate Limiting

Per-user limits (by Firebase UID):
- 100 requests/hour
- 2,000 requests/day

Tracked in Firestore `rate_limits` collection.

### 4. Feedback with Slack Integration

- Feedback saved to Firestore (never lost)
- Slack notifications sent asynchronously
- Tracks delivery status in Firestore
- Warns user if Slack fails

See `docs/MONITORING_FEEDBACK.md` for monitoring.

### 5. Fallback Strategy

If backend is unreachable, client falls back to local Gemini API.

## Development

### Local Development with Mock Data

Set `MOCK_ANALYSIS=true` to return mock responses without calling Gemini:

```bash
MOCK_ANALYSIS=true npm run dev
```

### Hot Reload

Uses `nodemon` to auto-reload on file changes:

```bash
npm run dev
```

### Testing Endpoints

```bash
# Get a Firebase token from client
cd ../client
python -c "
from core.firebase_auth import FirebaseAuth
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
auth = FirebaseAuth(config['firebase']['api_key'])
print(auth.get_token())
"

# Use token in requests
TOKEN="your-firebase-token"

# Test analysis
curl -X POST http://localhost:8080/v1/analyze/screenshot \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Client-Version: 0.1.0" \
  -F "image=@screenshot.png"

# Test feedback
curl -X POST http://localhost:8080/v1/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feedback_type":"general","feedback_text":"Test"}'
```

## Troubleshooting

### "Secret not found" error

**Cause:** Secrets not configured in GCP Secret Manager

**Fix:**
```bash
npm run setup:slack
```

### "Permission denied" accessing secrets

**Cause:** Cloud Run service account doesn't have access

**Fix:**
```bash
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:gen-lang-client-0772617718@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Slack notifications not working

**Cause:** Multiple possible issues

**Fix:**
```bash
# Check Slack configuration
npm run check:slack

# Test Slack integration
npm run test:slack

# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

See `SLACK_SETUP.md` for detailed troubleshooting.

### Cold start latency

Cloud Run has ~1-2s cold start time when idle. First request after idle is slower.

**Mitigation:**
- Use Cloud Run minimum instances (costs money)
- Or accept cold starts (better for beta)

## Monitoring

### Check Backend Health

```bash
curl https://telos-backend-ae7k4avtpq-el.a.run.app/health
```

### View Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=telos-backend" \
  --limit 50 --format json
```

### Query Failed Feedback

See `docs/MONITORING_FEEDBACK.md` for monitoring Slack failures.

## Documentation

- **API Contract:** `../shared/api-contract.md`
- **Slack Setup:** `SLACK_SETUP.md`
- **Deployment:** `DEPLOYMENT.md`
- **Testing:** `TEST_FEEDBACK_FLOW.md`
- **Monitoring:** `../docs/MONITORING_FEEDBACK.md`
- **Architecture:** `../docs/architecture.md`

## NPM Scripts

```bash
npm run dev           # Start with hot reload
npm run start         # Start production server
npm run setup         # Sync prompts to Firestore
npm run setup:slack   # Configure Slack secrets
npm run check:slack   # Check Slack configuration
npm run test:slack    # Test Slack integration
```

## Tech Stack

- **Runtime:** Node.js 18+
- **Framework:** Express.js
- **AI:** Google Gemini 2.5 Flash
- **Auth:** Firebase Admin SDK
- **Hosting:** Google Cloud Run (asia-south1/Mumbai)
- **Secrets:** GCP Secret Manager
- **Database:** Firestore (prompts, rate limits, feedback)

## Security

✅ **Best Practices:**
- Secrets in Secret Manager, not Git
- Firebase token verification on all endpoints
- Rate limiting per user
- No logging of request bodies (images are sensitive)
- CORS configured for production domain

❌ **Never Do:**
- Commit secrets to Git
- Log request bodies or tokens
- Skip authentication middleware
- Store screenshots permanently

## Contributing

Before making changes:
1. Read `../docs/architecture.md` for system design
2. Read `../docs/decisions.md` for architectural decisions
3. Update `../shared/api-contract.md` if changing API
4. Test locally before deploying
5. Check `../.cursorrules` for project conventions

## Support

- **Issues:** Found in production? Check Cloud Run logs first
- **Slack Setup:** See `SLACK_SETUP.md`
- **Architecture:** See `../docs/architecture.md`
- **Decisions:** See `../docs/decisions.md`
