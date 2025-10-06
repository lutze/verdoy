"""
Experiment schemas for the VerdoyLab API.

This module defines Pydantic schemas for experiment data validation,
serialization, and API responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


class ExperimentStatus(str, Enum):
    """Experiment status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TrialStatus(str, Enum):
    """Trial status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    project_id: UUID = Field(..., description="Project ID")
    process_id: UUID = Field(..., description="Process ID")
    bioreactor_id: UUID = Field(..., description="Bioreactor ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Experiment parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Experiment metadata")
    total_trials: int = Field(default=1, ge=1, le=100, description="Total number of trials")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate experiment name."""
        if not v.strip():
            raise ValueError("Experiment name cannot be empty")
        return v.strip()
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate experiment parameters."""
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate experiment metadata."""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Experiment parameters")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Experiment metadata")
    total_trials: Optional[int] = Field(None, ge=1, le=100, description="Total number of trials")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate experiment name."""
        if v is not None and not v.strip():
            raise ValueError("Experiment name cannot be empty")
        return v.strip() if v else v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate experiment parameters."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate experiment metadata."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v


class ExperimentTrialCreate(BaseModel):
    """Schema for creating a new experiment trial."""
    
    trial_number: int = Field(..., ge=1, description="Trial number")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Trial-specific parameters")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate trial parameters."""
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v


class ExperimentTrialUpdate(BaseModel):
    """Schema for updating an experiment trial."""
    
    parameters: Optional[Dict[str, Any]] = Field(None, description="Trial-specific parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Trial results")
    error_message: Optional[str] = Field(None, description="Error message if trial failed")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate trial parameters."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v
    
    @validator('results')
    def validate_results(cls, v):
        """Validate trial results."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Results must be a dictionary")
        return v


class ExperimentTrialResponse(BaseModel):
    """Schema for experiment trial response."""
    
    id: UUID = Field(..., description="Trial ID")
    experiment_id: UUID = Field(..., description="Experiment ID")
    trial_number: int = Field(..., description="Trial number")
    status: TrialStatus = Field(..., description="Trial status")
    started_at: Optional[datetime] = Field(None, description="Trial start time")
    completed_at: Optional[datetime] = Field(None, description="Trial completion time")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Trial parameters")
    results: Dict[str, Any] = Field(default_factory=dict, description="Trial results")
    error_message: Optional[str] = Field(None, description="Error message")
    created_by: Optional[UUID] = Field(None, description="Creator ID")
    duration_minutes: Optional[int] = Field(None, description="Trial duration in minutes")
    
    class Config:
        from_attributes = True


class ExperimentResponse(BaseModel):
    """Schema for experiment response."""
    
    id: UUID = Field(..., description="Experiment ID")
    name: str = Field(..., description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    entity_type: str = Field(..., description="Entity type")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    status: ExperimentStatus = Field(..., description="Experiment status")
    project_id: Optional[UUID] = Field(None, description="Project ID")
    process_id: Optional[UUID] = Field(None, description="Process ID")
    bioreactor_id: Optional[UUID] = Field(None, description="Bioreactor ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Experiment parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Experiment metadata")
    current_trial: int = Field(..., description="Current trial number")
    total_trials: int = Field(..., description="Total number of trials")
    started_at: Optional[datetime] = Field(None, description="Experiment start time")
    completed_at: Optional[datetime] = Field(None, description="Experiment completion time")
    results: Dict[str, Any] = Field(default_factory=dict, description="Experiment results")
    error_message: Optional[str] = Field(None, description="Error message")
    duration_minutes: Optional[int] = Field(None, description="Experiment duration in minutes")
    progress_percentage: int = Field(..., description="Experiment progress percentage")
    is_running: bool = Field(..., description="Whether experiment is running")
    is_finished: bool = Field(..., description="Whether experiment is finished")
    can_start: bool = Field(..., description="Whether experiment can be started")
    can_pause: bool = Field(..., description="Whether experiment can be paused")
    can_resume: bool = Field(..., description="Whether experiment can be resumed")
    can_stop: bool = Field(..., description="Whether experiment can be stopped")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    is_active: bool = Field(..., description="Whether experiment is active")
    
    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """Schema for experiment list response."""
    
    experiments: List[ExperimentResponse] = Field(..., description="List of experiments")
    total_count: int = Field(..., description="Total number of experiments")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


class ExperimentStatsResponse(BaseModel):
    """Schema for experiment statistics response."""
    
    total_experiments: int = Field(..., description="Total number of experiments")
    active_experiments: int = Field(..., description="Number of active experiments")
    completed_experiments: int = Field(..., description="Number of completed experiments")
    failed_experiments: int = Field(..., description="Number of failed experiments")
    draft_experiments: int = Field(..., description="Number of draft experiments")
    archived_experiments: int = Field(..., description="Number of archived experiments")
    total_trials: int = Field(..., description="Total number of trials")
    running_trials: int = Field(..., description="Number of running trials")


class ExperimentControlRequest(BaseModel):
    """Schema for experiment control requests."""
    
    action: str = Field(..., description="Control action (start, pause, resume, stop, complete, fail)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action-specific parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Results for completion")
    error_message: Optional[str] = Field(None, description="Error message for failure")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate control action."""
        valid_actions = ['start', 'pause', 'resume', 'stop', 'complete', 'fail']
        if v not in valid_actions:
            raise ValueError(f"Invalid action: {v}. Must be one of {valid_actions}")
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate parameters."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v
    
    @validator('results')
    def validate_results(cls, v):
        """Validate results."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Results must be a dictionary")
        return v


class ExperimentControlResponse(BaseModel):
    """Schema for experiment control response."""
    
    success: bool = Field(..., description="Whether control action was successful")
    message: str = Field(..., description="Response message")
    experiment: Optional[ExperimentResponse] = Field(None, description="Updated experiment data")
    error: Optional[str] = Field(None, description="Error message if failed")


class ExperimentFilterRequest(BaseModel):
    """Schema for experiment filtering."""
    
    status: Optional[ExperimentStatus] = Field(None, description="Filter by status")
    project_id: Optional[UUID] = Field(None, description="Filter by project ID")
    process_id: Optional[UUID] = Field(None, description="Filter by process ID")
    bioreactor_id: Optional[UUID] = Field(None, description="Filter by bioreactor ID")
    search: Optional[str] = Field(None, description="Search term for name/description")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    
    @validator('search')
    def validate_search(cls, v):
        """Validate search term."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else v 