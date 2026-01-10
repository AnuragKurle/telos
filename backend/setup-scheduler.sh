#!/bin/bash
# Setup Cloud Scheduler for automated daily emails
#
# This script creates a Cloud Scheduler job that triggers the email sending
# endpoint every hour. The backend will check if it's time to send emails
# based on each user's timezone and preferences.

echo "Setting up Cloud Scheduler for Telos Daily Emails"
echo "=================================================="
echo ""

PROJECT_ID="gen-lang-client-0772617718"
REGION="asia-south1"
JOB_NAME="telos-daily-emails"
SCHEDULE="0 * * * *"  # Every hour
BACKEND_URL="https://telos-backend-ae7k4avtpq-el.a.run.app"
ENDPOINT="/v1/reports/trigger-daily-emails"

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Schedule: Every hour (cron: $SCHEDULE)"
echo "  Endpoint: $BACKEND_URL$ENDPOINT"
echo ""

# Enable Cloud Scheduler API
echo "Enabling Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID

# Delete existing job if it exists
echo ""
echo "Checking for existing job..."
gcloud scheduler jobs delete $JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID \
    --quiet 2>/dev/null || echo "No existing job found"

# Create the scheduler job
echo ""
echo "Creating Cloud Scheduler job..."
gcloud scheduler jobs create http $JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID \
    --schedule="$SCHEDULE" \
    --uri="$BACKEND_URL$ENDPOINT" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --oidc-service-account-email="$PROJECT_ID@appspot.gserviceaccount.com" \
    --oidc-token-audience="$BACKEND_URL" \
    --time-zone="Asia/Kolkata" \
    --description="Trigger daily email reports for Telos users"

echo ""
echo "✅ Cloud Scheduler job created successfully!"
echo ""
echo "The job will run every hour and:"
echo "  1. Check all users with email reports enabled"
echo "  2. Generate summaries from Firestore usage data if missing"
echo "  3. Send emails to users at their preferred time (9 AM local)"
echo ""
echo "To manually trigger the job now:"
echo "  gcloud scheduler jobs run $JOB_NAME --location=$REGION --project=$PROJECT_ID"
echo ""
echo "To view logs:"
echo "  gcloud logging read \"resource.type=cloud_run_revision\" --limit=50 --project=$PROJECT_ID"
