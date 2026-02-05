# Deployment Guide - Telos Backend

This guide walks you through deploying the Telos backend to Google Cloud Run.

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud SDK installed**
   ```bash
   # Check if installed
   gcloud version
   
   # If not installed, download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticated with Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project gen-lang-client-0772617718
   ```

3. **Required APIs enabled** (should be done from Phase 0)
   - Cloud Run API
   - Cloud Build API
   - Secret Manager API
   - Firestore API

4. **Environment variables configured**
   - Copy `env.example` to `.env`
   - Fill in your Firebase/GCP credentials

---

## Local Testing (Do This First!)

Before deploying, test locally to ensure everything works:

```bash
# 1. Install dependencies
cd backend
npm install

# 2. Set up .env file
cp env.example .env
# Edit .env with your credentials

# 3. Start development server
npm run dev

# 4. Test health endpoint
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "ok",
#   "service": "telos-backend",
#   "version": "0.1.0",
#   "timestamp": "..."
# }
```

---

## Deployment Steps

### Step 1: Build Docker Container

Build and push the Docker image to Google Container Registry:

```bash
cd backend

# Build and upload to GCR
gcloud builds submit --tag gcr.io/gen-lang-client-0772617718/telos-backend

# This will:
# - Build the Docker image using your Dockerfile
# - Push it to gcr.io/PROJECT_ID/telos-backend:latest
# - Take ~2-5 minutes depending on connection speed
```

### Step 2: Deploy to Cloud Run

Deploy the container to Cloud Run:

```bash
gcloud run deploy telos-backend \
  --image gcr.io/gen-lang-client-0772617718/telos-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_PROJECT_ID=gen-lang-client-0772617718,GCP_PROJECT_ID=gen-lang-client-0772617718,GEMINI_SECRET_NAME=GEMINI_API_KEY,MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10

# This will:
# - Deploy your container to Cloud Run
# - Set environment variables
# - Configure scaling parameters
# - Return a public HTTPS URL
```

### Step 3: Note the Service URL

After deployment, you'll see output like:

```
Service [telos-backend] revision [telos-backend-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://telos-backend-xxxxx-uc.a.run.app
```

**Save this URL!** You'll need it for the Python client configuration.

### Step 4: Test Production Endpoint

```bash
# Replace with your actual Cloud Run URL
SERVICE_URL="https://telos-backend-xxxxx-uc.a.run.app"

# Test health endpoint
curl $SERVICE_URL/health

# Expected response:
# {
#   "status": "ok",
#   "service": "telos-backend",
#   "version": "0.1.0",
#   "timestamp": "..."
# }
```

---

## Verify Deployment

### 1. Check Cloud Run Service

```bash
# List all Cloud Run services
gcloud run services list

# Get service details
gcloud run services describe telos-backend --region us-central1
```

### 2. View Logs

```bash
# Stream logs in real-time
gcloud run services logs tail telos-backend --region us-central1

# View recent logs
gcloud run services logs read telos-backend --region us-central1 --limit 50
```

### 3. Test with Real Firebase Token

You'll need a Firebase ID token to test the analysis endpoint. You can get one by:

1. Implementing Firebase Auth in the Python client (Phase 2)
2. Using the Firebase REST API directly
3. Using the Firebase Console to get a test token

```bash
# With a valid Firebase token
curl -X POST $SERVICE_URL/v1/analyze/screenshot \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "X-Client-Version: 0.1.0" \
  -F "image=@test-screenshot.png"
```

---

## Troubleshooting

### Issue: "Permission Denied" during deployment

**Solution:** Ensure Cloud Run service account has required permissions:

```bash
# Get the service account email
gcloud run services describe telos-backend --region us-central1 --format="value(spec.template.spec.serviceAccountName)"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding gen-lang-client-0772617718 \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# Grant Firestore access (should be automatic, but just in case)
gcloud projects add-iam-policy-binding gen-lang-client-0772617718 \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/datastore.user"
```

### Issue: Gemini API calls failing

**Solution:** Check that Secret Manager has the Gemini API key:

```bash
# List secrets
gcloud secrets list

# View secret metadata (not the actual value)
gcloud secrets describe GEMINI_API_KEY

# If missing, create it:
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

### Issue: Firestore prompts not loading

**Solution:** Populate Firestore with default prompt:

Use the Firebase Console or a setup script to create:

```
prompts/screenshot-analysis
  - activeVersion: "v1"
  - updatedAt: <timestamp>

prompts/screenshot-analysis/versions/v1
  - content: "<your prompt text>"
  - createdAt: <timestamp>
```

---

## Updating the Deployment

When you make code changes:

```bash
# 1. Rebuild and push image
gcloud builds submit --tag gcr.io/gen-lang-client-0772617718/telos-backend

# 2. Deploy new version (Cloud Run will automatically use latest image)
gcloud run deploy telos-backend \
  --image gcr.io/gen-lang-client-0772617718/telos-backend \
  --region us-central1

# Cloud Run will:
# - Deploy new revision
# - Gradually shift traffic to it
# - Keep previous revision as backup
```

---

## Rollback

If something breaks, rollback to previous revision:

```bash
# List revisions
gcloud run revisions list --service telos-backend --region us-central1

# Rollback to specific revision
gcloud run services update-traffic telos-backend \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

---

## Monitoring & Costs

### View Metrics

1. Go to Cloud Console: https://console.cloud.google.com
2. Navigate to Cloud Run → telos-backend
3. View "Metrics" tab for:
   - Request count
   - Latency
   - Error rate
   - Container instances

### Estimate Costs

Cloud Run pricing (as of 2025):
- **CPU:** $0.00002400 per vCPU-second
- **Memory:** $0.00000250 per GiB-second
- **Requests:** $0.40 per million requests
- **Free tier:** 2 million requests/month, 360,000 GiB-seconds/month

For 1000 requests/day (~30k/month):
- Requests: ~$0.01/month
- CPU/Memory: ~$1-2/month
- **Total: ~$2-3/month** (well within free tier for beta)

---

## Next Steps

After deployment:

1. **Save the Cloud Run URL** to your password manager
2. **Update Python client** with the production URL
3. **Test end-to-end** with the Python client
4. **Monitor logs** for the first few days
5. **Set up alerts** in Cloud Console (optional)

---

## Security Notes

- Cloud Run service is public (`--allow-unauthenticated`) because auth is handled by Firebase tokens
- Never commit `.env` file or service account keys
- All secrets are stored in Secret Manager, not environment variables
- Images are processed in-memory and never saved to disk
- Rate limiting prevents abuse

---

## Quick Reference

```bash
# Deploy
gcloud builds submit --tag gcr.io/gen-lang-client-0772617718/telos-backend
gcloud run deploy telos-backend --image gcr.io/gen-lang-client-0772617718/telos-backend --region us-central1

# View logs
gcloud run services logs tail telos-backend --region us-central1

# Get service URL
gcloud run services describe telos-backend --region us-central1 --format="value(status.url)"

# Delete service (if needed)
gcloud run services delete telos-backend --region us-central1
```

---

**You're all set!** 🚀

Your backend is now deployed to Cloud Run and ready to accept screenshot uploads from the Python client.


