# Slack Notification Setup

## Prerequisites

1. **Upgrade to Blaze Plan** (if not already):
   - Cloud Functions making external network requests require the Blaze (pay-as-you-go) plan
   - Go to: https://console.firebase.google.com/project/gen-lang-client-0772617718/usage/details
   - Upgrade if needed (you'll only pay for actual usage)

2. **Wait 5-10 minutes** after enabling Eventarc API (if this is your first time using 2nd gen functions)

## Setup Options

### Option 1: Using Slack Bot Token (Recommended)

1. Create a Slack App:
   - Go to: https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "Telos Waitlist Notifier"
   - Workspace: Select your workspace

2. Add Bot Token Scopes:
   - Go to "OAuth & Permissions"
   - Add Bot Token Scopes: `chat:write`
   - Install to Workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. Invite Bot to Channel:
   - Go to your Slack channel `C0A6L5K9Z0U`
   - Type: `/invite @YourBotName`

4. Set Secret:
   ```bash
   cd website
   firebase functions:secrets:set SLACK_TOKEN
   # Paste your Bot Token when prompted
   ```

### Option 2: Using Slack Webhook (Simpler)

1. Create Incoming Webhook:
   - Go to: https://api.slack.com/apps
   - Create/Select your app
   - Go to "Incoming Webhooks" → Activate
   - Click "Add New Webhook to Workspace"
   - Select channel `C0A6L5K9Z0U`
   - Copy the Webhook URL

2. Set Secret:
   ```bash
   cd website
   firebase functions:secrets:set SLACK_WEBHOOK
   # Paste your Webhook URL when prompted
   ```

## Deploy

After setting the secret, deploy:

```bash
cd website
firebase deploy --only functions
```

## Test

1. Submit an email on the landing page
2. Check your Slack channel `C0A6L5K9Z0U` for the notification

## Troubleshooting

- **Permission errors**: Wait 5-10 minutes after first deployment, then retry
- **Function not triggering**: Check Firestore rules allow writes to `waitlist/{email}`
- **No Slack message**: Check function logs: `firebase functions:log`

