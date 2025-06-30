"""
Command schemas for LMS Core API.

This module contains Pydantic schemas for device command management,
execution tracking, and command history.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams, TimeRangeParams


class CommandStatus(str, Enum):
    """Command status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CommandType(str, Enum):
    """Command type enumeration."""
    RESTART = "restart"
    UPDATE_FIRMWARE = "update_firmware"
    UPDATE_CONFIG = "update_config"
    RESET = "reset"
    CALIBRATE = "calibrate"
    READ_SENSOR = "read_sensor"
    SET_ALERT = "set_alert"
    CUSTOM = "custom"


class CommandPriority(str, Enum):
    """Command priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CommandCreate(BaseModel):
    """Schema for command creation."""
    device_id: UUID = Field(..., description="Device ID")
    command_type: CommandType = Field(..., description="Command type")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Command parameters")
    timeout_seconds: int = Field(300, ge=30, le=3600, description="Command timeout in seconds")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    retry_count: int = Field(0, ge=0, le=5, description="Number of retries")
    retry_delay_seconds: int = Field(60, ge=10, le=3600, description="Delay between retries in seconds")
    description: Optional[str] = Field(None, max_length=500, description="Command description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Validate command timeout."""
        if v < 30:
            raise ValueError('Timeout must be at least 30 seconds')
        if v > 3600:  # 1 hour
            raise ValueError('Timeout cannot exceed 1 hour')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        """Validate retry count."""
        if v < 0:
            raise ValueError('Retry count cannot be negative')
        if v > 5:
            raise ValueError('Retry count cannot exceed 5')
        return v
    
    @validator('retry_delay_seconds')
    def validate_retry_delay(cls, v):
        """Validate retry delay."""
        if v < 10:
            raise ValueError('Retry delay must be at least 10 seconds')
        if v > 3600:  # 1 hour
            raise ValueError('Retry delay cannot exceed 1 hour')
        return v
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """Validate scheduled execution time."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class CommandUpdate(BaseModel):
    """Schema for command updates."""
    status: Optional[CommandStatus] = Field(None, description="Command status")
    result: Optional[Dict[str, Any]] = Field(None, description="Command result")
    error_message: Optional[str] = Field(None, description="Error message")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Execution time in milliseconds")
    retry_attempt: Optional[int] = Field(None, ge=0, description="Current retry attempt")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CommandResponse(BaseResponseSchema):
    """Schema for command response."""
    device_id: UUID = Field(..., description="Device ID")
    command_type: str = Field(..., description="Command type")
    priority: str = Field(..., description="Command priority")
    status: str = Field(..., description="Command status")
    parameters: Dict[str, Any] = Field(..., description="Command parameters")
    timeout_seconds: int = Field(..., description="Command timeout in seconds")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    retry_count: int = Field(..., description="Number of retries")
    retry_delay_seconds: int = Field(..., description="Delay between retries in seconds")
    description: Optional[str] = Field(None, description="Command description")
    result: Optional[Dict[str, Any]] = Field(None, description="Command result")
    error_message: Optional[str] = Field(None, description="Error message")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    retry_attempt: Optional[int] = Field(None, description="Current retry attempt")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    event_id: UUID = Field(..., description="Associated event ID")


class CommandListResponse(BaseModel):
    """Schema for command list response."""
    commands: List[CommandResponse] = Field(..., description="List of commands")
    total: int = Field(..., description="Total number of commands")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class CommandQueryParams(PaginationParams, TimeRangeParams):
    """Schema for command query parameters."""
    device_id: Optional[UUID] = Field(None, description="Filter by device ID")
    command_type: Optional[CommandType] = Field(None, description="Filter by command type")
    status: Optional[CommandStatus] = Field(None, description="Filter by status")
    priority: Optional[CommandPriority] = Field(None, description="Filter by priority")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    scheduled: Optional[bool] = Field(None, description="Filter by scheduled commands")
    failed: Optional[bool] = Field(None, description="Filter by failed commands")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class CommandBulkCreate(BaseModel):
    """Schema for bulk command creation."""
    device_ids: List[UUID] = Field(..., description="List of device IDs")
    command_type: CommandType = Field(..., description="Command type")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Command priority")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Command parameters")
    timeout_seconds: int = Field(300, ge=30, le=3600, description="Command timeout in seconds")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    retry_count: int = Field(0, ge=0, le=5, description="Number of retries")
    retry_delay_seconds: int = Field(60, ge=10, le=3600, description="Delay between retries in seconds")
    description: Optional[str] = Field(None, max_length=500, description="Command description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @validator('device_ids')
    def validate_device_ids(cls, v):
        """Validate device IDs list."""
        if not v:
            raise ValueError('At least one device ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 devices can be targeted at once')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Validate command timeout."""
        if v < 30:
            raise ValueError('Timeout must be at least 30 seconds')
        if v > 3600:  # 1 hour
            raise ValueError('Timeout cannot exceed 1 hour')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        """Validate retry count."""
        if v < 0:
            raise ValueError('Retry count cannot be negative')
        if v > 5:
            raise ValueError('Retry count cannot exceed 5')
        return v
    
    @validator('retry_delay_seconds')
    def validate_retry_delay(cls, v):
        """Validate retry delay."""
        if v < 10:
            raise ValueError('Retry delay must be at least 10 seconds')
        if v > 3600:  # 1 hour
            raise ValueError('Retry delay cannot exceed 1 hour')
        return v
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """Validate scheduled execution time."""
        if v is not None and v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class CommandBulkResponse(BaseModel):
    """Schema for bulk command response."""
    total_commands: int = Field(..., description="Total number of commands created")
    successful_commands: int = Field(..., description="Number of successfully created commands")
    failed_commands: int = Field(..., description="Number of failed command creations")
    command_ids: List[UUID] = Field(..., description="List of created command IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Creation errors")


