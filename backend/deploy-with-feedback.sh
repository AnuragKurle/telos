#!/bin/bash
# Deploy Telos Backend with Feedback Feature
# Bash deployment script

set -e

# Configuration
PROJECT_ID="gen-lang-client-0772617718"
SERVICE_NAME="telos-backend"
REGION="us-central1"
SLACK_WEBHOOK="https://hooks.slack.com/services/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"

echo "🚀 Deploying Telos Backend with Feedback Feature..."
echo ""

# Step 1: Create or update Slack webhook secret
echo "📝 Step 1: Adding Slack webhook to Secret Manager..."
if echo "$SLACK_WEBHOOK" | gcloud secrets create SLACK_WEBHOOK \
    --data-file=- \
    --project=$PROJECT_ID 2>/dev/null; then
    echo "✓ Created SLACK_WEBHOOK secret"
else
    echo "Secret already exists, updating..."
    echo "$SLACK_WEBHOOK" | gcloud secrets versions add SLACK_WEBHOOK \
        --data-file=- \
        --project=$PROJECT_ID
    echo "✓ Updated SLACK_WEBHOOK secret"
fi

# Step 2: Grant Cloud Run access to the secret
echo ""
echo "🔐 Step 2: Granting Cloud Run access to secrets..."

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding SLACK_WEBHOOK \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo "✓ Granted access to SLACK_WEBHOOK"

# Step 3: Deploy to Cloud Run
echo ""
echo "☁️  Step 3: Deploying to Cloud Run..."
echo "This will take 2-3 minutes..."

gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars "FIREBASE_PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH,MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production" \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10

# Step 4: Get the service URL
echo ""
echo "🎉 Deployment complete!"
echo ""

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --format "value(status.url)")

echo "Backend URL: $SERVICE_URL"
echo ""
echo "Testing endpoints..."

# Test health endpoint
if curl -s "$SERVICE_URL/health" | grep -q "ok"; then
    echo "✓ Health check: OK"
else
    echo "✗ Health check failed"
fi

echo ""
echo "📝 Feedback endpoint: $SERVICE_URL/v1/feedback"
echo "💬 Slack channel ID: C0A6VF5PBUH"
echo ""
echo "✅ Ready to receive feedback from your app!"

