# Deployment Steps for Cloud Function

## Quick Start

Follow these steps to deploy the Cloud Function and updated microservice:

### Step 1: Deploy the Cloud Function

```bash
./deploy_cloud_function.sh
```

**What this does:**
- Creates Pub/Sub topic `classification-events` (if not exists)
- Deploys Cloud Function `classification-event-handler`
- Sets up trigger from Pub/Sub topic to function

**Expected output:**
```
✅ Cloud Function deployed successfully!

📊 Function Details:
   Name: classification-event-handler
   Region: us-central1
   Trigger: Pub/Sub topic 'classification-events'
   Runtime: Python 3.11
```

### Step 2: Deploy the Updated Microservice

```bash
./deploy.sh
```

**What this does:**
- Builds Docker image with Pub/Sub client
- Deploys to Cloud Run with Pub/Sub environment variables
- Connects to Cloud SQL database

**Expected output:**
```
✅ Deployment complete!

🌐 Service URL: https://ms4-classification-uq2tkhfvqa-uc.a.run.app
```

### Step 3: Test the Integration

**Test classification (triggers Cloud Function):**
```bash
curl -X POST https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications \
  -H "Content-Type: application/json" \
  -d '{"message_ids": ["bb38a561-4bdf-4573-bcac-d83304afb078"]}'
```

**Check Cloud Function logs:**
```bash
gcloud functions logs read classification-event-handler \
  --region=us-central1 \
  --limit=10
```

**You should see:**
```
================================================================================
📊 CLASSIFICATION EVENT RECEIVED at 2025-12-12T...
================================================================================
Classification ID: ...
Message ID: bb38a561-4bdf-4573-bcac-d83304afb078
Label: followup
Priority: 6
...
```

## Verification Checklist

- [ ] Cloud Function deployed successfully
- [ ] Pub/Sub topic `classification-events` exists
- [ ] Microservice deployed with Pub/Sub support
- [ ] Classification creates event in Cloud Function logs
- [ ] Database stores classification correctly

## Troubleshooting

### Cloud Function not triggering?

1. **Check if topic exists:**
   ```bash
   gcloud pubsub topics list
   ```

2. **Check function status:**
   ```bash
   gcloud functions describe classification-event-handler --region=us-central1
   ```

3. **Manually test Pub/Sub:**
   ```bash
   gcloud pubsub topics publish classification-events \
     --message='{"cls_id":"test","msg_id":"test","label":"todo","priority":5}'
   ```

### Pub/Sub client not initializing?

Check Cloud Run logs:
```bash
gcloud run services logs read ms4-classification --region=us-central1 --limit=50
```

Look for:
- `✅ Pub/Sub client initialized: projects/.../topics/classification-events`
- `📤 Published classification event: <message_id>`

If you see:
- `⚠️ Pub/Sub client initialization failed: ...`

This means the service is running without Pub/Sub (OK for local dev, but should work in Cloud Run).

## What Gets Deployed

### Cloud Function Structure
```
cloud_function/
├── main.py              # Function code
└── requirements.txt     # Dependencies
```

### Microservice Changes
```
utils/
└── pubsub_client.py     # New: Pub/Sub event publisher

main.py                  # Updated: Emits events after classification
requirements.txt         # Updated: Added google-cloud-pubsub
deploy.sh               # Updated: Added Pub/Sub env vars
```

## Environment Variables

The following are automatically set during deployment:

```bash
GCP_PROJECT_ID=sodium-hue-479204-p3
PUBSUB_TOPIC=classification-events
```

## Cost

All within Google Cloud free tier:
- **Cloud Functions**: 2M invocations/month free
- **Pub/Sub**: 10 GB/month free
- **Expected cost**: $0

## For Demo

Show the professor:

1. **Open Cloud Function in console:**
   https://console.cloud.google.com/functions/details/us-central1/classification-event-handler

2. **Classify a message** (via API or Swagger UI)

3. **Show logs in real-time:**
   ```bash
   gcloud functions logs read classification-event-handler \
     --region=us-central1 \
     --limit=10
   ```

4. **Explain**: "Every time a message is classified, my microservice emits an event to Pub/Sub, which triggers this Cloud Function. In production, this could send notifications, update dashboards, or trigger workflows."

