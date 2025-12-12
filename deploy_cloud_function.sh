#!/bin/bash

# Deploy Google Cloud Function for Classification Events
# This script:
# 1. Creates the Pub/Sub topic if it doesn't exist
# 2. Deploys the Cloud Function that listens to that topic

set -e  # Exit on error

PROJECT_ID="sodium-hue-479204-p3"
REGION="us-central1"
TOPIC_NAME="classification-events"
FUNCTION_NAME="classification-event-handler"

echo "🚀 Deploying Classification Event Cloud Function"
echo "================================================"

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Create Pub/Sub topic if it doesn't exist
echo "📬 Creating Pub/Sub topic (if not exists)..."
if gcloud pubsub topics describe $TOPIC_NAME --project=$PROJECT_ID &> /dev/null; then
    echo "✅ Topic '$TOPIC_NAME' already exists"
else
    gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID
    echo "✅ Topic '$TOPIC_NAME' created"
fi

# Deploy Cloud Function
echo "🔧 Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --region=$REGION \
    --runtime=python311 \
    --source=./cloud_function \
    --entry-point=classification_event_handler \
    --trigger-topic=$TOPIC_NAME \
    --project=$PROJECT_ID \
    --max-instances=10 \
    --memory=256MB \
    --timeout=60s

echo ""
echo "✅ Cloud Function deployed successfully!"
echo ""
echo "📊 Function Details:"
echo "   Name: $FUNCTION_NAME"
echo "   Region: $REGION"
echo "   Trigger: Pub/Sub topic '$TOPIC_NAME'"
echo "   Runtime: Python 3.11"
echo ""
echo "🔍 View logs:"
echo "   gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=50"
echo ""
echo "🧪 Test the function by classifying a message in your microservice!"
echo "   It will automatically emit an event to the topic and trigger this function."
echo ""

