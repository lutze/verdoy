"""
Pydantic schemas for LMS Core API.

This package contains all Pydantic schemas for request/response validation,
organized by domain and functionality.
"""

from .base import BaseResponse, ErrorResponse, PaginationParams
from .user import UserCreate, UserLogin, TokenResponse, UserResponse
from .device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse,
    DeviceStatusUpdate, DeviceHealthResponse, DeviceApiKey,
    DeviceQueryParams, DeviceStatus, EntityType
)
from .reading import (
    SensorReading, DeviceReadingsRequest, ReadingResponse,
    ReadingQueryParams
)
from .alert import (
    AlertCreate, AlertUpdate, AlertResponse, AlertListResponse,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertQueryParams
)
from .organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationListResponse
)
from .billing import (
    BillingCreate, BillingResponse, BillingListResponse,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
)
from .command import (
    CommandCreate, CommandUpdate, CommandResponse, CommandListResponse,
    CommandQueryParams
)

__all__ = [
    # Base schemas
    "BaseResponse",
    "ErrorResponse", 
    "PaginationParams",
    
    # User schemas
    "UserCreate",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    
    # Device schemas
    "DeviceCreate",
    "DeviceUpdate", 
    "DeviceResponse",
    "DeviceListResponse",
    "DeviceStatusUpdate",
    "DeviceHealthResponse",
    "DeviceApiKey",
    "DeviceQueryParams",
    "DeviceStatus",
    "EntityType",
    
    # Reading schemas
    "SensorReading",
    "DeviceReadingsRequest",
    "ReadingResponse",
    "ReadingQueryParams",
    
    # Alert schemas
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse", 
    "AlertListResponse",
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRuleResponse",
    "AlertQueryParams",
    
    # Organization schemas
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationListResponse",
    
    # Billing schemas
    "BillingCreate",
    "BillingResponse",
    "BillingListResponse",
    "SubscriptionCreate",
    "SubscriptionUpdate", 
    "SubscriptionResponse",
    
    # Command schemas
    "CommandCreate",
    "CommandUpdate",
    "CommandResponse",
    "CommandListResponse",
    "CommandQueryParams"
] 