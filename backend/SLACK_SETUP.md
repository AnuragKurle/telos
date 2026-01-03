# Slack Integration Setup

## Overview

Slack webhooks are stored in **GCP Secret Manager**, not in the GitHub repo. This keeps your credentials secure and out of version control.

## Quick Setup

### Step 1: Get Your Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Select your app (or create a new one)
3. Navigate to **"Incoming Webhooks"**
4. Enable webhooks
5. Click **"Add New Webhook to Workspace"**
6. Select the channel for feedback notifications
7. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### Step 2: Run Setup Script

```bash
cd backend
node setup-slack-secrets.js setup
```

This interactive wizard will:
- ✅ Create secrets in GCP Secret Manager
- ✅ Store your webhook URL securely
- ✅ Show you commands to grant Cloud Run access

### Step 3: Grant Cloud Run Access

Run the commands shown by the setup wizard, for example:

```bash
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:gen-lang-client-0772617718@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 4: Deploy Backend

```bash
cd backend
.\deploy-anywhere.ps1  # Windows
# or
./deploy.sh            # Linux/Mac
```

### Step 5: Test It Works

```bash
cd backend
node setup-slack-secrets.js test
```

This sends a test message to your Slack channel.

## Manual Setup (Alternative)

If you prefer to set up secrets manually:

```bash
# Create the secret
echo -n "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" | \
  gcloud secrets create SLACK_WEBHOOK --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:gen-lang-client-0772617718@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Verify Configuration

Check if secrets are configured:

```bash
cd backend
node setup-slack-secrets.js check
```

**Expected output:**
```
✓ SLACK_WEBHOOK exists: https://hooks.slack...
✓ Backend can access SLACK_WEBHOOK
✅ Slack integration is configured
✅ Feedback notifications will work
```

## Environment Variables (For Local Dev)

For local development, you can use environment variables instead of Secret Manager:

```bash
# .env (DO NOT COMMIT THIS FILE)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH
```

Add `.env` to `.gitignore` to prevent accidentally committing it.

## Two Options for Slack Integration

### Option 1: Webhook URL (Recommended)

**Pros:**
- ✅ Easier to set up
- ✅ No need to manage bot permissions
- ✅ Works immediately

**Setup:**
- Store in secret: `SLACK_WEBHOOK`

### Option 2: Bot Token (Advanced)

**Pros:**
- ✅ More flexibility (can post to any channel)
- ✅ Can use advanced Slack features

**Cons:**
- ❌ Requires managing OAuth scopes
- ❌ Need to invite bot to channels

**Setup:**
1. Get bot token from https://api.slack.com/apps → OAuth & Permissions
2. Store in secret: `SLACK_BOT_TOKEN`
3. Invite bot to channel: `/invite @YourBotName`

## Secrets Used

| Secret Name | Purpose | Required? |
|-------------|---------|-----------|
| `SLACK_WEBHOOK` | Feedback notifications webhook | Yes (or SLACK_BOT_TOKEN) |
| `SLACK_BOT_TOKEN` | Alternative to webhook | No |
| `SLACK_SIGNUP_WEBHOOK` | User signup notifications | No |

**You need at least ONE of:**
- `SLACK_WEBHOOK` (recommended)
- `SLACK_BOT_TOKEN`

## How Backend Loads Secrets

The backend automatically tries to load secrets in this order:

1. **GCP Secret Manager** (production)
   - Looks for secret named `SLACK_WEBHOOK` or `SLACK_BOT_TOKEN`
   - Uses `@google-cloud/secret-manager` client

2. **Environment Variables** (local dev fallback)
   - `process.env.SLACK_WEBHOOK`
   - `process.env.SLACK_BOT_TOKEN`

3. **Returns null** if not found
   - Feedback is still saved to Firestore
   - User is warned that Slack failed
   - You can query Firestore for missed feedback

See `backend/src/services/secrets.js` for implementation.

## Channel Configuration

Set the channel ID for feedback notifications:

```bash
# In Cloud Run environment variables
SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH
```

To find your channel ID:
1. Open Slack in browser
2. Navigate to the channel
3. Check the URL: `...slack.com/archives/C0A6VF5PBUH`
4. The last part is your channel ID

## Troubleshooting

### "Secret not found"

**Cause:** Secret doesn't exist in Secret Manager

**Fix:**
```bash
node setup-slack-secrets.js setup
```

### "Permission denied"

**Cause:** Cloud Run service account doesn't have access

**Fix:**
```bash
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:YOUR-PROJECT@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### "channel_not_found"

**Cause:** Bot not invited to channel (if using bot token)

**Fix:**
1. Go to the Slack channel
2. Type: `/invite @YourBotName`

### Test message works but feedback doesn't

**Cause:** Different environment (local vs production)

**Fix:**
1. Check Cloud Run has secrets access
2. Verify Cloud Run environment variables
3. Check Cloud Run logs for errors

## Security Best Practices

✅ **DO:**
- Store webhooks in Secret Manager
- Add `.env` to `.gitignore`
- Rotate webhooks if compromised
- Use separate webhooks for dev/prod

❌ **DON'T:**
- Commit webhook URLs to Git
- Share webhook URLs publicly
- Use same webhook for multiple projects
- Store webhooks in code comments

## Monitoring

Check if Slack notifications are failing:

```bash
# Query Firestore for failed notifications
cd backend
node -e "
import { getFirestore } from './src/config/firebase.js';

const firestore = getFirestore();
const failed = await firestore
  .collection('feedback')
  .where('slack_notification.sent', '==', false)
  .get();

console.log(\`Failed notifications: \${failed.size}\`);
"
```

See `docs/MONITORING_FEEDBACK.md` for more details.

## References

- **Setup Script:** `backend/setup-slack-secrets.js`
- **Secrets Service:** `backend/src/services/secrets.js`
- **Slack Service:** `backend/src/services/slack.js`
- **Monitoring Guide:** `docs/MONITORING_FEEDBACK.md`
- **Slack API Docs:** https://api.slack.com/messaging/webhooks

