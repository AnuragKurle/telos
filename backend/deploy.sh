#!/bin/bash

# Telos Backend Deployment Script
# Automates deployment to Google Cloud Run

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration - read from environment or gcloud config
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
SERVICE_NAME="telos-backend"
REGION="${GCP_REGION:-asia-south1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID not set and no gcloud default project configured${NC}"
    echo "Set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo -e "${BLUE}🚀 Telos Backend Deployment${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with Google Cloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Set project
echo -e "${BLUE}📋 Setting project...${NC}"
gcloud config set project ${PROJECT_ID}

# Build and push Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image built successfully${NC}"

# Deploy to Cloud Run
echo -e "${BLUE}☁️  Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_PROJECT_ID=${PROJECT_ID},GCP_PROJECT_ID=${PROJECT_ID},GEMINI_SECRET_NAME=GEMINI_API_KEY,SLACK_FEEDBACK_CHANNEL_ID=${SLACK_FEEDBACK_CHANNEL_ID:-},MIN_CLIENT_VERSION=0.1.0,RATE_LIMIT_PER_HOUR=100,RATE_LIMIT_PER_DAY=2000,NODE_ENV=production,DODO_ENV=live_mode,SENDGRID_FROM_EMAIL=reports@telos.dev,SENDGRID_FROM_NAME=Telos,SENDGRID_API_KEY_SECRET_NAME=SENDGRID_API_KEY \
  --set-secrets DODO_PAYMENTS_API_KEY=DODO_PAYMENTS_API_KEY:latest,DODO_PRODUCT_ID_MONTHLY=DODO_PRODUCT_ID_MONTHLY:latest,DODO_PRODUCT_ID_YEARLY=DODO_PRODUCT_ID_YEARLY:latest,DODO_WEBHOOK_SECRET=DODO_WEBHOOK_SECRET:latest,FRONTEND_URL=FRONTEND_URL:latest,PORTKEY_API_KEY=PORTKEY_API_KEY:latest,PORTKEY_VIRTUAL_KEY=PORTKEY_VIRTUAL_KEY:latest,SLACK_ALERTS_WEBHOOK=SLACK_WEBHOOK:latest,SENDGRID_API_KEY=SENDGRID_API_KEY:latest \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment successful!${NC}"

# Get service URL
echo ""
echo -e "${BLUE}📍 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "Service URL: ${BLUE}${SERVICE_URL}${NC}"
echo ""
echo "Test it:"
echo -e "  ${BLUE}curl ${SERVICE_URL}/health${NC}"
echo ""
echo "Next steps:"
echo "  1. Test the health endpoint"
echo "  2. Update your Python client with this URL"
echo "  3. Test with a real Firebase token"
echo ""

