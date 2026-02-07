# Backend

Node.js + Express API running on Google Cloud Run (`asia-south1`).

**Production URL:** `https://telos-backend-ae7k4avtpq-el.a.run.app`

## What It Does

- Validates Firebase Auth tokens
- Relays screenshots to Gemini Vision (via Portkey) for analysis
- Stores daily summaries in Firestore and sends email reports (SendGrid)
- Manages subscriptions and payments (Dodo Payments)
- Sends Slack notifications for signups, feedback, referrals, alerts
- Exposes admin API for waitlist, campaigns, and user management

## Project Structure

```
backend/
├── src/
│   ├── server.js              # Express app entry point
│   ├── config/
│   │   ├── beta_users.js      # Beta user configuration
│   │   └── firebase.js        # Firebase Admin SDK init
│   ├── middleware/
│   │   ├── auth.js            # Firebase token verification
│   │   ├── rateLimit.js       # Per-user rate limiting
│   │   ├── subscriptionCheck.js
│   │   ├── upload.js          # File upload handling (multer)
│   │   └── versionCheck.js    # Client version gating
│   ├── routes/
│   │   ├── admin.js           # Admin endpoints (waitlist, campaigns, digest)
│   │   ├── analyze.js         # POST /v1/analyze/screenshot
│   │   ├── auth.js            # Signup, verify-access, payment intent
│   │   ├── checkout.js        # Dodo Payments webhooks
│   │   ├── feedback.js        # POST /v1/feedback
│   │   ├── referral.js        # Referral code generation and tracking
│   │   ├── reports.js         # Email preferences, trigger daily emails
│   │   └── webReport.js       # Web-based report viewer
│   ├── services/
│   │   ├── email.js           # SendGrid: daily reports, HTML generation
│   │   ├── encryption.js      # AES-256 encryption for stored data
│   │   ├── gemini.js          # Gemini Vision API client (via Portkey)
│   │   ├── inviteEmail.js     # Invitation email templates
│   │   ├── monitoring.js      # Performance monitoring + Slack alerts
│   │   ├── prompts.js         # Prompt loading from Firestore
│   │   ├── scheduler.js       # Cron: daily email reports, trial expiry
│   │   ├── secrets.js         # GCP Secret Manager client
│   │   ├── sentry.js          # Error tracking
│   │   ├── slack.js           # Slack webhook notifications (24+ types)
│   │   └── summaryGenerator.js # AI summary generation from usage data
│   └── tests/
│       ├── referral.test.js
│       └── slack-notifications.test.js
├── Dockerfile
├── deploy.ps1                 # Windows deployment script
├── deploy.sh                  # Linux/macOS deployment script
├── deploy-anywhere.ps1        # Wrapper that loads gcloud SDK
├── setup-scheduler.sh         # Cloud Scheduler setup (daily emails)
├── setup-firestore-prompts.js # Sync AI prompts to Firestore
├── setup-slack-secrets.js     # Configure Slack secrets in GCP
├── env.example                # Environment variable template
└── package.json
```

## Local Development

```bash
cp env.example .env            # Edit with your values
npm install
npm run dev                    # http://localhost:8080
curl http://localhost:8080/health
```

Requires GCP authentication:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project gen-lang-client-0772617718
```

## Deploy

```bash
# Windows
.\deploy-anywhere.ps1

# Linux/macOS
./deploy.sh
```

This builds a Docker image via Cloud Build and deploys to Cloud Run.

## Environment Variables

Set via `--set-env-vars` and `--set-secrets` in the deploy scripts.

| Variable | Source | Purpose |
|----------|--------|---------|
| `FIREBASE_PROJECT_ID` | env | Firebase project |
| `GCP_PROJECT_ID` | env | GCP project for Secret Manager |
| `GEMINI_SECRET_NAME` | env | Secret Manager key name for Gemini |
| `SENDGRID_FROM_EMAIL` | env | Verified sender email |
| `SLACK_FEEDBACK_CHANNEL_ID` | env | Slack channel for feedback |
| `MIN_CLIENT_VERSION` | env | Minimum client version to accept |
| `SENDGRID_API_KEY` | secret | SendGrid API key |
| `PORTKEY_API_KEY` | secret | Portkey API key (Gemini proxy) |
| `PORTKEY_VIRTUAL_KEY` | secret | Portkey virtual key |
| `SLACK_ALERTS_WEBHOOK` | secret | Slack webhook for all notifications |
| `DODO_PAYMENTS_API_KEY` | secret | Dodo Payments API key |
| `DODO_WEBHOOK_SECRET` | secret | Dodo webhook verification |
| `FRONTEND_URL` | secret | Website URL for email links |

## Key Integrations

**Slack notifications** -- Signup, trial activation, upgrades, referrals, feedback, payment, campaign status, monitoring alerts. All non-blocking (failures don't break the main flow). Uses general `SLACK_WEBHOOK` as fallback if `SLACK_SIGNUP_WEBHOOK` isn't configured.

**Email reports** -- Cloud Scheduler hits `POST /v1/reports/trigger-daily-emails` every hour. The backend checks each user's timezone and preferred send time, generates an HTML report with charts (via QuickChart.io), and sends via SendGrid.

**Payments** -- Dodo Payments webhooks at `/v1/checkout/webhook`. Handles subscription lifecycle (monthly $3, yearly $30).

## Setup Scripts

```bash
# Sync AI prompts from client/prompts/ to Firestore
node setup-firestore-prompts.js

# Configure Slack webhook secrets in GCP Secret Manager
node setup-slack-secrets.js

# Create Cloud Scheduler job for daily emails
bash setup-scheduler.sh
```
