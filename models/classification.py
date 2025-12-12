from __future__ import annotations

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ClassificationLabel(str, Enum):
    TODO = "todo"
    FOLLOWUP = "followup"
    NOISE = "noise"

class ClassificationBase(BaseModel):
    """Base classification model"""
    msg_id: UUID = Field(..., description="Message ID being classified")
    user_id: Optional[str] = Field(None, description="User ID for filtering")
    label: ClassificationLabel = Field(..., description="Classification label")
    priority: int = Field(..., ge=1, le=10, description="Priority score from 1-10")

class ClassificationCreate(ClassificationBase):
    """Classification creation payload"""
    pass

class ClassificationUpdate(BaseModel):
    """Classification update payload"""
    label: Optional[ClassificationLabel] = None
    priority: Optional[int] = Field(None, ge=1, le=10)

class ClassificationRead(ClassificationBase):
    """Classification as returned by the API"""
    cls_id: UUID = Field(default_factory=UUID, description="Classification ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When classification was created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "cls_id": "550e8400-e29b-41d4-a716-446655440000",
                "msg_id": "123e4567-e89b-12d3-a456-426614174000",
                "label": "todo",
                "priority": 8,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    }

class ClassificationRequest(BaseModel):
    """Request to classify multiple messages"""
    message_ids: Optional[List[UUID]] = Field(None, description="List of message IDs to classify")
    user_id: Optional[str] = Field(None, description="User ID to fetch and classify all their messages")
    
    def model_post_init(self, __context):
        """Validate that either message_ids or user_id is provided"""
        if not self.message_ids and not self.user_id:
            from pydantic import ValidationError
            raise ValueError("Either 'message_ids' or 'user_id' must be provided")

class ClassificationResponse(BaseModel):
    """Response containing classification results"""
    classifications: List[ClassificationRead] = Field(..., description="List of classifications")
    total_processed: int = Field(..., description="Total number of messages processed")
    success_count: int = Field(..., description="Number of successful classifications")
    error_count: int = Field(..., description="Number of failed classifications")
