"""
Project schemas for API request/response validation.

This module contains Pydantic models for project management operations:
- ProjectCreate: For creating new projects
- ProjectUpdate: For updating existing projects  
- ProjectResponse: For API responses
- ProjectListResponse: For list endpoints
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectPriority(str, Enum):
    """Project priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Project priority")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    expected_completion: Optional[date] = Field(None, description="Expected completion date")
    budget: Optional[str] = Field(None, max_length=100, description="Project budget")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress percentage (0-100)")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    project_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Project settings")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v

    @validator('expected_completion')
    def validate_expected_completion(cls, v, values):
        """Validate expected completion is reasonable."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('Expected completion must be after start date')
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    organization_id: UUID = Field(..., description="Organization ID")
    project_lead_id: Optional[UUID] = Field(None, description="Project lead user ID")

    class Config:
        schema_extra = {
            "example": {
                "name": "pH Optimization Study",
                "description": "Research project to optimize pH levels for maximum yield",
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "priority": "high",
                "start_date": "2024-01-15",
                "expected_completion": "2024-06-30",
                "budget": "$50,000",
                "tags": ["optimization", "pH", "yield"],
                "project_lead_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    status: Optional[ProjectStatus] = Field(None, description="Project status")
    priority: Optional[ProjectPriority] = Field(None, description="Project priority")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    expected_completion: Optional[date] = Field(None, description="Expected completion date")
    actual_completion: Optional[date] = Field(None, description="Actual completion date")
    project_lead_id: Optional[UUID] = Field(None, description="Project lead user ID")
    budget: Optional[str] = Field(None, max_length=100, description="Project budget")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    tags: Optional[List[str]] = Field(None, description="Project tags")
    project_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    settings: Optional[Dict[str, Any]] = Field(None, description="Project settings")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date."""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "pH Optimization Study - Phase 2",
                "description": "Extended research project to optimize pH levels for maximum yield",
                "status": "active",
                "priority": "high",
                "progress_percentage": 45,
                "expected_completion": "2024-08-30"
            }
        }


class ProjectResponse(BaseModel):
    """Schema for project API responses."""
    id: UUID
    name: str
    description: Optional[str]
    organization_id: UUID
    status: ProjectStatus
    priority: ProjectPriority
    start_date: Optional[date]
    end_date: Optional[date]
    expected_completion: Optional[date]
    actual_completion: Optional[date]
    project_lead_id: Optional[UUID]
    budget: Optional[str]
    progress_percentage: int
    tags: List[str]
    project_metadata: Dict[str, Any]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_completed: bool
    is_overdue: bool

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "pH Optimization Study",
                "description": "Research project to optimize pH levels for maximum yield",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "active",
                "priority": "high",
                "start_date": "2024-01-15",
                "expected_completion": "2024-06-30",
                "project_lead_id": "550e8400-e29b-41d4-a716-446655440002",
                "budget": "$50,000",
                "progress_percentage": 25,
                "tags": ["optimization", "pH", "yield"],
                "project_metadata": {"source": "research", "type": "pH optimization"},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:15:00Z",
                "is_active": True,
                "is_completed": False,
                "is_overdue": False
            }
        }


class ProjectListResponse(BaseModel):
    """Schema for project list API responses."""
    projects: List[ProjectResponse]
    total: int
    page: int
    per_page: int
    
    class Config:
        schema_extra = {
            "example": {
                "projects": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "pH Optimization Study",
                        "status": "active",
                        "priority": "high",
                        "progress_percentage": 25
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
        }


class ProjectSummary(BaseModel):
    """Schema for project summary information."""
    id: UUID
    name: str
    status: ProjectStatus
    priority: ProjectPriority
    progress_percentage: int
    start_date: Optional[date]
    expected_completion: Optional[date]
    is_overdue: bool
    
    class Config:
        from_attributes = True


class ProjectStatistics(BaseModel):
    """Schema for project statistics."""
    total_projects: int
    active_projects: int
    completed_projects: int
    overdue_projects: int
    on_hold_projects: int
    average_progress: float
    
    class Config:
        schema_extra = {
            "example": {
                "total_projects": 25,
                "active_projects": 18,
                "completed_projects": 5,
                "overdue_projects": 2,
                "on_hold_projects": 0,
                "average_progress": 67.5
            }
        } 