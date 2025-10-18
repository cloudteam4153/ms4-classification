from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta

from models.task import TaskRead, TaskCreate, TaskStatus, TaskGenerationRequest, TaskGenerationResponse
from models.classification import ClassificationRead, ClassificationLabel
from models.message import MessageRead

class TaskGenerator:
    """Service for generating tasks from classified messages"""
    
    def __init__(self):
        pass
    
    def generate_tasks_from_classifications(
        self, 
        classifications: List[ClassificationRead], 
        messages: List[MessageRead],
        request: TaskGenerationRequest
    ) -> TaskGenerationResponse:
        """
        Generate tasks from classifications
        
        Args:
            classifications: List of classifications to generate tasks from
            messages: List of messages (for context)
            request: Task generation request
            
        Returns:
            TaskGenerationResponse with generated tasks
        """
        tasks = []
        success_count = 0
        error_count = 0
        
        # Create a lookup for messages by ID
        message_map = {str(msg.msg_id): msg for msg in messages}
        
        for classification in classifications:
            try:
                # Find the corresponding message
                message = message_map.get(str(classification.msg_id))
                if not message:
                    raise ValueError(f"Message {classification.msg_id} not found")
                
                # Only generate tasks for TODO and FOLLOWUP classifications
                if classification.label in [ClassificationLabel.TODO, ClassificationLabel.FOLLOWUP]:
                    task = self._create_task_from_classification(classification, message, request.user_id)
                    tasks.append(task)
                    success_count += 1
                    
            except Exception as e:
                print(f"Error generating task for classification {classification.cls_id}: {e}")
                error_count += 1
        
        return TaskGenerationResponse(
            tasks=tasks,
            total_generated=len(classifications),
            success_count=success_count,
            error_count=error_count
        )
    
    def _create_task_from_classification(
        self, 
        classification: ClassificationRead, 
        message: MessageRead, 
        user_id: UUID
    ) -> TaskRead:
        """Create a task from a classification and message"""
        
        # Generate title from message subject or snippet
        title = self._generate_task_title(message)
        
        # Generate description
        description = self._generate_task_description(message, classification)
        
        # Determine due date
        due_date = self._determine_due_date(classification, message)
        
        return TaskRead(
            task_id=uuid4(),
            user_id=user_id,
            source_message_id=message.msg_id,
            title=title,
            status=TaskStatus.OPEN,
            due_date=due_date,
            priority=classification.priority,
            description=description,
            created_at=datetime.utcnow()
        )
    
    def _generate_task_title(self, message: MessageRead) -> str:
        """Generate a task title from the message"""
        if message.subject:
            return message.subject
        elif message.snippet:
            # Use first 50 characters of snippet as title
            return message.snippet[:50] + "..." if len(message.snippet) > 50 else message.snippet
        else:
            return f"Task from {message.sender}"
    
    def _generate_task_description(self, message: MessageRead, classification: ClassificationRead) -> str:
        """Generate a task description"""
        description_parts = []
        
        if message.subject:
            description_parts.append(f"Subject: {message.subject}")
        
        description_parts.append(f"From: {message.sender}")
        description_parts.append(f"Channel: {message.channel.value}")
        description_parts.append(f"Received: {message.received_at.strftime('%Y-%m-%d %H:%M')}")
        
        if message.snippet:
            description_parts.append(f"\nMessage:\n{message.snippet}")
        
        description_parts.append(f"\nClassification: {classification.label.value} (Priority: {classification.priority})")
        
        return "\n".join(description_parts)
    
    def _determine_due_date(self, classification: ClassificationRead, message: MessageRead) -> Optional[date]:
        """Determine due date based on classification and message content"""
        content = f"{message.subject or ''} {message.snippet}".lower()
        
        # Check for specific due date mentions
        if "eod today" in content or "end of day today" in content:
            return date.today()
        elif "eod tomorrow" in content or "tomorrow" in content or "by tomorrow" in content:
            return date.today() + timedelta(days=1)
        elif "this week" in content:
            # Friday of current week
            days_until_friday = (4 - date.today().weekday() + 7) % 7
            return date.today() + timedelta(days=days_until_friday)
        elif "next week" in content:
            # Friday of next week
            days_until_friday = (4 - date.today().weekday() + 7) % 7
            return date.today() + timedelta(days=days_until_friday + 7)
        elif classification.label == ClassificationLabel.TODO and classification.priority >= 8:
            return date.today() + timedelta(days=1)  # High priority todos due tomorrow
        elif classification.label == ClassificationLabel.TODO:
            return date.today() + timedelta(days=3)  # Other todos due in 3 days
        elif classification.label == ClassificationLabel.FOLLOWUP:
            return date.today() + timedelta(days=5)  # Follow-ups due in 5 days
        
        return None