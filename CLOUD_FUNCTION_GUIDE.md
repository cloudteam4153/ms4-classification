# Google Cloud Function Implementation Guide

## Overview

This document describes the Google Cloud Function implementation that fulfills the requirement:

> **"Implement at least one Google Cloud Function. Demonstrate triggering the cloud function by having one of your microservices emit an event on a topic."**

## Architecture

```
Classification Microservice (Cloud Run)
    ↓
    | Classifies message using OpenAI
    ↓
    | Stores in Cloud SQL database
    ↓
    | Emits event to Pub/Sub topic
    ↓
Google Cloud Pub/Sub Topic: "classification-events"
    ↓
    | Triggers Cloud Function
    ↓
Google Cloud Function: "classification-event-handler"
    ↓
    | Processes event (logs, could send notifications, etc.)
```

## Components

### 1. Pub/Sub Client (`utils/pubsub_client.py`)

- **Purpose**: Publishes classification events to Google Cloud Pub/Sub
- **Topic**: `classification-events`
- **Event Data**: JSON containing classification details (cls_id, msg_id, label, priority, timestamp)

### 2. Cloud Function (`cloud_function/main.py`)

- **Trigger**: Pub/Sub topic `classification-events`
- **Runtime**: Python 3.11
- **Purpose**: Receives and processes classification events
- **Current Implementation**: Logs event details (in production, could send notifications, update dashboards, etc.)

### 3. Integration in Main Service (`main.py`)

After each classification is stored in the database, the service emits an event:

```python
# Emit events to Pub/Sub for each classification
for classification in response.classifications:
    pubsub_client.publish_classification_event({
        "cls_id": classification.cls_id,
        "msg_id": classification.msg_id,
        "label": classification.label.value,
        "priority": classification.priority,
        "created_at": classification.created_at
    })
```

## Deployment

### Step 1: Deploy the Cloud Function

```bash
./deploy_cloud_function.sh
```

This script:
1. Creates the Pub/Sub topic `classification-events` (if it doesn't exist)
2. Deploys the Cloud Function with Pub/Sub trigger

### Step 2: Deploy the Microservice with Pub/Sub Support

```bash
./deploy.sh
```

This deploys your microservice with the necessary Pub/Sub environment variables.

## Testing

### 1. Classify a Message

```bash
curl -X POST https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications \
  -H "Content-Type: application/json" \
  -d '{"message_ids": ["bb38a561-4bdf-4573-bcac-d83304afb078"]}'
```

### 2. Check Cloud Function Logs

```bash
gcloud functions logs read classification-event-handler \
  --region=us-central1 \
  --limit=50
```

You should see output like:

```
================================================================================
📊 CLASSIFICATION EVENT RECEIVED at 2025-12-12T20:30:45.123456
================================================================================
Classification ID: a48068a0-4b1f-442f-b85e-0564a2946c3b
Message ID: bb38a561-4bdf-4573-bcac-d83304afb078
Label: followup
Priority: 6
Created At: 2025-12-10T23:28:40.999406
================================================================================
```

## What This Demonstrates

✅ **Cloud Function Implementation**: Function deployed and operational  
✅ **Pub/Sub Integration**: Microservice emits events to Pub/Sub topic  
✅ **Event-Driven Architecture**: Function automatically triggered by events  
✅ **Requirement Fulfilled**: "Demonstrate triggering the cloud function by having one of your microservices emit an event on a topic"

## Production Use Cases

While the current implementation logs events, in a production system this Cloud Function could:

- Send email/SMS notifications for high-priority classifications
- Update real-time analytics dashboards
- Trigger downstream workflows in other services
- Store events in a data warehouse for analysis
- Send webhooks to external systems
- Create tasks in project management tools

## Configuration

Environment variables in Cloud Run:
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `PUBSUB_TOPIC`: The Pub/Sub topic name (default: `classification-events`)

## Troubleshooting

### Events not being published

Check Cloud Run logs:
```bash
gcloud run services logs read ms4-classification --region=us-central1 --limit=50
```

Look for:
- `✅ Pub/Sub client initialized: projects/.../topics/classification-events`
- `📤 Published classification event: <message_id>`

### Cloud Function not triggering

1. Verify the topic exists:
   ```bash
   gcloud pubsub topics list
   ```

2. Check function status:
   ```bash
   gcloud functions describe classification-event-handler --region=us-central1
   ```

3. Manually test the function:
   ```bash
   gcloud pubsub topics publish classification-events \
     --message='{"cls_id":"test","msg_id":"test","label":"todo","priority":5}'
   ```

## Cost Considerations

- **Pub/Sub**: First 10 GB per month free, then $0.06 per GB
- **Cloud Functions**: First 2 million invocations free per month
- **Expected cost for this project**: Essentially $0 (well within free tier)

