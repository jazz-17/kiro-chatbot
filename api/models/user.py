from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from .base import BaseEntity


class User(BaseEntity):
    """User model for authentication and session management"""
    email: EmailStr
    password_hash: str
    encrypted_api_keys: Optional[Dict[str, str]] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for user creation"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)"""
    id: UUID
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True