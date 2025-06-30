"""
User schemas for LMS Core API.

This module contains Pydantic schemas for user authentication,
registration, and profile management.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseResponseSchema


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    name: str = Field(..., description="User full name")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    name: Optional[str] = Field(None, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_active: Optional[bool] = Field(None, description="User active status")


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetRequest(BaseModel):
    """Schema for password reset request (alias for PasswordReset)."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Token expiration time in seconds")
    user_id: UUID = Field(..., description="User ID")


class TokenRefresh(BaseModel):
    """Schema for token refresh."""
    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseResponseSchema):
    """Schema for user response."""
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_active: bool = Field(..., description="User active status")
    is_superuser: bool = Field(False, description="User admin status")
    entity_id: UUID = Field(..., description="Associated entity ID")


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_active: bool = Field(..., description="User active status")
    is_superuser: bool = Field(False, description="User admin status")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class UserQueryParams(BaseModel):
    """Schema for user query parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization") 