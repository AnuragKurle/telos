# Email Report System - Setup Guide

## Overview

The backend email report system is now implemented! This guide will walk you through the final setup steps to get daily email reports working.

## ✅ What's Been Completed

### Backend Code
- ✅ **Email Service** ([`src/services/email.js`](file:///d:/Experiments/screentracker/backend/src/services/email.js))
  - SendGrid integration with HTML email templates
  - Timezone-aware scheduling logic
  - Batch email sending function
  
- ✅ **API Endpoints** ([`src/routes/reports.js`](file:///d:/Experiments/screentracker/backend/src/routes/reports.js))
  - `POST /v1/reports/daily-summary` - Upload summaries from client
  - `GET /v1/reports/daily-summary/:date` - Retrieve summaries
  - `PUT /v1/reports/email-preferences` - Update user preferences
  - `GET /v1/reports/email-preferences` - Get user preferences
  
- ✅ **Scheduler Updates** ([`src/services/scheduler.js`](file:///d:/Experiments/screentracker/backend/src/services/scheduler.js))
  - Now runs hourly to check for emails to send
  - Timezone-aware delivery
  
- ✅ **Dependencies**
  - `@sendgrid/mail` package installed
  - Routes registered in server

---

## 🚀 Setup Steps

### Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Sign up for a free account (100 emails/day)
3. Verify your email address

### Step 2: Verify Sender Identity

**Option A: Single Sender Verification** (Easiest for testing)
1. In SendGrid dashboard, go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in details:
   - **From Name**: Telos Screen Tracker
   - **From Email**: your-email@gmail.com (or whatever you want to use)
   - **Company Address**: Your address
4. Verify the email SendGrid sends you

**Option B: Domain Authentication** (Better for production)
1. Go to **Settings** → **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Follow DNS setup instructions for your domain
4. Use `reports@yourdomain.com` as sender

### Step 3: Generate API Key

1. In SendGrid, go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Name it: `Telos Backend`
4. Select **Full Access** (or at minimum **Mail Send** permission)
5. Click **Create & View**
6. **COPY THE API KEY** - you'll only see it once!

### Step 4: Store API Key in GCP Secret Manager

```bash
# Navigate to backend directory
cd d:\Experiments\screentracker\backend

# Create secret in GCP Secret Manager
gcloud secrets create SENDGRID_API_KEY \
  --replication-policy="automatic" \
  --data-file=-

# Paste your SendGrid API key when prompted, then press Enter and Ctrl+D
```

Alternatively, use GCP Console:
1. Go to https://console.cloud.google.com/security/secret-manager
2. Click **CREATE SECRET**
3. Name: `SENDGRID_API_KEY`
4. Secret value: paste your SendGrid API key
5. Click **CREATE**

### Step 5: Update Environment Variables

Update your `.env` file (or create it from `env.example`):

```env
# Copy env.example if you don't have .env yet
# Then add/update these lines:

SENDGRID_API_KEY_SECRET_NAME=SENDGRID_API_KEY
SENDGRID_FROM_EMAIL=your-verified-email@example.com
SENDGRID_FROM_NAME=Telos Screen Tracker
```

### Step 6: Test Email Service

Create a test script:

```bash
# Create test file
cd d:\Experiments\screentracker\backend
```

Create `test-email.js`:
```javascript
import dotenv from 'dotenv';
import { initializeFirebase } from './src/config/firebase.js';
import { sendDailyReport } from './src/services/email.js';

dotenv.config();
initializeFirebase();

const testSummary = {
  date: '2026-01-08',
  work_seconds: 5400,
  learning_seconds: 360,
  browsing_seconds: 3600,
  entertainment_seconds: 1800,
  productivity_score: 75,
  daily_narrative: 'Test narrative: You had a productive day with balanced work and learning time.',
  key_learnings_json: '["Learned SendGrid integration", "Set up email service"]',
  context_switches: 5
};

sendDailyReport('YOUR_EMAIL@example.com', testSummary)
  .then(result => {
    console.log('Test result:', result);
    process.exit(result.success ? 0 : 1);
  })
  .catch(err => {
    console.error('Test failed:', err);
    process.exit(1);
  });
```

Run the test:
```bash
node test-email.js
```

Check your inbox! You should receive a beautiful daily report email.

---

## 📊 Firestore Collections Setup

The system expects these collections in Firestore:

### Collection: `users`
Already exists from auth system. Will be extended with:
```javascript
{
  // Document ID = user email
  email: "user@example.com",
  uid: "firebase-uid",
  emailReports: {
    enabled: true,           // Default: true for all users
    sendTime: "09:00",      // User's preferred time (HH:MM)
    timezone: "UTC",        // User's timezone
    frequency: "daily",     // "daily" (weekly/monthly later)
    updatedAt: Timestamp
  },
  // ... existing fields (trial, accessStatus, etc.)
}
```

### Collection: `daily_summaries` (NEW)
Will be created automatically when clients upload summaries:
```javascript
{
  userId: "firebase-uid",
  userEmail: "user@example.com",
  date: "2026-01-08",         // YYYY-MM-DD format
  uploadedAt: Timestamp,
  emailSent: false,           // Set to true after sending
  emailSentAt: null,          // Timestamp when sent
  summary: {
    work_seconds: 5460,
    learning_seconds: 360,
    // ... all summary data
  }
}
```

**No manual setup needed** - collections will be created on first write.

---

## 🔧 Next Steps: Client Integration

Now that the backend is ready, you need to integrate the client to upload summaries.

### Add Backend Client Methods

I'll create these for you in the next phase:

1. **Upload Function** in [`client/core/backend_client.py`](file:///d:/Experiments/screentracker/client/core/backend_client.py)
   ```python
   def upload_daily_summary(date, summary)
   def update_email_preferences(enabled, sendTime, timezone)
   def get_email_preferences()
   ```

2. **Auto-upload** in [`client/core/daily_aggregator.py`](file:///d:/Experiments/screentracker/client/core/daily_aggregator.py)
   - After generating summary, upload to backend

3. **Settings UI** in [`client/tui/screens/settings.py`](file:///d:/Experiments/screentracker/client/tui/screens/settings.py)
   - Email preferences toggle
   - Time picker
   - Timezone selector

---

## 🧪 Testing Checklist

Before rolling out to all users:

- [ ] SendGrid account created and verified
- [ ] API key stored in GCP Secret Manager
- [ ] Environment variables configured
- [ ] Test email sent successfully
- [ ] Backend deployed with new code
- [ ] Scheduler running (check logs every hour)
- [ ] Client integration complete
- [ ] Test full flow: generate → upload → receive email
- [ ] Test with your account for 1-2 days
- [ ] Set email preferences for beta users

---

## 🐛 Troubleshooting

### Email not sending
1. Check backend logs:
   ```bash
   # If running locally
   npm run dev
   
   # If deployed to Cloud Run
   gcloud logging read "resource.type=cloud_run_revision" --limit 50
   ```

2. Look for `[EMAIL]` log messages
3. Common issues:
   - SendGrid API key not found → Check Secret Manager
   - Sender not verified → Verify in SendGrid
   - Wrong timezone → Check user preferences

### Email goes to spam
- Add SPF/DKIM records (SendGrid domain authentication)
- Ask users to mark as "Not Spam"
- Use verified domain instead of Gmail

### Scheduler not running
- Check if backend started successfully
- Look for `[SCHEDULER] Started hourly job runner` in logs
- Verify `runDailyJobs()` is being called every hour

---

## 📈 Monitoring

### Key Metrics to Track

```javascript
// Add to scheduler for logging
console.log('[EMAIL] Daily stats:', {
  usersEnabled: totalUsers,
  emailsSent: sentCount,
  emailsFailed: errorCount,
  deliveryRate: (sentCount / (sentCount + errorCount)) * 100
});
```

### Firestore Queries

Check sent emails:
```javascript
db.collection('daily_summaries')
  .where('emailSent', '==', true)
  .where('date', '==', yesterday)
  .get();
```

Check pending emails:
```javascript
db.collection('daily_summaries')
  .where('emailSent', '==', false)
  .get();
```

---

## Cost Tracking

**Current Setup (100 users)**:
- SendGrid: $0/month (free tier)
- GCP Cloud Run: ~$0 (within free tier)
- Firestore: ~$0 (within free tier)
- **Total: $0/month**

**At Scale (1000 users)**:
- SendGrid: $15/month (Pro plan, 40K emails)
- GCP: Still within free tier
- **Total: ~$15/month**

---

## 🎉 Deployment

### Local Testing
```bash
cd d:\Experiments\screentracker\backend
npm run dev
```

### Deploy to Cloud Run
```bash
# Your existing deployment script
.\deploy.ps1

# Or manual
gcloud run deploy telos-backend \
  --source . \
  --platform managed \
  --region us-central1
```

---

## Ready to Proceed?

Once you've completed Steps 1-6 above, test the email sending, and confirm it works, we can move on to:

1. **Client Integration** - Upload summaries from desktop app
2. **Settings UI** - Let users configure email preferences
3. **Testing** - Full end-to-end test
4. **Rollout** - Enable for all beta users

Let me know when you're ready for the next phase!
