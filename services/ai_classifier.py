from __future__ import annotations

import json
import random
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from openai import OpenAI

from models.classification import ClassificationLabel, ClassificationRead, ClassificationRequest, ClassificationResponse
from models.message import MessageRead
from utils.config import config

class AIClassifier:
    """AI-powered message classifier using OpenAI API"""
    
    def __init__(self):
        self.openai_api_key = config.OPENAI_API_KEY
        self.openai_model = config.OPENAI_MODEL
        
        # Use mock mode if no API key is provided
        self.mock_mode = not self.openai_api_key
        
        if not self.mock_mode:
            self.client = OpenAI(api_key=self.openai_api_key)
            print(f"✅ OpenAI API initialized with model: {self.openai_model}")
        else:
            self.client = None
            print("⚠️  OpenAI API key not found. Using mock classification mode.")
    
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
        """Real AI classification using OpenAI API"""
        try:
            # Prepare message content for AI analysis
            content = f"""Subject: {message.subject or 'No subject'}
From: {message.sender}
Channel: {message.channel.value}
Message: {message.snippet}
Received: {message.received_at}"""
            
            # Create AI prompt for classification
            system_prompt = """You are an AI assistant that classifies email and Slack messages into categories to help users prioritize their inbox.

Classify each message into ONE of these categories:
- "todo": Messages that require action, tasks to complete, assignments, requests that need response
- "followup": Messages that need follow-up, reminders, status updates, pending items
- "noise": Newsletters, promotions, automated notifications, spam, or informational messages that don't need action

Also assign a priority score from 1-10 where:
- 1-3: Low priority (newsletters, general info)
- 4-6: Medium priority (routine tasks, standard requests)
- 7-8: High priority (time-sensitive, important requests)
- 9-10: Urgent (immediate action needed, from executives, critical deadlines)

Consider these factors:
- Sender importance (CEO, boss, manager vs automated systems)
- Urgency indicators (URGENT, ASAP, deadline, due date)
- Action requirements (need to, must, please do, can you)
- Time sensitivity (tomorrow, today, by EOD)

Return your response as JSON with this exact format:
{
  "label": "todo|followup|noise",
  "priority": 1-10,
  "reasoning": "brief explanation"
}"""

            user_prompt = f"Classify this message:\n\n{content}"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=150
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            label_str = result.get("label", "noise")
            priority = int(result.get("priority", 5))
            
            # Validate and convert label
            try:
                label = ClassificationLabel(label_str)
            except ValueError:
                print(f"Invalid label from AI: {label_str}, defaulting to noise")
                label = ClassificationLabel.NOISE
            
            # Ensure priority is in valid range
            priority = max(1, min(10, priority))
            
            # Apply business rules to adjust priority
            final_priority = self._apply_business_rules(message, priority)
            
            return ClassificationRead(
                cls_id=uuid4(),
                msg_id=message.msg_id,
                label=label,
                priority=final_priority,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            print("Falling back to mock classification")
            return self._mock_classify_message(message)
    
