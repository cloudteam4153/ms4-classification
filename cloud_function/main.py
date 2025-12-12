"""
Google Cloud Function for Classification Events
This function is triggered by Pub/Sub events when classifications are created
"""
import json
import base64
import functions_framework
from datetime import datetime


@functions_framework.cloud_event
def classification_event_handler(cloud_event):
    """
    Cloud Function triggered by Pub/Sub when a new classification is created.
    
    This demonstrates the requirement:
    "Implement at least one Google Cloud Function. Demonstrate triggering 
    the cloud function by having one of your microservices emit an event on a topic."
    
    Args:
        cloud_event: A CloudEvent object containing the Pub/Sub message
    """
    # Extract message data from Pub/Sub event
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    
    try:
        # Parse the classification data
        classification_data = json.loads(pubsub_message)
        
        # Log the classification event (in production, this could trigger notifications, 
        # update analytics, trigger workflows, etc.)
        print("=" * 80)
        print(f"📊 CLASSIFICATION EVENT RECEIVED at {datetime.utcnow().isoformat()}")
        print("=" * 80)
        print(f"Classification ID: {classification_data.get('cls_id')}")
        print(f"Message ID: {classification_data.get('msg_id')}")
        print(f"Label: {classification_data.get('label')}")
        print(f"Priority: {classification_data.get('priority')}")
        print(f"Created At: {classification_data.get('created_at')}")
        print("=" * 80)
        
        # In a real system, you could:
        # - Send notifications to users
        # - Update analytics dashboards
        # - Trigger downstream workflows
        # - Update external systems
        # - Send emails for high-priority items
        
        if classification_data.get('priority', 0) >= 8:
            print("🔥 HIGH PRIORITY CLASSIFICATION - Would trigger urgent notification")
        
        return {"status": "success", "processed": classification_data.get('cls_id')}
        
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding message: {e}")
        return {"status": "error", "message": "Invalid JSON"}
    except Exception as e:
        print(f"❌ Error processing classification event: {e}")
        return {"status": "error", "message": str(e)}

