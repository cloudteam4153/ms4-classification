from __future__ import annotations

from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field

class BriefItem(BaseModel):
    """Individual item in a daily brief"""
    classification_id: UUID = Field(..., description="Classification ID")
    message_id: UUID = Field(..., description="Message ID")
    title: str = Field(..., description="Brief item title")
    description: str = Field(..., description="Brief item description")
    priority_score: int = Field(..., ge=1, le=10, description="Priority score")
    channel: str = Field(..., description="Message channel (gmail/slack)")
    sender: str = Field(..., description="Message sender")
    received_at: datetime = Field(..., description="When message was received")
    extracted_tasks: Optional[List[str]] = Field(None, description="Tasks extracted from message")

class BriefBase(BaseModel):
    """Base daily brief model"""
    user_id: UUID = Field(..., description="User ID this brief belongs to")
    brief_date: date = Field(..., description="Date this brief covers")
    total_items: int = Field(..., description="Total number of items in brief")
    high_priority_count: int = Field(..., description="Number of high priority items")
    todo_count: int = Field(..., description="Number of todo items")
    followup_count: int = Field(..., description="Number of followup items")

class BriefCreate(BriefBase):
    """Brief creation payload"""
    items: List[BriefItem] = Field(..., description="Items in the brief")

class BriefRead(BriefBase):
    """Brief as returned by the API"""
    brief_id: UUID = Field(default_factory=UUID, description="Brief ID")
    items: List[BriefItem] = Field(..., description="Items in the brief")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When brief was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When brief was last updated")

    model_config = {
        "json_schema_extra": {
            "example": {
                "brief_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "brief_date": "2025-01-15",
                "total_items": 5,
                "high_priority_count": 2,
                "todo_count": 3,
                "followup_count": 2,
                "items": [
                    {
                        "classification_id": "111e1111-e11b-11d1-a111-111111111111",
                        "message_id": "222e2222-e22b-22d2-a222-222222222222",
                        "title": "Urgent: Project Deadline Tomorrow",
                        "description": "John needs project status update by EOD",
                        "priority_score": 9,
                        "channel": "gmail",
                        "sender": "john.doe@example.com",
                        "received_at": "2025-01-15T09:00:00Z",
                        "extracted_tasks": ["Update project status", "Send report to John"]
                    }
                ],
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }
    }

class BriefRequest(BaseModel):
    """Request to generate a daily brief"""
    user_id: UUID = Field(..., description="User ID to generate brief for")
    date: Optional[str] = Field(None, description="Date for brief (defaults to today) in YYYY-MM-DD format")
    max_items: Optional[int] = Field(50, description="Maximum number of items to include")
