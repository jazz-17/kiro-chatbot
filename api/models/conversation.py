from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from .base import BaseEntity


class Message(BaseEntity):
    """Message model for chat messages"""
    conversation_id: UUID
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="meta_data")


class Conversation(BaseEntity):
    """Conversation model for chat sessions"""
    user_id: UUID
    title: str
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="meta_data")
    messages: List[Message] = Field(default_factory=list)


class ConversationCreate(BaseModel):
    """Schema for conversation creation"""
    title: str
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    """Schema for message creation"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: UUID
    user_id: UUID
    title: str
    provider: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[Message] = Field(default_factory=list)

    class Config:
        from_attributes = True