class CommandStatsResponse(BaseModel):
    """Schema for command statistics response."""
    device_id: Optional[UUID] = Field(None, description="Device ID")
    total_commands: int = Field(..., description="Total number of commands")
    pending_commands: int = Field(..., description="Number of pending commands")
    completed_commands: int = Field(..., description="Number of completed commands")
    failed_commands: int = Field(..., description="Number of failed commands")
    cancelled_commands: int = Field(..., description="Number of cancelled commands")
    avg_execution_time_ms: float = Field(..., description="Average execution time in milliseconds")
    success_rate: float = Field(..., description="Command success rate")
    command_type_distribution: Dict[str, int] = Field(..., description="Command type distribution")
    priority_distribution: Dict[str, int] = Field(..., description="Priority distribution")
    time_period: str = Field(..., description="Time period for statistics")


class CommandTemplateCreate(BaseModel):
    """Schema for command template creation."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    command_type: CommandType = Field(..., description="Command type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    timeout_seconds: int = Field(300, ge=30, le=3600, description="Default timeout in seconds")
    retry_count: int = Field(0, ge=0, le=5, description="Default retry count")
    retry_delay_seconds: int = Field(60, ge=10, le=3600, description="Default retry delay in seconds")
    priority: CommandPriority = Field(CommandPriority.NORMAL, description="Default priority")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_public: bool = Field(False, description="Whether template is public")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate template name."""
        if not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()


class CommandTemplateResponse(BaseResponseSchema):
    """Schema for command template response."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    command_type: str = Field(..., description="Command type")
    parameters: Dict[str, Any] = Field(..., description="Default parameters")
    timeout_seconds: int = Field(..., description="Default timeout in seconds")
    retry_count: int = Field(..., description="Default retry count")
    retry_delay_seconds: int = Field(..., description="Default retry delay in seconds")
    priority: str = Field(..., description="Default priority")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_public: bool = Field(..., description="Whether template is public")
    usage_count: int = Field(0, description="Number of times template was used")
    properties: Dict[str, Any] = Field(..., description="Template properties")


class CommandTemplateListResponse(BaseModel):
    """Schema for command template list response."""
    templates: List[CommandTemplateResponse] = Field(..., description="List of command templates")
    total: int = Field(..., description="Total number of templates")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class CommandCancelRequest(BaseModel):
    """Schema for command cancellation request."""
    command_ids: List[UUID] = Field(..., description="List of command IDs to cancel")
    reason: Optional[str] = Field(None, max_length=200, description="Cancellation reason")
    
    @validator('command_ids')
    def validate_command_ids(cls, v):
        """Validate command IDs list."""
        if not v:
            raise ValueError('At least one command ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 commands can be cancelled at once')
        return v


class CommandRetryRequest(BaseModel):
    """Schema for command retry request."""
    command_ids: List[UUID] = Field(..., description="List of command IDs to retry")
    reset_retry_count: bool = Field(False, description="Reset retry count")
    new_timeout: Optional[int] = Field(None, ge=30, le=3600, description="New timeout in seconds")
    
    @validator('command_ids')
    def validate_command_ids(cls, v):
        """Validate command IDs list."""
        if not v:
            raise ValueError('At least one command ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 commands can be retried at once')
        return v


class CommandExecutionResponse(BaseModel):
    """Schema for command execution response."""
    command_id: UUID = Field(..., description="Command ID")
    device_id: UUID = Field(..., description="Device ID")
    status: str = Field(..., description="Execution status (pending, executed, failed, etc.)")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    result: Optional[str] = Field(None, description="Result or output of the command")
    error: Optional[str] = Field(None, description="Error message if failed") 