# Telos Backend Deployment Script (PowerShell)
# Automates deployment to Google Cloud Run

$ErrorActionPreference = "Stop"

# Configuration - read from environment or gcloud config
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { (gcloud config get-value project 2>$null) }
$SERVICE_NAME = "telos-backend"
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "asia-south1" }
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

if (-not $PROJECT_ID) {
    Write-Host "Error: GCP_PROJECT_ID not set and no gcloud default project configured"
    Write-Host "Set it with: `$env:GCP_PROJECT_ID = 'your-project-id'"
    exit 1
}

Write-Host "Starting Telos Backend Deployment"
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed"
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Check if authenticated
$account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if (-not $account) {
    Write-Host "Error: Not authenticated with Google Cloud"
    Write-Host "Run: gcloud auth login"
    exit 1
}

# Set project
Write-Host "Setting project..."
gcloud config set project $PROJECT_ID

# Build and push Docker image
Write-Host "Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed"
    exit 1
}

Write-Host "Image built successfully"

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "FIREBASE_PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=$($env:SLACK_FEEDBACK_CHANNEL_ID),MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production,DODO_ENV=live_mode,SENDGRID_FROM_EMAIL=reports@telos.dev,SENDGRID_FROM_NAME=Telos,SENDGRID_API_KEY_SECRET_NAME=SENDGRID_API_KEY" `
  --set-secrets "DODO_PAYMENTS_API_KEY=DODO_PAYMENTS_API_KEY:latest,DODO_PRODUCT_ID_MONTHLY=DODO_PRODUCT_ID_MONTHLY:latest,DODO_PRODUCT_ID_YEARLY=DODO_PRODUCT_ID_YEARLY:latest,DODO_WEBHOOK_SECRET=DODO_WEBHOOK_SECRET:latest,FRONTEND_URL=FRONTEND_URL:latest,PORTKEY_API_KEY=PORTKEY_API_KEY:latest,PORTKEY_VIRTUAL_KEY=PORTKEY_VIRTUAL_KEY:latest,SLACK_ALERTS_WEBHOOK=SLACK_WEBHOOK:latest,SENDGRID_API_KEY=SENDGRID_API_KEY:latest" `
  --memory 512Mi `
  --cpu 1 `
  --timeout 60 `
  --concurrency 80 `
  --min-instances 0 `
  --max-instances 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed"
    exit 1
}

Write-Host "Deployment successful!"

# Get service URL
Write-Host ""
Write-Host "Getting service URL..."
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "Deployment complete!"
Write-Host ""
Write-Host "Service URL: $SERVICE_URL"
Write-Host ""
Write-Host "Test it:"
Write-Host "  curl $SERVICE_URL/health"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Test the health endpoint"
Write-Host "  2. Update your Python client with this URL"
Write-Host "  3. Test with a real Firebase token"
Write-Host ""
