# Team Integration Guide

**Service Owner**: Jonathan  
**Service URL**: https://ms4-classification-uq2tkhfvqa-uc.a.run.app  
**Status**: ✅ Production Ready

---

## 🎯 For Akhil (Composite Microservice)

### What My Service Does
Takes message IDs → Returns AI classifications (todo/followup/noise) + priority scores (1-10)

### How to Call My Service

**1. Get Classifications for Dashboard**
```python
import requests

# Get all recent classifications
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={"limit": 100}
)
classifications = response.json()

# Example response:
# [
#   {
#     "cls_id": "uuid",
#     "msg_id": "message-uuid-from-sanjay",
#     "label": "todo",
#     "priority": 8,
#     "created_at": "2025-12-10T..."
#   }
# ]

# Match with messages using msg_id
for cls in classifications:
    # Fetch full message from Sanjay using cls["msg_id"]
    # Combine for unified inbox display
```

**2. Classify New Messages (Requires JWT)**
```python
# When user wants to classify messages
response = requests.post(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={
        "message_ids": ["msg-uuid-1", "msg-uuid-2", "msg-uuid-3"]
    }
)

result = response.json()
# Returns: {"classifications": [...], "total_processed": 3, "success_count": 3}
```

**3. Filter Classifications**
```python
# Get only high-priority TODOs
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={
        "label": "todo",
        "min_priority": 7,
        "limit": 50
    }
)
```

### Integration Points
- **You call me**: When aggregating dashboard data
- **You call me**: When user triggers classification
- **I call Sanjay**: To fetch message content (you don't need to)

---

## 🎯 For David (Tasks Microservice)

### What You Can Do With My Data

**Monitor for High-Priority TODOs**
```python
import requests

# Check for new TODOs that need tasks created
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={
        "label": "todo",
        "min_priority": 6  # Medium-high priority and above
    }
)

for classification in response.json():
    msg_id = classification["msg_id"]
    priority = classification["priority"]
    
    # Check if task already exists for this message
    if not task_exists(msg_id):
        # Create task in your service
        create_task(
            message_id=msg_id,
            priority=priority,
            auto_generated=True
        )
```

### Use Cases
1. **Auto-create tasks** from high-priority TODO classifications
2. **Update task priorities** based on classification scores
3. **Link tasks to messages** using the msg_id field

---


## 🎯 For Beverly (Web UI)

### How Users Interact With My Service

**Through Akhil's Composite:**
1. User views inbox → Composite calls my `/classifications` endpoint
2. Composite shows classification badges on messages (TODO, Follow-up, etc.)
3. User clicks "Classify" → Composite calls my `POST /classifications`
4. AI analyzes → Results appear in real-time

### UI Elements You Might Show
- **Classification Badge**: "TODO" (red), "Follow-up" (yellow), "Noise" (gray)
- **Priority Indicator**: 1-10 score or stars (⭐⭐⭐)
- **Classify Button**: Triggers classification via composite
- **Filter by Classification**: Show only TODOs, etc.

---

## 🔧 API Reference

### Base URL
```
https://ms4-classification-uq2tkhfvqa-uc.a.run.app
```

### Key Endpoints

**GET /classifications**
- **Auth**: Optional
- **Params**: `label`, `min_priority`, `max_priority`, `limit`
- **Returns**: Array of classification objects

**POST /classifications** 🔒
- **Auth**: Required (JWT Bearer token)
- **Body**: `{"message_ids": ["uuid1", "uuid2"]}`
- **Returns**: Classification results

**GET /classifications/{id}**
- **Auth**: Optional
- **Returns**: Single classification object

**GET /health**
- **Auth**: None
- **Returns**: Service health status

### Full API Documentation
https://ms4-classification-uq2tkhfvqa-uc.a.run.app/docs

---

## 🧪 Testing

### Quick Health Check
```bash
curl https://ms4-classification-uq2tkhfvqa-uc.a.run.app/health
```

### Test Classification (Need JWT from Sanjay)
```bash
curl -X POST https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": ["some-message-uuid"]}'
```

### Interactive Testing
Visit: https://ms4-classification-uq2tkhfvqa-uc.a.run.app/docs

---

## 📊 Response Format

### Classification Object
```json
{
  "cls_id": "550e8400-e29b-41d4-a716-446655440000",
  "msg_id": "123e4567-e89b-12d3-a456-426614174000",
  "label": "todo",
  "priority": 8,
  "created_at": "2025-12-10T21:00:00Z"
}
```

### Classification Labels
- **`todo`**: Requires action, needs response, has deadline
- **`followup`**: Needs follow-up, reminder, pending item
- **`noise`**: Newsletter, promotion, automated, no action needed

### Priority Scores (1-10)
- **9-10**: Urgent (from CEO, critical deadline)
- **7-8**: High priority (important, time-sensitive)
- **4-6**: Medium priority (routine tasks)
- **1-3**: Low priority (FYI, newsletters)

---

## ❓ FAQ

**Q: Do I need to send you the full message content?**  
A: No! Just send message IDs. I fetch the content from Sanjay's service.


**Q: Can I classify multiple messages at once?**  
A: Yes! Send an array of message_ids in one request.

**Q: Do classifications persist?**  
A: Yes! Stored in Cloud SQL database permanently.

**Q: What if a message is already classified?**  
A: You can re-classify it. New classification will be created (we keep history).

**Q: Do I need authentication?**  
A: Only for POST (creating classifications). GET requests are public.

---

## 🐛 Troubleshooting

**401 Unauthorized**
- Make sure you're sending: `Authorization: Bearer <token>`
- Get JWT token from Sanjay's OAuth flow

**404 Message Not Found**
- Check that message_id exists in Sanjay's service
- I fetch from: `https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app/messages/{id}`

**Slow Response**
- First classification may be slow (cold start)
- Subsequent requests are fast (~1-2s)

---

**Last Updated**: December 10, 2025  
**Service Version**: 2.0.0  
**Status**: ✅ Production Ready

