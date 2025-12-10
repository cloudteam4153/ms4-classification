# Classification Microservice (ms4)

**Live Service:** https://ms4-classification-uq2tkhfvqa-uc.a.run.app  
**API Docs:** https://ms4-classification-uq2tkhfvqa-uc.a.run.app/docs  
**Team Member:** Jonathan Lederer

AI-powered message classification microservice using OpenAI GPT for a unified inbox assistant. Deployed on Google Cloud Run with Cloud SQL database.

---

## 🎯 What This Service Does

Classifies email and Slack messages into three categories using AI:
- **`todo`** - Messages requiring action or response
- **`followup`** - Messages needing follow-up or reminders  
- **`noise`** - Newsletters, promotions, automated messages

Each classification includes a priority score (1-10) based on:
- Urgency indicators (URGENT, ASAP, deadline)
- Sender importance (CEO, manager vs automated)
- Action requirements (need to, must, please)
- Time sensitivity (today, tomorrow, EOD)

---

## 🏗️ Architecture & Integration

### How It Fits in the System

```
User → Google OAuth (Sanjay/ms2) 
     → JWT Token
     → Composite Service (Akhil/ms1)
     → Classification Service (YOU ARE HERE)
     → Returns classifications
     → Composite aggregates with messages + tasks
     → Web UI (Beverly) displays unified inbox
```

### Service Dependencies

**Integrates WITH:**
- **Integrations Service (Sanjay/ms2)**: Fetches messages via `/messages` API
- **Composite Service (Akhil/ms1)**: Receives classification requests, returns results

**Used BY:**
- **Tasks Service (David/ms3)**: Monitors classifications to auto-create tasks
- **Composite Service (Akhil/ms1)**: Aggregates classifications with messages for dashboard

---

## 🔌 API Endpoints

