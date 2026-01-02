# Deploy Telos Backend with Feedback Feature
# PowerShell deployment script

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "gen-lang-client-0772617718"
$SERVICE_NAME = "telos-backend"
$REGION = "us-central1"
$SLACK_WEBHOOK = "https://hooks.slack.com/services/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"

Write-Host "Deploying Telos Backend with Feedback Feature..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Create or update Slack webhook secret
Write-Host "Step 1: Adding Slack webhook to Secret Manager..." -ForegroundColor Yellow

# Check if secret exists
$secretExists = gcloud secrets describe SLACK_WEBHOOK --project=$PROJECT_ID 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret already exists, updating..." -ForegroundColor Yellow
    echo $SLACK_WEBHOOK | gcloud secrets versions add SLACK_WEBHOOK --data-file=- --project=$PROJECT_ID
    Write-Host "Updated SLACK_WEBHOOK secret" -ForegroundColor Green
} else {
    Write-Host "Creating new secret..." -ForegroundColor Yellow
    echo $SLACK_WEBHOOK | gcloud secrets create SLACK_WEBHOOK --data-file=- --project=$PROJECT_ID
    Write-Host "Created SLACK_WEBHOOK secret" -ForegroundColor Green
}

# Step 2: Grant Cloud Run access to the secret
Write-Host ""
Write-Host "Step 2: Granting Cloud Run access to secrets..." -ForegroundColor Yellow

# Get the project number
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$SERVICE_ACCOUNT = "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding SLACK_WEBHOOK --member="serviceAccount:${SERVICE_ACCOUNT}" --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID

Write-Host "Granted access to SLACK_WEBHOOK" -ForegroundColor Green

# Step 3: Deploy to Cloud Run
Write-Host ""
Write-Host "Step 3: Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This will take 2-3 minutes..." -ForegroundColor Gray

gcloud run deploy $SERVICE_NAME --source . --platform managed --region $REGION --project $PROJECT_ID --allow-unauthenticated --set-env-vars "FIREBASE_PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=C0A6VF5PBUH,MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production" --memory 512Mi --cpu 1 --timeout 60 --concurrency 80 --min-instances 0 --max-instances 10

# Step 4: Get the service URL
Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""

$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format "value(status.url)"

Write-Host "Backend URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow

# Test health endpoint
$healthUrl = "$SERVICE_URL/health"
$response = Invoke-RestMethod -Uri $healthUrl -Method Get

Write-Host "Health check: OK" -ForegroundColor Green
Write-Host "  Service: $($response.service)" -ForegroundColor Gray
Write-Host "  Version: $($response.version)" -ForegroundColor Gray

Write-Host ""
Write-Host "Feedback endpoint: $SERVICE_URL/v1/feedback" -ForegroundColor Cyan
Write-Host "Slack channel ID: C0A6VF5PBUH" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to receive feedback from your app!" -ForegroundColor Green
