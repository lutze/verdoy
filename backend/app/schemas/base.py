"""
Base schemas for VerdoyLab API.

This module contains base Pydantic schemas that are shared
across all domains and functionality.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class BaseResponse(BaseModel):
    """Base response schema for all API responses."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response schema for API errors."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Base pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Base paginated response schema."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, per_page: int):
        """Create a paginated response."""
        pages = (total + per_page - 1) // per_page
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )


class TimeRangeParams(BaseModel):
    """Base time range parameters."""
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")


class SortParams(BaseModel):
    """Base sorting parameters."""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc/desc)")


class FilterParams(BaseModel):
    """Base filter parameters."""
    search: Optional[str] = Field(None, description="Search term")
    status: Optional[str] = Field(None, description="Filter by status")


class BaseCreateSchema(BaseModel):
    """Base schema for create operations."""
    pass


class BaseUpdateSchema(BaseModel):
    """Base schema for update operations."""
    pass


class BaseResponseSchema(BaseModel):
    """Base schema for response operations."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: str
    database: str
    uptime: Optional[float] = None


class SystemInfoResponse(BaseModel):
    """System information response schema."""
    version: str
    environment: str
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    features: List[str] = [] 