#!/bin/bash

# Deploy script for Cloud Run
# Usage: ./deploy.sh [project-id] [region]

set -e

# Load environment variables from deploy_env.sh if it exists
if [ -f "deploy_env.sh" ]; then
    echo "📦 Loading environment variables from deploy_env.sh..."
    source deploy_env.sh
else
    echo "⚠️  Warning: deploy_env.sh not found. Using defaults."
    echo "   Copy deploy_env.sh.example to deploy_env.sh and configure it."
fi

# Configuration
PROJECT_ID=${1:-${PROJECT_ID:-"sodium-hue-479204-p3"}}
REGION=${2:-${REGION:-"us-central1"}}
SERVICE_NAME="ms4-classification"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Required environment variables (loaded from deploy_env.sh)
# DO NOT put secrets here - this file is committed to git!
DB_PASSWORD=${DB_PASSWORD:-""}
OPENAI_API_KEY=${OPENAI_API_KEY:-""}
DB_USER=${DB_USER:-"postgres"}
DB_NAME=${DB_NAME:-"classifications_db"}
INTEGRATIONS_SERVICE_URL=${INTEGRATIONS_SERVICE_URL:-"https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app"}

# Check for required secrets
if [ -z "$DB_PASSWORD" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: Missing required environment variables"
    echo "   Please create deploy_env.sh from deploy_env.sh.example"
    exit 1
fi

echo "🚀 Deploying Classification Microservice to Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build container image
echo "🔨 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300 \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:ms4-classifications \
  --set-env-vars "ENVIRONMENT=production,FASTAPIPORT=8080,DB_TYPE=postgresql,DB_HOST=/cloudsql/${PROJECT_ID}:${REGION}:ms4-classifications,DB_PORT=5432,DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},OPENAI_API_KEY=${OPENAI_API_KEY},INTEGRATIONS_SERVICE_URL=${INTEGRATIONS_SERVICE_URL},GCP_PROJECT_ID=${PROJECT_ID},PUBSUB_TOPIC=classification-events"

# Get service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📝 Service deployed successfully!"
echo "   Test: curl ${SERVICE_URL}/health"
echo "   Docs: ${SERVICE_URL}/docs"
echo ""
echo "✅ Environment variables configured:"
echo "   - Database: Cloud SQL PostgreSQL"
echo "   - OpenAI API: Enabled"
echo "   - Integrations Service: Connected"
echo ""

