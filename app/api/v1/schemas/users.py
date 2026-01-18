"""
User request/response schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """User data for API responses."""
    id: str
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """User profile update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None


class PasswordUpdateRequest(BaseModel):
    """Password update request."""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class AdminUserUpdateRequest(BaseModel):
    """Admin user update (includes role)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
