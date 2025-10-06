"""
Organization schemas for VerdoyLab API.

This module contains Pydantic schemas for organization management,
membership, and settings.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams


class OrganizationStatus(str, Enum):
    """Organization status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    PENDING = "pending"


class OrganizationType(str, Enum):
    """Organization type enumeration."""
    ENTERPRISE = "enterprise"
    SMALL_BUSINESS = "small_business"
    STARTUP = "startup"
    EDUCATIONAL = "educational"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    INDIVIDUAL = "individual"


class OrganizationCreate(BaseModel):
    """Schema for organization creation."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    organization_type: OrganizationType = Field(OrganizationType.SMALL_BUSINESS, description="Organization type")
    website: Optional[str] = Field(None, description="Organization website")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[str] = Field(None, description="Organization address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    timezone: str = Field("UTC", description="Timezone")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate organization name."""
        if not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()
    
    @validator('website')
    def validate_website(cls, v):
        """Validate website URL."""
        if v is not None and v.strip():
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError('Invalid website URL format')
        return v.strip() if v and v.strip() else None


class OrganizationUpdate(BaseModel):
    """Schema for organization updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    organization_type: Optional[OrganizationType] = Field(None, description="Organization type")
    website: Optional[str] = Field(None, description="Organization website")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[str] = Field(None, description="Organization address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    timezone: Optional[str] = Field(None, description="Timezone")
    status: Optional[OrganizationStatus] = Field(None, description="Organization status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate organization name."""
        if v is not None and not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip() if v is not None else v
    
    @validator('website')
    def validate_website(cls, v):
        """Validate website URL."""
        if v is not None and v.strip():
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError('Invalid website URL format')
        return v.strip() if v and v.strip() else None


class OrganizationResponse(BaseResponseSchema):
    """Schema for organization response."""
    name: str = Field(..., description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    organization_type: str = Field(..., description="Organization type")
    status: str = Field(..., description="Organization status")
    website: Optional[str] = Field(None, description="Organization website")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[str] = Field(None, description="Organization address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    timezone: str = Field(..., description="Timezone")
    settings: Dict[str, Any] = Field(..., description="Organization settings")
    member_count: int = Field(0, description="Number of members")
    device_count: int = Field(0, description="Number of devices")
    properties: Dict[str, Any] = Field(..., description="Organization properties")


class OrganizationListResponse(BaseModel):
    """Schema for organization list response."""
    organizations: List[OrganizationResponse] = Field(..., description="List of organizations")
    total: int = Field(..., description="Total number of organizations")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class OrganizationQueryParams(PaginationParams):
    """Schema for organization query parameters."""
    search: Optional[str] = Field(None, description="Search term")
    organization_type: Optional[OrganizationType] = Field(None, description="Filter by organization type")
    status: Optional[OrganizationStatus] = Field(None, description="Filter by status")
    country: Optional[str] = Field(None, description="Filter by country")
    timezone: Optional[str] = Field(None, description="Filter by timezone")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class OrganizationMemberCreate(BaseModel):
    """Schema for organization member creation."""
    user_id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    role: str = Field("member", description="Member role")
    permissions: Optional[List[str]] = Field(default_factory=list, description="Member permissions")
    is_active: bool = Field(True, description="Whether member is active")


class OrganizationMemberUpdate(BaseModel):
    """Schema for organization member updates."""
    role: Optional[str] = Field(None, description="Member role")
    permissions: Optional[List[str]] = Field(None, description="Member permissions")
    is_active: Optional[bool] = Field(None, description="Whether member is active")


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response."""
    id: UUID = Field(..., description="Member ID")
    user_id: UUID = Field(..., description="User ID")
    organization_id: UUID = Field(..., description="Organization ID")
    role: str = Field(..., description="Member role")
    permissions: List[str] = Field(..., description="Member permissions")
    is_active: bool = Field(..., description="Whether member is active")
    joined_at: datetime = Field(..., description="Join date")
    user_name: str = Field(..., description="User name")
    user_email: str = Field(..., description="User email")
    
    class Config:
        from_attributes = True


class OrganizationMemberListResponse(BaseModel):
    """Schema for organization member list response."""
    members: List[OrganizationMemberResponse] = Field(..., description="List of members")
    total: int = Field(..., description="Total number of members")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class OrganizationStatsResponse(BaseModel):
    """Schema for organization statistics response."""
    organization_id: UUID = Field(..., description="Organization ID")
    total_members: int = Field(..., description="Total number of members")
    active_members: int = Field(..., description="Number of active members")
    total_devices: int = Field(..., description="Total number of devices")
    online_devices: int = Field(..., description="Number of online devices")
    total_readings: int = Field(..., description="Total number of readings")
    total_alerts: int = Field(..., description="Total number of alerts")
    active_alerts: int = Field(..., description="Number of active alerts")
    data_usage_gb: float = Field(..., description="Data usage in GB")
    storage_usage_gb: float = Field(..., description="Storage usage in GB")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


class OrganizationSettingsUpdate(BaseModel):
    """Schema for organization settings updates."""
    data_retention_days: Optional[int] = Field(None, ge=1, le=3650, description="Data retention period in days")
    max_devices: Optional[int] = Field(None, ge=1, description="Maximum number of devices")
    max_members: Optional[int] = Field(None, ge=1, description="Maximum number of members")
    alert_notifications: Optional[bool] = Field(None, description="Enable alert notifications")
    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    sms_notifications: Optional[bool] = Field(None, description="Enable SMS notifications")
    webhook_notifications: Optional[bool] = Field(None, description="Enable webhook notifications")
    default_timezone: Optional[str] = Field(None, description="Default timezone")
    data_export_enabled: Optional[bool] = Field(None, description="Enable data export")
    api_rate_limit: Optional[int] = Field(None, ge=100, description="API rate limit per hour")
    
    @validator('data_retention_days')
    def validate_data_retention(cls, v):
        """Validate data retention period."""
        if v is not None and v < 1:
            raise ValueError('Data retention must be at least 1 day')
        if v is not None and v > 3650:  # 10 years
            raise ValueError('Data retention cannot exceed 10 years')
        return v


class OrganizationInviteCreate(BaseModel):
    """Schema for organization invitation creation."""
    email: EmailStr = Field(..., description="Invitee email address")
    organization_id: UUID = Field(..., description="Organization ID")
    role: str = Field("member", description="Invited role")
    permissions: Optional[List[str]] = Field(default_factory=list, description="Invited permissions")
    message: Optional[str] = Field(None, max_length=500, description="Invitation message")
    expires_in_days: int = Field(7, ge=1, le=30, description="Invitation expiration in days")


class OrganizationInviteResponse(BaseModel):
    """Schema for organization invitation response."""
    id: UUID = Field(..., description="Invitation ID")
    email: str = Field(..., description="Invitee email address")
    organization_id: UUID = Field(..., description="Organization ID")
    role: str = Field(..., description="Invited role")
    permissions: List[str] = Field(..., description="Invited permissions")
    status: str = Field(..., description="Invitation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    organization_name: str = Field(..., description="Organization name")
    
    class Config:
        from_attributes = True 