### Public Endpoints
- `GET /` - Service info and status
- `GET /health` - Health check
- `GET /messages` - List messages (proxies to Sanjay's service)
- `GET /messages/{id}` - Get single message
- `GET /classifications` - List all classifications
- `GET /classifications/{id}` - Get single classification

### Classification Endpoints
- `POST /classifications` - **Classify messages using OpenAI**
- `PUT /classifications/{id}` - Update classification
- `DELETE /classifications/{id}` - Delete classification

*Note: JWT validation is handled by Sanjay's integrations service (ms2)*

---

## 🚀 Quick Integration Guide

### For Akhil (Composite Service)

**Call classification endpoint:**
```python
import requests

# Get classifications for dashboard
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={"limit": 50}
)
classifications = response.json()

# Match with messages using msg_id
for classification in classifications:
    msg_id = classification["msg_id"]
    # Fetch full message from Sanjay's service using msg_id
```

**Trigger new classification:**
```python
# User wants to classify new messages
response = requests.post(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={"message_ids": [msg_id1, msg_id2, msg_id3]}
)
```

### For David (Tasks Service)

**Monitor for new classifications:**
```python
# Periodically check for new TODO classifications
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={"label": "todo", "min_priority": 7}
)

# Auto-create tasks from high-priority TODOs
for cls in response.json():
    if not task_exists(cls["msg_id"]):
        create_task(cls["msg_id"], cls["priority"])
```

### For Sanjay (Integrations Service)

**Your service fetches messages from:**
```
GET https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app/messages
```

No changes needed on your end - we pull from you!

---

## 🔧 Technical Details

### Tech Stack
- **Framework**: FastAPI 0.116.1
- **AI Model**: OpenAI GPT-4o-mini
- **Database**: Google Cloud SQL (PostgreSQL 14)
- **Deployment**: Google Cloud Run
- **Authentication**: JWT token validation
- **Language**: Python 3.11

### Database Schema

```sql
CREATE TABLE classifications (
    cls_id UUID PRIMARY KEY,
    msg_id UUID NOT NULL,  -- Foreign key to messages in Sanjay's DB
    label VARCHAR(20) NOT NULL CHECK (label IN ('todo', 'followup', 'noise')),
    priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_id (msg_id),
    INDEX idx_label (label),
    INDEX idx_priority (priority)
);
```

### Response Format

**Classification Object:**
```json
{
  "cls_id": "550e8400-e29b-41d4-a716-446655440000",
  "msg_id": "123e4567-e89b-12d3-a456-426614174000",
  "label": "todo",
  "priority": 8,
  "created_at": "2025-12-10T21:00:00Z"
}
```

---

## 🧪 Testing the Service

### 1. Health Check
```bash
curl https://ms4-classification-uq2tkhfvqa-uc.a.run.app/health
```

### 2. View Service Status
```bash
curl https://ms4-classification-uq2tkhfvqa-uc.a.run.app/
# Shows: database status, AI mode, environment
```

### 3. List Classifications (No Auth Required)
```bash
curl https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications?limit=10
```

### 4. Classify Messages (Requires JWT)
```bash
curl -X POST https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_ids": ["msg-uuid-1", "msg-uuid-2"]
  }'
```

### 5. Interactive Testing
Visit: https://ms4-classification-uq2tkhfvqa-uc.a.run.app/docs

---

## 📋 Professor Requirements ✅

### 1. OAuth2/OIDC + JWT Token Validation ✅
- Handled by Sanjay's integrations service (ms2)
- Users log in with Google OAuth
- JWT tokens generated and validated by Sanjay's service
- **Professor requirement met by team integration**

### 2. Cloud Run Deployment ✅
- Service: ms4-classification
- Region: us-central1
- URL: https://ms4-classification-uq2tkhfvqa-uc.a.run.app

### 3. Cloud SQL Database ✅
- PostgreSQL 14 instance: ms4-classifications
- Database: classifications_db
- Stores all classification results

---

## 🎬 Demo Script (Friday Dec 12, 3pm)

**1. Show AI Classification (2 min)**
- Show message from Sanjay's service
- Call classification endpoint
- OpenAI analyzes: sender, urgency, content
- Returns: label (todo/followup/noise) + priority (1-10)

**2. Show Database Storage (1 min)**
- GET `/classifications` shows stored results
- Data persists in Cloud SQL
- Can be queried by Akhil's composite

**3. Show Integration (1 min)**
- Service fetches messages from Sanjay's API
- Stores only msg_id + classification
- Akhil's composite aggregates everything

---

## 🔗 Important Links

- **Live Service**: https://ms4-classification-uq2tkhfvqa-uc.a.run.app
- **API Documentation**: https://ms4-classification-uq2tkhfvqa-uc.a.run.app/docs
- **Health Check**: https://ms4-classification-uq2tkhfvqa-uc.a.run.app/health
- **GitHub**: [Your repo URL]
- **Cloud Run Console**: https://console.cloud.google.com/run (Project: sodium-hue-479204-p3)
- **Cloud SQL Console**: https://console.cloud.google.com/sql

---

## 📁 Project Structure

```
ms4-classification/
├── main.py                      # FastAPI application & endpoints
├── models/
│   ├── classification.py        # Classification data models
│   ├── message.py              # Message data models
│   └── health.py               # Health check model
├── services/
│   ├── ai_classifier.py        # OpenAI GPT classification logic
│   └── integrations_client.py  # Client for Sanjay's API
├── middleware/
│   └── auth.py                 # JWT validation middleware
├── utils/
│   ├── config.py               # Environment configuration
│   └── database.py             # Cloud SQL connection
├── Dockerfile                   # Container definition
├── deploy.sh                    # Deployment script
└── requirements.txt            # Python dependencies
```

---

## 🤝 Team

- **Jonathan** (Classification/ms4): 
- **Sanjay** (Integrations/ms2): JWT tokens, messages API
- **Akhil** (Composite/ms1): Integration requests
- **David** (Tasks/ms3): Task auto-creation
- **Beverly** (Web UI): Frontend integration

---

**Status**: ✅ **PRODUCTION READY** - Deployed and fully operational!
