# Deploy Feedback Feature - Quick Guide

Your Slack webhook is ready! Follow these steps to deploy:

## Option 1: Using Google Cloud Shell (Recommended - Easiest!)

1. Go to: https://console.cloud.google.com/
2. Click the **"Activate Cloud Shell"** button (top right, terminal icon)
3. Wait for Cloud Shell to load (~10 seconds)
4. Run these commands one by one:

```bash
# Clone your repo or upload backend folder
# If you have it in GitHub:
# git clone YOUR_REPO_URL
# cd screentracker/backend

# OR upload the backend folder using the "Upload File" button in Cloud Shell

# Navigate to backend folder
cd backend

# Install dependencies
npm install

# Create Slack webhook secret
echo "https://hooks.slack.com/services/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" | \
gcloud secrets create SLACK_WEBHOOK \
  --data-file=- \
  --project=gen-lang-client-0772617718

# Grant access (replace PROJECT_NUMBER with your actual number)
PROJECT_NUMBER=$(gcloud projects describe gen-lang-client-0772617718 --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0772617718

# Deploy!
gcloud run deploy telos-backend \
  --source . \
  --region us-central1 \
  --project gen-lang-client-0772617718 \
  --allow-unauthenticated \
  --set-env-vars "FIREBASE_PROJECT_ID=gen-lang-client-0772617718,GCP_PROJECT_ID=gen-lang-client-0772617718,GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH,NODE_ENV=production"
```

## Option 2: Using Local Terminal (If gcloud is installed)

Open **Git Bash** or **WSL** and run:

```bash
cd /d/Experiments/screentracker/backend

# Create secret
echo "https://hooks.slack.com/services/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" | \
gcloud secrets create SLACK_WEBHOOK \
  --data-file=- \
  --project=gen-lang-client-0772617718

# Grant access
PROJECT_NUMBER=$(gcloud projects describe gen-lang-client-0772617718 --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0772617718

# Deploy
chmod +x deploy-with-feedback.sh
./deploy-with-feedback.sh
```

## Option 3: Manual Steps in GCP Console

### Step 1: Add Slack Webhook to Secret Manager

1. Go to: https://console.cloud.google.com/security/secret-manager?project=gen-lang-client-0772617718
2. Click **"CREATE SECRET"**
3. Fill in:
   - **Name:** `SLACK_WEBHOOK`
   - **Secret value:** `https://hooks.slack.com/services/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`
4. Click **"CREATE SECRET"**

### Step 2: Grant Permissions

1. Click on the `SLACK_WEBHOOK` secret you just created
2. Click **"PERMISSIONS"** tab
3. Click **"GRANT ACCESS"**
4. Add member: Find your project number from the project settings, then add: 
   - `YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com`
5. Role: **Secret Manager Secret Accessor**
6. Click **"SAVE"**

### Step 3: Deploy Backend

1. Go to: https://console.cloud.google.com/run?project=gen-lang-client-0772617718
2. Click on **"telos-backend"** service
3. Click **"EDIT & DEPLOY NEW REVISION"**
4. Scroll to **"Environment Variables"**
5. Add new variable:
   - Name: `SLACK_FEEDBACK_CHANNEL_ID`
   - Value: `C0A6VF5PBUH`
6. Click **"DEPLOY"**
7. Wait 2-3 minutes for deployment

## Verify It Works

After deployment:

1. Get your backend URL from Cloud Run console
2. Test: `curl https://YOUR-BACKEND-URL/health`
3. Try submitting feedback from your app (press F)
4. Check your Slack channel for the notification!

---

## If Secret Already Exists

If you get "Secret already exists" error:

```bash
# Update the secret instead
echo "https://hooks.slack.com/services/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" | \
gcloud secrets versions add SLACK_WEBHOOK \
  --data-file=- \
  --project=gen-lang-client-0772617718
```

## Troubleshooting

- **"gcloud not found"**: Use Option 1 (Cloud Shell) or install gcloud SDK
- **"Permission denied"**: Make sure you're logged in: `gcloud auth login`
- **"Project not found"**: Set project: `gcloud config set project gen-lang-client-0772617718`

