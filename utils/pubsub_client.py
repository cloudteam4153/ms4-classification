"""
Pub/Sub client for emitting classification events to Google Cloud Pub/Sub
"""
import json
import os
from typing import Dict, Any, Optional
from google.cloud import pubsub_v1


class PubSubClient:
    """Client for publishing classification events to Pub/Sub"""
    
    def __init__(self):
        """Initialize Pub/Sub publisher client"""
        self.project_id = os.getenv("GCP_PROJECT_ID", "sodium-hue-479204-p3")
        self.topic_name = os.getenv("PUBSUB_TOPIC", "classification-events")
        
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            self.enabled = True
            print(f"✅ Pub/Sub client initialized: {self.topic_path}")
        except Exception as e:
            print(f"⚠️  Pub/Sub client initialization failed: {e}")
            print("   Events will not be published (this is OK for local development)")
            self.publisher = None
            self.topic_path = None
            self.enabled = False
    
    def publish_classification_event(self, classification_data: Dict[str, Any]) -> Optional[str]:
        """
        Publish a classification event to Pub/Sub
        
        Args:
            classification_data: Dictionary containing classification details
            
        Returns:
            Message ID if successful, None if failed or disabled
        """
        if not self.enabled:
            return None
        
        try:
            # Convert classification data to JSON
            message_json = json.dumps({
                "cls_id": str(classification_data.get("cls_id")),
                "msg_id": str(classification_data.get("msg_id")),
                "label": classification_data.get("label"),
                "priority": classification_data.get("priority"),
                "created_at": classification_data.get("created_at").isoformat() 
                              if hasattr(classification_data.get("created_at"), "isoformat")
                              else str(classification_data.get("created_at"))
            })
            
            # Encode to bytes
            message_bytes = message_json.encode("utf-8")
            
            # Publish to Pub/Sub
            future = self.publisher.publish(self.topic_path, message_bytes)
            message_id = future.result(timeout=5.0)
            
            print(f"📤 Published classification event: {message_id}")
            return message_id
            
        except Exception as e:
            print(f"❌ Error publishing to Pub/Sub: {e}")
            return None
    
    def publish_batch_classification_event(self, classifications: list) -> int:
        """
        Publish multiple classification events
        
        Args:
            classifications: List of classification dictionaries
            
        Returns:
            Number of successfully published events
        """
        if not self.enabled:
            return 0
        
        success_count = 0
        for classification in classifications:
            if self.publish_classification_event(classification):
                success_count += 1
        
        return success_count


# Global instance
pubsub_client = PubSubClient()

