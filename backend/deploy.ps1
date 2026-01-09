# Telos Backend Deployment Script (PowerShell)
# Automates deployment to Google Cloud Run

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "gen-lang-client-0772617718"
$SERVICE_NAME = "telos-backend"
$REGION = "asia-south1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

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
gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated --set-env-vars "FIREBASE_PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH,MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production,PORTKEY_API_KEY=AapMbWHuS0fvPfOSF9z4iOBuEYTm,PORTKEY_VIRTUAL_KEY=google-virtual-881dd3" --memory 512Mi --cpu 1 --timeout 60 --concurrency 80 --min-instances 0 --max-instances 10

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
