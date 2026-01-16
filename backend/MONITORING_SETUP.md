# Monitoring & Error Tracking Setup Guide

This guide explains how to set up comprehensive monitoring, error tracking, and alerting for the Telos backend.

## Table of Contents

1. [Overview](#overview)
2. [Sentry Setup (Error Tracking)](#sentry-setup)
3. [Slack Alerts Setup](#slack-alerts-setup)
4. [Secret Manager Configuration](#secret-manager-configuration)
5. [Environment Variables](#environment-variables)
6. [Testing](#testing)
7. [Monitoring Features](#monitoring-features)

---

## Overview

The Telos backend now includes:

- **Sentry**: Error tracking and performance monitoring
- **Slack Alerts**: Real-time notifications for critical events
- **Performance Monitoring**: Automatic tracking of slow requests
- **Rate Limit Monitoring**: Alerts when users approach quotas
- **Security Event Tracking**: Notifications for suspicious activities

---

## Sentry Setup (Error Tracking)

### 1. Create Sentry Account

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project (select **Node.js/Express**)
3. Copy your **DSN** (Data Source Name)

### 2. Add DSN to Environment

#### For Local Development:

```bash
# backend/.env
SENTRY_DSN=https://your-sentry-dsn@o123456.ingest.sentry.io/7654321
SENTRY_ENVIRONMENT=development

# Optional: Send events in development
SENTRY_SEND_IN_DEV=true
```

#### For Production (Google Cloud Secret Manager):

```bash
# Add secret to Secret Manager
gcloud secrets create SENTRY_DSN \
  --data-file=- \
  --project=your-gcp-project-id \
  <<< "https://your-sentry-dsn@o123456.ingest.sentry.io/7654321"

# Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding SENTRY_DSN \
  --member="serviceAccount:your-service-account@your-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=your-gcp-project-id
```

Then update Cloud Run environment:

```bash
gcloud run services update telos-backend \
  --set-env-vars SENTRY_DSN_SECRET_NAME=SENTRY_DSN \
  --set-env-vars SENTRY_ENVIRONMENT=production \
  --region=us-central1
```

### 3. Verify Sentry Integration

**Test error tracking:**

```bash
curl -X POST http://localhost:8080/test-error
```

Check Sentry dashboard - you should see the error logged.

---

## Slack Alerts Setup

### 1. Create Slack Incoming Webhook

1. Go to [Slack API](https://api.slack.com/messaging/webhooks)
2. Click **Create New App** → **From scratch**
3. Name your app (e.g., "Telos Monitoring")
4. Select your workspace
5. Navigate to **Incoming Webhooks** and activate
6. Click **Add New Webhook to Workspace**
7. Select the channel for alerts (e.g., `#telos-alerts`)
8. Copy the webhook URL

### 2. Add Webhook to Environment

#### For Local Development:

```bash
# backend/.env
SLACK_ALERTS_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

#### For Production (Google Cloud Secret Manager):

```bash
# Add secret to Secret Manager
gcloud secrets create SLACK_ALERTS_WEBHOOK \
  --data-file=- \
  --project=your-gcp-project-id \
  <<< "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"

# Grant access
gcloud secrets add-iam-policy-binding SLACK_ALERTS_WEBHOOK \
  --member="serviceAccount:your-service-account@your-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=your-gcp-project-id
```

Update Cloud Run:

```bash
gcloud run services update telos-backend \
  --set-env-vars SLACK_ALERTS_WEBHOOK_SECRET_NAME=SLACK_ALERTS_WEBHOOK \
  --region=us-central1
```

### 3. Test Slack Alerts

Send a test alert:

```bash
curl -X POST http://localhost:8080/test-slack-alert
```

You should receive a message in your Slack channel.

---

## Secret Manager Configuration

### Required Secrets

All secrets should be stored in Google Cloud Secret Manager for production:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `SENDGRID_API_KEY` | SendGrid API key for emails | `SG.abc...` |
| `PORTKEY_API_KEY` | Portkey API key | `Aap...` |
| `PORTKEY_VIRTUAL_KEY` | Portkey virtual key | `google-virtual-...` |
| `SENTRY_DSN` | Sentry DSN for error tracking | `https://...` |
| `SLACK_ALERTS_WEBHOOK` | Slack webhook URL for alerts | `https://hooks.slack.com/...` |
| `SLACK_BOT_TOKEN` | Slack bot token (for feedback) | `xoxb-...` |
| `SLACK_WEBHOOK` | Slack webhook for feedback | `https://hooks.slack.com/...` |

### Creating Secrets

```bash
# Create a secret
gcloud secrets create SECRET_NAME \
  --data-file=- \
  --project=your-gcp-project-id \
  <<< "your-secret-value"

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@your-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=your-gcp-project-id
```

### Accessing Secrets in Code

The backend automatically retrieves secrets from Secret Manager using the `secrets.js` service:

```javascript
import { getSecret } from './services/secrets.js';

// Retrieve any secret
const apiKey = await getSecret('GEMINI_API_KEY');
```

**Priority order:**
1. Environment variable (for local dev)
2. Secret Manager (for production)

---

## Environment Variables

### Required Environment Variables

```bash
# backend/.env (for local development)

# Server Configuration
PORT=8080
NODE_ENV=development

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GEMINI_SECRET_NAME=GEMINI_API_KEY

# Portkey AI Configuration
PORTKEY_API_KEY=your-portkey-api-key
PORTKEY_VIRTUAL_KEY=your-portkey-virtual-key

# Sentry Error Tracking
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=development
SENTRY_SEND_IN_DEV=false

# Slack Alerts
SLACK_ALERTS_WEBHOOK=your-slack-webhook-url

# SendGrid Email Configuration
SENDGRID_API_KEY_SECRET_NAME=SENDGRID_API_KEY
SENDGRID_FROM_EMAIL=reports@telos.dev
SENDGRID_FROM_NAME=Telos Screen Tracker

# Dodo Payments Configuration
DODO_PAYMENTS_API_KEY=your-dodo-api-key
DODO_PRODUCT_ID_MONTHLY=pdt_your_monthly_product_id
DODO_PRODUCT_ID_YEARLY=pdt_your_yearly_product_id
DODO_WEBHOOK_SECRET=your_webhook_secret
FRONTEND_URL=https://telos.app

# Rate Limiting
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=2000

# Client Version
MIN_CLIENT_VERSION=0.1.0
```

### Cloud Run Environment Variables

For production, set environment variables via:

```bash
gcloud run services update telos-backend \
  --set-env-vars NODE_ENV=production \
  --set-env-vars SENTRY_ENVIRONMENT=production \
  --region=us-central1
```

---

## Testing

### 1. Test Sentry Integration

**Backend:**

```bash
cd backend
npm install
npm start

# Trigger a test error (you'll need to add this endpoint)
curl -X GET http://localhost:8080/test-sentry
```

Check Sentry dashboard for the error.

**Client:**

```bash
cd client
pip install -r requirements.txt
export SENTRY_DSN="your-client-sentry-dsn"
python main.py
```

### 2. Test Slack Alerts

```bash
# Test Slack webhook
curl -X POST http://localhost:8080/test-slack-alert
```

Check your Slack channel for the test alert.

### 3. Test Performance Monitoring

```bash
# Trigger a slow request
curl -X GET http://localhost:8080/v1/analyze/slow
```

You should receive:
- Slack alert about slow response time
- Sentry performance trace

### 4. Test Rate Limit Monitoring

```bash
# Spam requests to trigger rate limit
for i in {1..150}; do
  curl -X POST http://localhost:8080/v1/analyze \
    -H "Authorization: Bearer your-token"
done
```

You should receive a Slack alert when quota approaches 90%.

---

## Monitoring Features

### Automatic Monitoring

The backend automatically monitors:

| Event | Trigger | Alert Channel | Severity |
|-------|---------|--------------|----------|
| Server errors (5xx) | Any 500+ status code | Slack + Sentry | ERROR |
| Slow requests | Response time > 2s | Slack | WARNING |
| High error rate | Error rate > 5% | Slack + Sentry | ERROR |
| Rate limit exceeded | User hits quota | Slack | WARNING |
| Health check failure | /health returns error | Slack + Sentry | CRITICAL |
| High quota usage | User at 90% quota | Slack | WARNING |
| Security events | Auth failures, etc. | Slack + Sentry | ERROR |
| Deployment | App starts in production | Slack | INFO |

### Manual Monitoring

You can send custom alerts from your code:

```javascript
import { sendSlackAlert, AlertSeverity, AlertCategory } from './services/monitoring.js';

// Send custom alert
await sendSlackAlert({
  severity: AlertSeverity.WARNING,
  category: AlertCategory.BUSINESS,
  title: 'Trial Conversion Success',
  message: 'User upgraded from trial to paid plan',
  fields: [
    { title: 'User Email', value: 'user@example.com', short: true },
    { title: 'Plan', value: 'Monthly', short: true },
  ],
});
```

### Sentry Custom Tracking

```javascript
import { captureException, captureMessage, setUser } from './services/sentry.js';

// Capture exception
try {
  // risky code
} catch (error) {
  captureException(error, {
    tags: { component: 'payment' },
    extra: { userId: 'user123' },
  });
}

// Capture message
captureMessage('Payment processing started', 'info', {
  tags: { flow: 'checkout' },
});

// Set user context
setUser({ id: 'user123', email: 'user@example.com' });
```

---

## Alert Rate Limiting

To prevent alert spam, alerts are rate-limited:
- **Cooldown period**: 5 minutes per alert type
- Same alert won't be sent more than once per 5 minutes

You can clear the cache for testing:

```javascript
import { clearAlertCache } from './services/monitoring.js';
clearAlertCache();
```

---

## Dashboard Setup

### Sentry Dashboard

1. Go to [sentry.io](https://sentry.io)
2. Navigate to your project
3. View:
   - **Issues**: All errors and exceptions
   - **Performance**: Slow transactions
   - **Releases**: Track deployments

### Custom Dashboards

Set up custom monitoring dashboards:

1. **Google Cloud Monitoring**
   - Monitor Cloud Run metrics
   - Set up custom alerts
   - View logs

2. **Slack Channel**
   - Create dedicated `#telos-alerts` channel
   - Set up channel notifications
   - Pin important alerts

---

## Troubleshooting

### Sentry Not Capturing Errors

1. Check DSN is set: `echo $SENTRY_DSN`
2. Check Sentry initialization logs: Look for "✅ Sentry initialized"
3. Verify environment: `SENTRY_SEND_IN_DEV=true` for dev testing
4. Check Sentry quota: Free tier has limits

### Slack Alerts Not Sending

1. Verify webhook URL: `echo $SLACK_ALERTS_WEBHOOK`
2. Check webhook is active in Slack API dashboard
3. Review rate limiting: Clear cache if testing
4. Check logs: `[MONITORING]` prefix in console

### Secrets Not Loading

1. Verify Secret Manager permissions:
   ```bash
   gcloud secrets get-iam-policy SECRET_NAME
   ```
2. Check service account has `secretAccessor` role
3. Verify GCP_PROJECT_ID is correct
4. Check secret exists:
   ```bash
   gcloud secrets list --project=your-project-id
   ```

---

## Cost Considerations

### Sentry

- **Free tier**: 5K errors/month, 10K transactions/month
- **Team tier**: $26/month - Unlimited errors, 50K transactions

### Slack

- **Free**: Unlimited webhooks, 90-day message history
- **Pro**: $7.25/user/month - Unlimited history

### Google Cloud Secret Manager

- **Free tier**: First 6 active secrets free
- **Pricing**: $0.06 per secret/month + $0.03 per 10K access operations

**Total estimated cost for production**: ~$30-50/month (with Sentry Team)

---

## Next Steps

1. ✅ Set up Sentry project
2. ✅ Configure Slack webhook
3. ✅ Add secrets to Secret Manager
4. ✅ Update Cloud Run environment variables
5. ✅ Deploy and verify monitoring
6. ⬜ Set up Google Cloud Monitoring alerts (optional)
7. ⬜ Configure uptime monitoring (Pingdom/UptimeRobot)
8. ⬜ Create runbook for common alerts

---

## Support

For issues or questions:
- Backend monitoring: Check `backend/src/services/monitoring.js`
- Sentry integration: Check `backend/src/services/sentry.js`
- Secret management: Check `backend/src/services/secrets.js`
- GitHub Issues: [github.com/your-repo/issues](https://github.com)
