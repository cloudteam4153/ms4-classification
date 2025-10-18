from __future__ import annotations

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ChannelType(str, Enum):
    GMAIL = "gmail"
    SLACK = "slack"

class MessageBase(BaseModel):
    """Base message model for Gmail/Slack messages"""
    external_id: str = Field(..., description="External message ID from Gmail/Slack")
    channel: ChannelType = Field(..., description="Message channel (gmail or slack)")
    sender: str = Field(..., description="Sender email or Slack user")
    subject: Optional[str] = Field(None, description="Message subject (for emails)")
    snippet: str = Field(..., description="Message content snippet")
    received_at: datetime = Field(..., description="When the message was received")
    raw_ref: Optional[str] = Field(None, description="Reference to raw message data")
    priority: Optional[int] = Field(None, description="Priority score (1-10)")

class MessageCreate(MessageBase):
    """Message creation payload"""
    account_id: UUID = Field(..., description="Account ID this message belongs to")

class MessageRead(MessageBase):
    """Message as returned by the API"""
    msg_id: UUID = Field(default_factory=UUID, description="Internal message ID")
    account_id: UUID = Field(..., description="Account ID this message belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When message was stored")

    model_config = {
        "json_schema_extra": {
            "example": {
                "msg_id": "550e8400-e29b-41d4-a716-446655440000",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "external_id": "gmail_msg_123",
                "channel": "gmail",
                "sender": "john.doe@example.com",
                "subject": "Project Update - Due Tomorrow",
                "snippet": "Hi team, I need to discuss the project status. Can we meet tomorrow?",
                "received_at": "2025-01-15T10:30:00Z",
                "raw_ref": "gmail://thread/123",
                "priority": 8,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    }
