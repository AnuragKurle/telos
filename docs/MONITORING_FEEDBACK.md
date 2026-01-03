# Monitoring Feedback Submissions

## Problem Solved

Previously, the feedback endpoint would return success to users even if the Slack notification failed. This created a dangerous false positive where users thought their feedback was sent, but it never reached Slack.

## Solution

**Backend Changes (`backend/src/routes/feedback.js`):**
- Now `await`s the Slack notification instead of fire-and-forget
- Logs Slack delivery status to Firestore in the `slack_notification` field
- Returns `slack_notified: true/false` in the response

**Client Changes (all feedback screens):**
- Checks the `slack_notified` field in the response
- Shows a warning if Slack failed: "⚠️ Feedback saved but Slack notification failed"
- Users know their feedback is in Firestore even if Slack didn't work

## How to Monitor Failed Notifications

### 1. Query Firestore for Failed Slack Notifications

```javascript
// In Firebase Console > Firestore
// Query: feedback collection where slack_notification.sent == false

const failedFeedback = await firestore
  .collection('feedback')
  .where('slack_notification.sent', '==', false)
  .orderBy('created_at', 'desc')
  .get();

failedFeedback.forEach(doc => {
  const data = doc.data();
  console.log(`Failed feedback ${doc.id}:`, {
    user: data.email,
    text: data.feedback_text,
    error: data.slack_notification.error,
    timestamp: data.created_at
  });
});
```

### 2. Check Backend Logs

When Slack fails, the backend logs:
```
⚠️ Feedback {feedback_id} saved but Slack notification failed: {error}
```

Search Cloud Run logs for "Slack notification failed".

### 3. Common Slack Failure Reasons

| Error | Cause | Fix |
|-------|-------|-----|
| No credentials | `SLACK_WEBHOOK` or `SLACK_BOT_TOKEN` not in Secret Manager | Add secret to GCP Secret Manager |
| Network timeout | Slack API unreachable | Check Cloud Run egress, retry manually |
| Invalid channel | Channel ID wrong or bot not invited | Verify channel ID, invite bot to channel |
| Rate limited | Too many messages to Slack | Implement Slack rate limiting |

### 4. Manually Retry Failed Notifications

If you find failed feedback in Firestore, you can manually send to Slack:

```javascript
// In backend, create a script: scripts/retry-failed-slack.js
import { getFirestore } from '../src/config/firebase.js';
import { sendSlackNotification } from '../src/services/slack.js';

async function retryFailedNotifications() {
  const firestore = getFirestore();
  const failed = await firestore
    .collection('feedback')
    .where('slack_notification.sent', '==', false)
    .limit(10)  // Process in batches
    .get();

  for (const doc of failed.docs) {
    const data = doc.data();
    const channelId = process.env.SLACK_FEEDBACK_CHANNEL_ID || 'C0A6VF5PBUH';
    
    const message = `📝 *Feedback (Retry)* from ${data.email}\n> ${data.feedback_text}`;
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
      console.log(`✓ Retried feedback ${doc.id}`);
    } else {
      console.error(`✗ Retry failed for ${doc.id}:`, result.error);
    }
  }
}

retryFailedNotifications();
```

Run it:
```bash
cd backend
node scripts/retry-failed-slack.js
```

## Firestore Schema

Feedback documents now include:

```json
{
  "id": "abc123",
  "uid": "firebase_user_id",
  "email": "user@example.com",
  "feedback_type": "summary",
  "feedback_text": "Category should be Learning",
  "context": { "summary_id": 123, "screen": "summary" },
  "metadata": { "app_version": "0.1.0" },
  "created_at": "2026-01-03T10:00:00Z",
  "status": "pending",
  "slack_notification": {
    "sent": false,
    "method": null,
    "error": "No credentials",
    "timestamp": "2026-01-03T10:00:01Z"
  }
}
```

## Alerts to Set Up (Recommended)

1. **Cloud Monitoring Alert:**
   - Metric: Log entries matching "Slack notification failed"
   - Threshold: > 5 in 1 hour
   - Action: Email/SMS notification

2. **Firestore Trigger (Firebase Functions):**
   ```javascript
   // Trigger on new feedback with slack_notification.sent == false
   exports.alertOnSlackFailure = functions.firestore
     .document('feedback/{feedbackId}')
     .onCreate(async (snap, context) => {
       const data = snap.data();
       if (!data.slack_notification?.sent) {
         // Send email to admin or log to monitoring service
       }
     });
   ```

## Testing Slack Integration

Before deploying, test Slack integration:

```bash
# 1. Check secrets are configured
cd backend
node -e "
  import { getSlackWebhook, getSlackBotToken } from './src/services/secrets.js';
  const webhook = await getSlackWebhook();
  const token = await getSlackBotToken();
  console.log('Webhook:', webhook ? 'Configured' : 'Missing');
  console.log('Bot Token:', token ? 'Configured' : 'Missing');
"

# 2. Test feedback endpoint locally
curl -X POST http://localhost:8080/v1/feedback \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback_type": "general",
    "feedback_text": "Test feedback",
    "context": {"screen": "test"}
  }'

# 3. Check Slack channel for message

# 4. Check response for slack_notified field
# Should return: {"success": true, "slack_notified": true, ...}
```

## Summary

✅ **No more silent failures** - Users are warned if Slack fails  
✅ **Feedback is never lost** - Always saved to Firestore first  
✅ **Trackable** - Query Firestore for failed notifications  
✅ **Retryable** - Can manually retry failed Slack messages  
✅ **Transparent** - Users know when something goes wrong  

