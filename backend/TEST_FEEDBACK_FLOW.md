# Testing Feedback Flow End-to-End

## Prerequisites

Before testing, ensure:

1. **Slack integration is configured** (one of these):
   - `SLACK_WEBHOOK` secret in GCP Secret Manager
   - `SLACK_BOT_TOKEN` secret in GCP Secret Manager
   - Or environment variables `SLACK_WEBHOOK` / `SLACK_BOT_TOKEN`

2. **Backend is deployed** to Cloud Run:
   ```bash
   cd backend
   .\deploy-anywhere.ps1  # Windows
   # or
   ./deploy.sh            # Linux/Mac
   ```

3. **Slack channel ID** is set:
   ```bash
   # In Cloud Run environment variables or .env
   SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH
   ```

## Test 1: Check Slack Secrets

```bash
cd backend

# Check if secrets are accessible
node -e "
import { getSlackWebhook, getSlackBotToken } from './src/services/secrets.js';

(async () => {
  try {
    const webhook = await getSlackWebhook();
    const token = await getSlackBotToken();
    
    console.log('Webhook:', webhook ? '✓ Configured' : '✗ Missing');
    console.log('Bot Token:', token ? '✓ Configured' : '✗ Missing');
    
    if (!webhook && !token) {
      console.error('\n⚠️ No Slack credentials found! Set up secrets first.');
      process.exit(1);
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
})();
"
```

**Expected:** At least one should show "✓ Configured"

## Test 2: Manual API Test (Local)

Start backend locally:

```bash
cd backend
npm run dev
```

Get a Firebase token from the client:

```bash
# In client directory
cd client
python -c "
from core.firebase_auth import FirebaseAuth
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

auth = FirebaseAuth(config['firebase']['api_key'])
token = auth.get_token()
print(f'Token: {token[:50]}...')
" > token.txt

# Use token in cURL
TOKEN=$(cat token.txt | grep Token | cut -d' ' -f2)

curl -X POST http://localhost:8080/v1/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Client-Version: 0.1.0" \
  -d '{
    "feedback_type": "general",
    "feedback_text": "Test feedback from local backend",
    "context": {"screen": "test"},
    "metadata": {"app_version": "0.1.0"}
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback_id": "abc123...",
  "slack_notified": true
}
```

**Check:**
1. ✅ Response shows `"slack_notified": true`
2. ✅ Message appears in Slack channel
3. ✅ Firestore has document in `feedback` collection with `slack_notification.sent = true`

## Test 3: Slack Failure Simulation

Temporarily break Slack by using invalid webhook URL:

```bash
# Set environment variable to invalid URL
export SLACK_WEBHOOK="https://hooks.slack.com/invalid"

# Restart backend
npm run dev

# Submit feedback again (same cURL as above)
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback_id": "abc123...",
  "slack_notified": false
}
```

**Check:**
1. ✅ Response shows `"slack_notified": false`
2. ✅ Backend logs show: `⚠️ Feedback abc123... saved but Slack notification failed: ...`
3. ✅ Firestore has document with `slack_notification.sent = false` and `slack_notification.error = "..."`

## Test 4: Client Integration Test

Test from the actual client app:

```bash
cd client
python main.py
```

**Steps:**
1. Navigate to Settings screen (press `4`)
2. Press `F2` to submit feedback
3. Enter test feedback: "Testing Slack integration"
4. Submit

**Check Client UI:**
- If Slack works: "✓ Feedback submitted successfully!"
- If Slack fails: "⚠️ Feedback saved but Slack notification failed. Dev will check Firestore."

**Check Slack Channel:**
- Look for message with:
  ```
  📝 *New Feedback Received* (from settings screen)
  > *Type:* general
  > *User:* anonymous (uid123...)
  > *Feedback:* Testing Slack integration
  ```

## Test 5: Production Test

After deploying to Cloud Run:

```bash
# Get production URL
BACKEND_URL="https://telos-backend-ae7k4avtpq-el.a.run.app"

# Test feedback endpoint
curl -X POST $BACKEND_URL/v1/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Client-Version: 0.1.0" \
  -d '{
    "feedback_type": "general",
    "feedback_text": "Production test",
    "context": {"screen": "test"}
  }'
```

**Check Cloud Run Logs:**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telos-backend" \
  --limit 20 --format json | grep -i feedback
