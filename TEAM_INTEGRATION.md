# Team Integration Guide

**Service Owner**: Jonathan  
**Service URL**: https://ms4-classification-uq2tkhfvqa-uc.a.run.app  
**Status**: ✅ Production Ready

---

## 🎯 For Akhil (Composite Microservice)

### What My Service Does
Takes message IDs → Returns AI classifications (todo/followup/noise) + priority scores (1-10)

### How to Call My Service

**1. Get Classifications for User (Dashboard)**
```python
import requests

# Get classifications for specific user
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={
        "user_id": "authenticated_user_id",  # Filter by user
        "limit": 100
    }
)
classifications = response.json()

# Example response:
# [
#   {
#     "cls_id": "uuid",
#     "msg_id": "message-uuid-from-sanjay",
#     "user_id": "authenticated_user_id",
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

**2. Classify New Messages for User**
```python
# Option A: Classify specific messages
response = requests.post(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    json={
        "message_ids": ["msg-uuid-1", "msg-uuid-2"],
        "user_id": "authenticated_user_id"  # Tag with user
    }
)

# Option B: Classify ALL messages for a user (first-time setup)
response = requests.post(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    json={
        "user_id": "authenticated_user_id"  # Fetches & classifies all
    }
)

result = response.json()
# Returns: {"classifications": [...], "total_processed": 44, "success_count": 44}
# Note: Also triggers Cloud Function for each classification!
```

**3. Filter Classifications**
```python
# Get only high-priority TODOs for a user
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={
        "user_id": "authenticated_user_id",  # Important: filter by user!
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

# Check for new TODOs for a specific user
response = requests.get(
    "https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications",
    params={
        "user_id": "user_id_here",  # Filter by user
        "label": "todo",
        "min_priority": 6  # Medium-high priority and above
    }
)

for classification in response.json():
    msg_id = classification["msg_id"]
    user_id = classification["user_id"]
    priority = classification["priority"]
    
    # Check if task already exists for this message
    if not task_exists(msg_id):
        # Create task in your service
        create_task(
            user_id=user_id,
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
- **Auth**: None required
- **Params**: `user_id` (filter by user), `label`, `min_priority`, `max_priority`, `limit`
- **Returns**: Array of classification objects

**POST /classifications**
- **Auth**: None required (handled by composite)
- **Body**: `{"message_ids": ["uuid1", "uuid2"], "user_id": "user123"}` OR `{"user_id": "user123"}`
- **Returns**: Classification results
- **Note**: Triggers Cloud Function for each classification created!

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

### Test Classification
```bash
curl -X POST https://ms4-classification-uq2tkhfvqa-uc.a.run.app/classifications \
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
  "user_id": "authenticated_user_id",
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
A: No! All endpoints are public. OAuth/JWT is handled by Sanjay's service.

**Q: How does user filtering work?**  
A: Pass `user_id` in POST to tag classifications, and in GET to filter. Each user only sees their own classifications.

---

## 🐛 Troubleshooting

**404 Message Not Found**
- Check that message_id exists in Sanjay's service
- I fetch from: `https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app/messages/{id}`

**Slow Response**
- First classification may be slow (cold start)
- Subsequent requests are fast (~1-2s)

---

**Last Updated**: December 12, 2025  
**Service Version**: 2.0.0  
**Status**: ✅ Production Ready

**New Features**:
- ✅ User-based filtering with `user_id` parameter
- ✅ Cloud Function integration (triggers on every classification)
- ✅ Classify all messages for a user in one request

