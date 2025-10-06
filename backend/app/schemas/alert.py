"""
Alert schemas for VerdoyLab API.

This module contains Pydantic schemas for alert management,
alert rules, and notification handling.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams, TimeRangeParams


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertType(str, Enum):
    """Alert type enumeration."""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    DEVICE_OFFLINE = "device_offline"
    BATTERY_LOW = "battery_low"
    SENSOR_ERROR = "sensor_error"
    DATA_QUALITY = "data_quality"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    """Notification type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"


class AlertRuleCreate(BaseModel):
    """Schema for alert rule creation."""
    name: str = Field(..., description="Alert rule name")
    description: Optional[str] = Field(None, description="Alert rule description")
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type to monitor")
    condition: str = Field(..., description="Alert condition (gt, lt, eq, ne, between)")
    threshold_value: float = Field(..., description="Threshold value")
    threshold_value_high: Optional[float] = Field(None, description="High threshold for range conditions")
    severity: AlertSeverity = Field(AlertSeverity.MEDIUM, description="Alert severity")
    alert_type: AlertType = Field(AlertType.THRESHOLD_EXCEEDED, description="Alert type")
    enabled: bool = Field(True, description="Whether rule is enabled")
    cooldown_minutes: int = Field(5, ge=1, description="Cooldown period in minutes")
    notification_channels: List[NotificationType] = Field(default_factory=list, description="Notification channels")
    notification_recipients: List[str] = Field(default_factory=list, description="Notification recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate alert condition."""
        valid_conditions = ['gt', 'lt', 'gte', 'lte', 'eq', 'ne', 'between', 'outside']
        if v not in valid_conditions:
            raise ValueError(f'Invalid condition: {v}. Must be one of {valid_conditions}')
        return v
    
    @validator('threshold_value_high')
    def validate_threshold_range(cls, v, values):
        """Validate threshold range for between/outside conditions."""
        condition = values.get('condition')
        if condition in ['between', 'outside'] and v is None:
            raise ValueError('threshold_value_high is required for between/outside conditions')
        if condition in ['between', 'outside'] and v is not None:
            threshold_value = values.get('threshold_value')
            if threshold_value is not None and v <= threshold_value:
                raise ValueError('threshold_value_high must be greater than threshold_value')
        return v
    
    @validator('cooldown_minutes')
    def validate_cooldown(cls, v):
        """Validate cooldown period."""
        if v < 1:
            raise ValueError('Cooldown must be at least 1 minute')
        if v > 1440:  # 24 hours
            raise ValueError('Cooldown cannot exceed 24 hours')
        return v


class AlertRuleUpdate(BaseModel):
    """Schema for alert rule updates."""
    name: Optional[str] = Field(None, description="Alert rule name")
    description: Optional[str] = Field(None, description="Alert rule description")
    condition: Optional[str] = Field(None, description="Alert condition")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    threshold_value_high: Optional[float] = Field(None, description="High threshold for range conditions")
    severity: Optional[AlertSeverity] = Field(None, description="Alert severity")
    enabled: Optional[bool] = Field(None, description="Whether rule is enabled")
    cooldown_minutes: Optional[int] = Field(None, ge=1, description="Cooldown period in minutes")
    notification_channels: Optional[List[NotificationType]] = Field(None, description="Notification channels")
    notification_recipients: Optional[List[str]] = Field(None, description="Notification recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate alert condition."""
        if v is not None:
            valid_conditions = ['gt', 'lt', 'gte', 'lte', 'eq', 'ne', 'between', 'outside']
            if v not in valid_conditions:
                raise ValueError(f'Invalid condition: {v}. Must be one of {valid_conditions}')
        return v


class AlertRuleResponse(BaseResponseSchema):
    """Schema for alert rule response."""
    name: str = Field(..., description="Alert rule name")
    description: Optional[str] = Field(None, description="Alert rule description")
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type to monitor")
    condition: str = Field(..., description="Alert condition")
    threshold_value: float = Field(..., description="Threshold value")
    threshold_value_high: Optional[float] = Field(None, description="High threshold for range conditions")
    severity: str = Field(..., description="Alert severity")
    alert_type: str = Field(..., description="Alert type")
    enabled: bool = Field(..., description="Whether rule is enabled")
    cooldown_minutes: int = Field(..., description="Cooldown period in minutes")
    notification_channels: List[str] = Field(..., description="Notification channels")
    notification_recipients: List[str] = Field(..., description="Notification recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    last_triggered: Optional[datetime] = Field(None, description="Last trigger time")
    trigger_count: int = Field(0, description="Number of times triggered")
    properties: Dict[str, Any] = Field(..., description="Alert rule properties")


class AlertCreate(BaseModel):
    """Schema for alert creation."""
    alert_rule_id: UUID = Field(..., description="Alert rule ID")
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    alert_type: AlertType = Field(..., description="Alert type")
    message: str = Field(..., description="Alert message")
    reading_value: Optional[float] = Field(None, description="Reading value that triggered alert")
    reading_unit: Optional[str] = Field(None, description="Reading unit")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")


class AlertUpdate(BaseModel):
    """Schema for alert updates."""
    status: AlertStatus = Field(..., description="Alert status")
    acknowledged_by: Optional[UUID] = Field(None, description="User who acknowledged")
    resolved_by: Optional[UUID] = Field(None, description="User who resolved")
    notes: Optional[str] = Field(None, description="Alert notes")
    resolution_time: Optional[datetime] = Field(None, description="Resolution time")


class AlertResponse(BaseResponseSchema):
    """Schema for alert response."""
    alert_rule_id: UUID = Field(..., description="Alert rule ID")
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    severity: str = Field(..., description="Alert severity")
    alert_type: str = Field(..., description="Alert type")
    status: str = Field(..., description="Alert status")
    message: str = Field(..., description="Alert message")
    reading_value: Optional[float] = Field(None, description="Reading value that triggered alert")
    reading_unit: Optional[str] = Field(None, description="Reading unit")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    acknowledged_by: Optional[UUID] = Field(None, description="User who acknowledged")
    resolved_by: Optional[UUID] = Field(None, description="User who resolved")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgement time")
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")
    notes: Optional[str] = Field(None, description="Alert notes")
    event_id: UUID = Field(..., description="Associated event ID")


class AlertListResponse(BaseModel):
    """Schema for alert list response."""
    alerts: List[AlertResponse] = Field(..., description="List of alerts")
    total: int = Field(..., description="Total number of alerts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class AlertRuleListResponse(BaseModel):
    """Schema for alert rule list response."""
    alert_rules: List[AlertRuleResponse] = Field(..., description="List of alert rules")
    total: int = Field(..., description="Total number of alert rules")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class AlertQueryParams(PaginationParams, TimeRangeParams):
    """Schema for alert query parameters."""
    device_id: Optional[UUID] = Field(None, description="Filter by device ID")
    alert_rule_id: Optional[UUID] = Field(None, description="Filter by alert rule ID")
    severity: Optional[AlertSeverity] = Field(None, description="Filter by severity")
    status: Optional[AlertStatus] = Field(None, description="Filter by status")
    alert_type: Optional[AlertType] = Field(None, description="Filter by alert type")
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    acknowledged_by: Optional[UUID] = Field(None, description="Filter by acknowledged by")
    resolved_by: Optional[UUID] = Field(None, description="Filter by resolved by")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class AlertRuleQueryParams(PaginationParams):
    """Schema for alert rule query parameters."""
    device_id: Optional[UUID] = Field(None, description="Filter by device ID")
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    severity: Optional[AlertSeverity] = Field(None, description="Filter by severity")
    alert_type: Optional[AlertType] = Field(None, description="Filter by alert type")
    enabled: Optional[bool] = Field(None, description="Filter by enabled status")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    search: Optional[str] = Field(None, description="Search term")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class AlertStatsResponse(BaseModel):
    """Schema for alert statistics response."""
    total_alerts: int = Field(..., description="Total number of alerts")
    active_alerts: int = Field(..., description="Number of active alerts")
    acknowledged_alerts: int = Field(..., description="Number of acknowledged alerts")
    resolved_alerts: int = Field(..., description="Number of resolved alerts")
    dismissed_alerts: int = Field(..., description="Number of dismissed alerts")
    severity_distribution: Dict[str, int] = Field(..., description="Severity distribution")
    alert_type_distribution: Dict[str, int] = Field(..., description="Alert type distribution")
    device_distribution: Dict[str, int] = Field(..., description="Device distribution")
    time_period: str = Field(..., description="Time period for statistics")


class NotificationConfig(BaseModel):
    """Schema for notification configuration."""
    notification_type: NotificationType = Field(..., description="Notification type")
    enabled: bool = Field(True, description="Whether notification is enabled")
    recipients: List[str] = Field(default_factory=list, description="Notification recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    template: Optional[str] = Field(None, description="Notification template")
    cooldown_minutes: int = Field(5, ge=1, description="Notification cooldown in minutes")


class AlertRuleBulkUpdate(BaseModel):
    """Schema for bulk alert rule updates."""
    alert_rule_ids: List[UUID] = Field(..., description="List of alert rule IDs")
    enabled: Optional[bool] = Field(None, description="Enable/disable rules")
    severity: Optional[AlertSeverity] = Field(None, description="Update severity")
    cooldown_minutes: Optional[int] = Field(None, ge=1, description="Update cooldown")
    notification_channels: Optional[List[NotificationType]] = Field(None, description="Update notification channels")
    
    @validator('alert_rule_ids')
    def validate_alert_rule_ids(cls, v):
        """Validate alert rule IDs list."""
        if not v:
            raise ValueError('At least one alert rule ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 alert rules can be updated at once')
        return v 