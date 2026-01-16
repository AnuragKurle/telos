# Beta Launch - Next Steps

## What Was Done

### Security
- ✅ Removed hardcoded Portkey API keys from `gemini.js`
- ✅ Now requires environment variables (will fail if not set)

### Error Tracking (Sentry)
- ✅ Backend: Added `@sentry/node` + integration in `server.js`
- ✅ Client: Added `sentry-sdk` + integration in `main.py`
- ✅ Captures all unhandled errors, performance traces, breadcrumbs

### Monitoring & Alerts (Slack)
- ✅ Created `monitoring.js` service with Slack webhooks
- ✅ Automatic alerts for: errors, slow requests, rate limits, security events
- ✅ Performance monitoring middleware on all endpoints
- ✅ Rate-limited alerts (5-min cooldown to prevent spam)

### Documentation
- ✅ `MONITORING_SETUP.md` - Full setup guide
- ✅ Updated `env.example` with all required variables

---

## Next Steps (30-40 minutes total)

### 1. Install Dependencies (2 min)
```bash
cd backend
npm install
```

### 2. Set Up Sentry (5 min)
1. Sign up at [sentry.io](https://sentry.io)
2. Create project: **Node.js/Express** (backend)
3. Copy DSN → Add to `backend/.env`:
```bash
SENTRY_DSN=https://xxx@sentry.io/123456
SENTRY_ENVIRONMENT=production
```

### 3. Set Up Slack Webhook (5 min)
1. Go to [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks)
2. Create app → Incoming Webhooks → Add to channel
3. Copy webhook URL → Add to `backend/.env`:
```bash
SLACK_ALERTS_WEBHOOK=https://hooks.slack.com/services/T.../B.../XXX
```

### 4. Add Required Environment Variables (2 min)
Add to `backend/.env`:
```bash
PORTKEY_API_KEY=your-portkey-api-key
PORTKEY_VIRTUAL_KEY=your-portkey-virtual-key
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
SLACK_ALERTS_WEBHOOK=your-slack-webhook
```

### 5. Add Secrets to Google Cloud Secret Manager (10 min)
```bash
# Navigate to backend
cd backend

# Create secrets (replace values)
echo "your-portkey-api-key" | gcloud secrets create PORTKEY_API_KEY --data-file=-
echo "your-portkey-virtual-key" | gcloud secrets create PORTKEY_VIRTUAL_KEY --data-file=-
echo "your-sentry-dsn" | gcloud secrets create SENTRY_DSN --data-file=-
echo "your-slack-webhook" | gcloud secrets create SLACK_ALERTS_WEBHOOK --data-file=-

# Grant access to Cloud Run service account
SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT@your-project.iam.gserviceaccount.com"
for secret in PORTKEY_API_KEY PORTKEY_VIRTUAL_KEY SENTRY_DSN SLACK_ALERTS_WEBHOOK; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 6. Test Locally (5 min)
```bash
cd backend
npm start

# Should see:
# ✅ Sentry initialized successfully
# 🚀 Telos Backend running on port 8080

# Test health endpoint
curl http://localhost:8080/health
```

### 7. Deploy to Production (10 min)
```bash
cd backend

# Update Cloud Run environment
gcloud run services update telos-backend \
  --set-env-vars NODE_ENV=production,SENTRY_ENVIRONMENT=production \
  --region=us-central1

# Deploy
gcloud run deploy telos-backend \
  --source . \
  --region=us-central1

# You should get Slack alert: "Deployment Successful"
```

---

## What You'll Get

- **Sentry**: Real-time error tracking with stack traces, performance monitoring
- **Slack Alerts**: Instant notifications for errors, slow requests, security events
- **Monitoring**: Automatic tracking of response times, error rates, quota usage

## Files Changed

### Backend
- `src/services/gemini.js` - Removed hardcoded keys
- `src/services/sentry.js` - New error tracking service
- `src/services/monitoring.js` - New monitoring/alerts service
- `src/server.js` - Added Sentry + monitoring middleware
- `src/middleware/rateLimit.js` - Added quota monitoring
- `package.json` - Added Sentry dependencies
- `env.example` - Added new required variables

### Client
- `requirements.txt` - Added sentry-sdk
- `utils/sentry_utils.py` - New error tracking utilities
- `main.py` - Added Sentry initialization

### Documentation
- `MONITORING_SETUP.md` - Complete setup guide
- `BETA_LAUNCH_NEXT_STEPS.md` - This file

---

## Cost: FREE for beta
- Sentry Free: 5K errors/month
- Slack: Free webhooks
- Secret Manager: ~$0.36/month

---

## Ready for Beta Launch ✨
After completing these steps, you'll have production-grade monitoring and error tracking.
