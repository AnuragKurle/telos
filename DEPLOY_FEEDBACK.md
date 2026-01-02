# Deploy Feedback Feature to Cloud Run

The feedback feature is implemented but needs to be deployed to your Cloud Run backend.

## What's Been Added:

### Backend:
- ✅ `/v1/feedback` endpoint in `backend/src/routes/feedback.js`
- ✅ Slack notification service in `backend/src/services/slack.js`
- ✅ Slack secret helpers in `backend/src/services/secrets.js`
- ✅ Route registered in `backend/src/server.js`

### Frontend:
- ✅ Feedback modal on all screens (F key)
- ✅ Backend client method `submit_feedback()`
- ✅ Screen tracking in all feedback submissions

## Deployment Steps:

### 1. Install Dependencies
```bash
cd backend
npm install
```

### 2. Add Slack Credentials to Secret Manager

**Option A: Using Slack Bot Token (Recommended)**
```bash
# Create the secret
echo -n "xoxb-YOUR-SLACK-BOT-TOKEN" | gcloud secrets create SLACK_BOT_TOKEN \
    --data-file=- \
    --project=YOUR_PROJECT_ID

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding SLACK_BOT_TOKEN \
    --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID
```

**Option B: Using Slack Webhook (Simpler)**
```bash
# Create the secret
echo -n "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" | gcloud secrets create SLACK_WEBHOOK \
    --data-file=- \
    --project=YOUR_PROJECT_ID

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
    --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID
```

### 3. Set Environment Variable (Optional)

If you want to override the default channel ID:
```bash
gcloud run services update telos-backend \
    --update-env-vars SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID
```

### 4. Deploy to Cloud Run

```bash
cd backend
gcloud run deploy telos-backend \
    --source . \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --allow-unauthenticated
```

### 5. Test the Endpoint

After deployment:
```bash
# Get your backend URL
gcloud run services describe telos-backend --region YOUR_REGION --format='value(status.url)'

# Test health check
curl https://YOUR-BACKEND-URL/health

# The /v1/feedback endpoint should now be available (requires auth)
```

## How It Works:

1. **User presses F** → Opens feedback modal
2. **User types feedback** → Submits to `/v1/feedback`
3. **Backend receives feedback** → Saves to Firestore collection `feedback`
4. **Backend sends Slack alert** → Posts to channel `C0A6VF5PBUH`
5. **User gets confirmation** → "✓ Feedback submitted successfully!"

## Firestore Structure:

```javascript
feedback/{feedback_id} {
  id: "abc123",
  uid: "firebase_user_id",
  email: "user@example.com",
  feedback_type: "summary" | "session" | "capture" | "chat" | "general",
  feedback_text: "Category should be Learning not Browsing",
  context: {
    screen: "dashboard",
    app: "VSCode",
    task: "Coding Python",
    category: "work",
    // ... other context based on feedback type
  },
  metadata: {
    screen: "dashboard",
    app_version: "0.1.0"
  },
  created_at: Timestamp,
  status: "pending"
}
```

## Slack Message Format:

```
📝 *New Feedback Received* (from dashboard screen)
> *Type:* capture
> *User:* user@example.com (uid123)
> *Feedback:* Category should be Learning not Browsing

*App:* VSCode  *Task:* Coding Python  *Category:* work
```

## Troubleshooting:

### "404 Cannot POST /v1/feedback"
- Backend not deployed yet → Run step 4 above

### "Failed to submit feedback: Network error"
- Check backend URL in client config
- Verify backend is healthy: `curl https://YOUR-BACKEND-URL/health`

### No Slack notification received
- Check Secret Manager has SLACK_BOT_TOKEN or SLACK_WEBHOOK
- Verify Cloud Run service account has secretAccessor role
- Check backend logs: `gcloud run logs read telos-backend --region YOUR_REGION`

### "Authentication failed"
- Ensure Firebase Auth is properly configured
- Check client has valid Firebase token

## Cost Estimate:

- **Firestore**: ~$0.001 per feedback submission (write + read)
- **Cloud Run**: Minimal (few milliseconds per request)
- **Secret Manager**: ~$0.06/month per secret
- **Slack API**: Free

**Estimated cost for 1000 feedbacks/month: < $1**

