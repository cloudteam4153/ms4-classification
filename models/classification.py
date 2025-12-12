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
    """Request to classify new messages for a user"""
    user_id: str = Field(..., description="User ID - required. Only new messages will be classified.")

class ClassificationResponse(BaseModel):
    """Response containing classification results"""
    classifications: List[ClassificationRead] = Field(..., description="List of classifications")
    total_processed: int = Field(..., description="Total number of messages processed")
    success_count: int = Field(..., description="Number of successful classifications")
    error_count: int = Field(..., description="Number of failed classifications")
