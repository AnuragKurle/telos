# Manual Deployment Guide

## The Issue
Your local machine doesn't have `gcloud` CLI installed. You have two options:

## Option 1: Install gcloud CLI (Recommended)

1. Download from: https://cloud.google.com/sdk/docs/install
2. Run installer
3. Authenticate: `gcloud auth login`
4. Set project: `gcloud config set project gen-lang-client-0772617718`
5. Deploy: `.\deploy.ps1`

## Option 2: Deploy via Google Cloud Console (Quick Fix)

### Step 1: Prepare the code
Your code is already ready in `D:\Experiments\screentracker\backend`

### Step 2: Deploy via Cloud Shell
1. Go to: https://console.cloud.google.com/run?project=gen-lang-client-0772617718
2. Click "Cloud Shell" icon (top right, looks like `>_`)
3. In Cloud Shell, run:

```bash
# Clone or upload your code (you can drag-drop files into Cloud Shell)
# Or use Cloud Shell Editor

# Navigate to backend folder
cd backend

# Build and deploy
gcloud builds submit --tag gcr.io/gen-lang-client-0772617718/telos-backend

gcloud run deploy telos-backend \
  --image gcr.io/gen-lang-client-0772617718/telos-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "FIREBASE_PROJECT_ID=gen-lang-client-0772617718,GCP_PROJECT_ID=gen-lang-client-0772617718,GEMINI_SECRET_NAME=GEMINI_API_KEY,MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10
```

## Option 3: Use Cloud Build Trigger (Automated)

If you push to GitHub, you can set up automatic deployments:
1. Push backend code to GitHub
2. Set up Cloud Build trigger in GCP Console
3. Auto-deploy on every push

## What Changed in This Update

### Files Modified:
- `src/services/gemini.js` - Now respects AI-generated emoji/color
- `src/services/prompts.js` - Added new prompt getters
- `setup-firestore-prompts.js` - Syncs from local files

### Why You Need to Redeploy:
The backend code that parses Gemini responses was updated to:
1. Use AI-generated `category_emoji` and `category_color` (not hardcoded)
2. Include `simple_category` field
3. Pass `detailed_context` as object

Without redeployment, your tracker will continue showing "Unknown" because the old backend is overriding the AI's values.

## Quick Test After Deployment

```bash
# Health check
curl https://telos-backend-761085171876.us-central1.run.app/health

# Should return: {"status":"ok","timestamp":"..."}
```

Then restart your Python tracker - it should now show proper categories!