```

Look for:
- ✅ `Retrieved secret: SLACK_WEBHOOK` or `SLACK_BOT_TOKEN`
- ✅ No errors matching `Slack notification failed`
- ⚠️ If you see `Slack notification failed`, check the error message

## Test 6: Monitor Firestore

Check Firestore for feedback documents:

1. Go to Firebase Console: https://console.firebase.google.com/project/gen-lang-client-0772617718/firestore
2. Navigate to `feedback` collection
3. Find your test documents

**Check each document:**

```javascript
{
  "feedback_text": "Test feedback from local backend",
  "feedback_type": "general",
  "uid": "...",
  "email": "anonymous",
  "context": {"screen": "test"},
  "metadata": {"app_version": "0.1.0"},
  "created_at": "2026-01-03T...",
  "status": "pending",
  
  // THIS IS THE KEY PART:
  "slack_notification": {
    "sent": true,              // Should be true if Slack worked
    "method": "webhook",       // or "bot_token"
    "error": null,             // or error message if failed
    "timestamp": "2026-01-03T..."
  }
}
```

## Test 7: Query Failed Notifications

Query Firestore for any failed Slack notifications:

```javascript
// In Firebase Console > Firestore > Run Query
// Or use Node.js:

import { getFirestore } from './src/config/firebase.js';

const firestore = getFirestore();
const failed = await firestore
  .collection('feedback')
  .where('slack_notification.sent', '==', false)
  .get();

console.log(`Found ${failed.size} failed Slack notifications:`);

failed.forEach(doc => {
  const data = doc.data();
  console.log({
    id: doc.id,
    text: data.feedback_text,
    error: data.slack_notification.error,
    time: data.created_at
  });
});
```

**If you find failed notifications:**
- Check the error message in `slack_notification.error`
- Common errors:
  - `"No credentials"` → Set up SLACK_WEBHOOK or SLACK_BOT_TOKEN secret
  - `"timeout of 5000ms exceeded"` → Network issue, retry manually
  - `"channel_not_found"` → Check SLACK_FEEDBACK_CHANNEL_ID

## Test 8: Retry Failed Notifications

If you have failed notifications, retry them:

```bash
cd backend
node -e "
import { getFirestore } from './src/config/firebase.js';
import { sendSlackNotification } from './src/services/slack.js';

(async () => {
  const firestore = getFirestore();
  const failed = await firestore
    .collection('feedback')
    .where('slack_notification.sent', '==', false)
    .limit(5)
    .get();

  console.log(\`Retrying \${failed.size} failed notifications...\`);

  for (const doc of failed.docs) {
    const data = doc.data();
    const channelId = process.env.SLACK_FEEDBACK_CHANNEL_ID || 'C0A6VF5PBUH';
    
    const message = \`📝 *Feedback (Retry)* from \${data.email}\\n> \${data.feedback_text}\`;
    const blocks = [
      {
        type: 'section',
        text: { type: 'mrkdwn', text: message }
      }
    ];

    const result = await sendSlackNotification(channelId, message, blocks);
    
    if (result.success) {
      await doc.ref.update({
        'slack_notification.sent': true,
        'slack_notification.retried_at': new Date()
      });
      console.log(\`✓ Retried \${doc.id}\`);
    } else {
      console.error(\`✗ Retry failed for \${doc.id}:\`, result.error);
    }
  }
})();
"
```

## Checklist Summary

Before considering testing complete:

- [ ] Slack secrets are configured (webhook or bot token)
- [ ] Local backend test shows `slack_notified: true`
- [ ] Message appears in Slack channel
- [ ] Firestore document has `slack_notification.sent = true`
- [ ] Simulated failure shows `slack_notified: false`
- [ ] Client shows warning when Slack fails
- [ ] Production backend test succeeds
- [ ] Cloud Run logs show no Slack errors
- [ ] No failed notifications in Firestore query

## Troubleshooting

### Problem: `slack_notified: false` even with correct secrets

**Check:**
1. Secret Manager permissions for Cloud Run service account
2. Secret names match (default: `SLACK_WEBHOOK` or `SLACK_BOT_TOKEN`)
3. Environment variable `GCP_PROJECT_ID` is set

### Problem: Slack message doesn't appear

**Check:**
1. Channel ID is correct (`SLACK_FEEDBACK_CHANNEL_ID`)
2. Bot is invited to the channel (if using bot token)
3. Webhook URL is not expired

### Problem: Client doesn't show warning

**Check:**
1. Client is running latest code with `slack_notified` check
2. Backend response includes `slack_notified` field
3. Client version >= 0.1.1

## Documentation

For monitoring ongoing feedback failures, see:
- `docs/MONITORING_FEEDBACK.md`

