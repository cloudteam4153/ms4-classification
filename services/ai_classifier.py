from __future__ import annotations

import json
import random
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

from models.classification import ClassificationLabel, ClassificationRead, ClassificationRequest, ClassificationResponse
from models.message import MessageRead

class AIClassifier:
    """AI-powered message classifier with mock OpenAI integration"""
    
    def __init__(self):
        self.openai_api_key = None  # Will be set when OpenAI integration is added
        self.mock_mode = True  # For now, use mock responses
    
    def classify_messages(self, messages: List[MessageRead]) -> ClassificationResponse:
        """
        Classify a list of messages using AI
        
        Args:
            messages: List of messages to classify
            
        Returns:
            ClassificationResponse with classification results
        """
        classifications = []
        success_count = 0
        error_count = 0
        
        for message in messages:
            try:
                # Use AI to classify the message
                if self.mock_mode:
                    classification = self._mock_classify_message(message)
                else:
                    classification = self._ai_classify_message(message)
                
                classifications.append(classification)
                success_count += 1
                
            except Exception as e:
                print(f"Error classifying message {message.msg_id}: {e}")
                error_count += 1
        
        return ClassificationResponse(
            classifications=classifications,
            total_processed=len(messages),
            success_count=success_count,
            error_count=error_count
        )
    
    def _apply_business_rules(self, message: MessageRead, base_priority: int) -> int:
        """Apply essential business rules for priority adjustment"""
        priority = base_priority
        
        # CEO emails always high priority
        if "ceo" in message.sender.lower() or "boss" in message.sender.lower():
            priority = min(10, priority + 3)
        
        # Legal emails get priority boost
        if "legal" in message.sender.lower():
            priority = min(10, priority + 2)
        
        # Manager emails get slight boost
        if "manager" in message.sender.lower():
            priority = min(10, priority + 1)
        
        return priority
    
    def _mock_classify_message(self, message: MessageRead) -> ClassificationRead:
        """Mock AI classification for development/testing"""
        # Create AI-like prompt analysis
        content = f"{message.subject or ''} {message.snippet}".lower()
        
        # AI-like analysis of the message
        urgency_indicators = ["urgent", "asap", "deadline", "due tomorrow", "critical", "immediately"]
        action_indicators = ["need to", "should", "must", "please", "can you", "action", "task", "todo"]
        followup_indicators = ["follow up", "follow-up", "reminder", "check", "status", "update"]
        noise_indicators = ["newsletter", "unsubscribe", "marketing", "promotion", "sale"]
        
        # Calculate urgency score
        urgency_score = sum(1 for word in urgency_indicators if word in content)
        action_score = sum(1 for word in action_indicators if word in content)
        followup_score = sum(1 for word in followup_indicators if word in content)
        noise_score = sum(1 for word in noise_indicators if word in content)
        
        # AI-like decision making
        if noise_score > 0 and action_score == 0:
            label = ClassificationLabel.NOISE
        elif urgency_score >= 2 or (urgency_score >= 1 and action_score >= 2):
            label = ClassificationLabel.TODO
        elif action_score >= 2 or followup_score >= 1:
            label = ClassificationLabel.TODO
        elif followup_score >= 1:
            label = ClassificationLabel.FOLLOWUP
        else:
            label = ClassificationLabel.NOISE
        
        # Calculate priority based on AI analysis
        base_priority = 5
        if urgency_score >= 2:
            base_priority = 9
        elif urgency_score >= 1:
            base_priority = 7
        elif action_score >= 2:
            base_priority = 6
        elif action_score >= 1:
            base_priority = 5
        else:
            base_priority = 3
        
        # Apply business rules
        final_priority = self._apply_business_rules(message, base_priority)

        return ClassificationRead(
            cls_id=uuid4(),
            msg_id=message.msg_id,
            label=label,
            priority=final_priority,
            created_at=datetime.utcnow()
        )
    
    def _ai_classify_message(self, message: MessageRead) -> ClassificationRead:
        """Real AI classification using OpenAI API (to be implemented)"""
        # TODO: Implement actual OpenAI API call with comprehensive prompt
        # For now, fall back to mock
        return self._mock_classify_message(message)
    
