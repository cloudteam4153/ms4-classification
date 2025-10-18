from __future__ import annotations

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum

class TaskStatus(str, Enum):
    OPEN = "open"
    DONE = "done"

class TaskBase(BaseModel):
    """Base task model"""
    user_id: UUID = Field(..., description="User ID this task belongs to")
    source_message_id: Optional[UUID] = Field(None, description="Source message ID this task was created from")
    title: str = Field(..., description="Task title")
    status: TaskStatus = Field(TaskStatus.OPEN, description="Task status")
    due_date: Optional[date] = Field(None, description="Task due date")
    priority: int = Field(..., ge=1, le=10, description="Priority score from 1-10")
    description: Optional[str] = Field(None, description="Task description")

class TaskCreate(TaskBase):
    """Task creation payload"""
    pass

class TaskUpdate(BaseModel):
    """Task update payload"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    due_date: Optional[date] = None

class TaskRead(TaskBase):
    """Task as returned by the API"""
    task_id: UUID = Field(default_factory=UUID, description="Task ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When task was created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "source_message_id": "03f796db-509a-4018-ab69-1d479f7b3d92",
                "title": "Review project status update",
                "status": "open",
                "due_date": "2025-01-16",
                "priority": 8,
                "description": "Review and respond to the urgent project status request from boss@company.com",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    }

class TaskGenerationRequest(BaseModel):
    """Request to generate tasks from classifications"""
    classification_ids: List[UUID] = Field(..., description="List of classification IDs to generate tasks from")
    user_id: UUID = Field(..., description="User ID to assign tasks to")

class TaskGenerationResponse(BaseModel):
    """Response containing generated tasks"""
    tasks: List[TaskRead] = Field(..., description="List of generated tasks")
    total_generated: int = Field(..., description="Total number of tasks generated")
    success_count: int = Field(..., description="Number of successful task generations")
    error_count: int = Field(..., description="Number of failed task generations")

# Rebuild models to resolve forward references
TaskGenerationRequest.model_rebuild()
TaskGenerationResponse.model_rebuild()
