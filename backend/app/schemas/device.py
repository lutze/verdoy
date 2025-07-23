"""
Device schemas for LMS Core API.

This module contains Pydantic schemas for device management,
status updates, and health monitoring.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams


class DeviceStatus(str, Enum):
    """Device status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    REGISTERED = "registered"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class EntityType(str, Enum):
    """Entity type enumeration."""
    DEVICE_ESP32 = "device.esp32"
    EQUIPMENT_OVEN = "equipment.oven"
    USER = "user"
    ORGANIZATION = "organization"


class DeviceCreate(BaseModel):
    """Schema for device creation."""
    name: str = Field(..., description="Device name")
    serial_number: str = Field(..., description="Device serial number")
    device_type: str = Field(..., description="Device type")
    model: str = Field(..., description="Device model")
    description: Optional[str] = Field(None, description="Device description")
    location: Optional[str] = Field(None, description="Device location")
    firmware_version: str = Field(..., description="Firmware version")
    mac_address: str = Field(..., description="MAC address")
    sensors: List[Dict[str, Any]] = Field(default_factory=list, description="Sensor configurations")
    reading_interval: int = Field(300, ge=60, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        """Validate MAC address format."""
        import re
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if not mac_pattern.match(v):
            raise ValueError('Invalid MAC address format')
        return v.upper()
    
    @validator('reading_interval')
    def validate_reading_interval(cls, v):
        """Validate reading interval."""
        if v < 60:
            raise ValueError('Reading interval must be at least 60 seconds')
        return v


class DeviceUpdate(BaseModel):
    """Schema for device updates."""
    name: Optional[str] = Field(None, description="Device name")
    description: Optional[str] = Field(None, description="Device description")
    location: Optional[str] = Field(None, description="Device location")
    status: Optional[DeviceStatus] = Field(None, description="Device status")
    reading_interval: Optional[int] = Field(None, ge=60, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    hardware_model: Optional[str] = Field(None, description="Hardware model")
    
    @validator('reading_interval')
    def validate_reading_interval(cls, v):
        """Validate reading interval."""
        if v is not None and v < 60:
            raise ValueError('Reading interval must be at least 60 seconds')
        return v


class DeviceStatusUpdate(BaseModel):
    """Schema for device status updates."""
    status: DeviceStatus = Field(..., description="Device status")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Battery level percentage")
    wifi_signal_strength: Optional[int] = Field(None, ge=-100, le=0, description="WiFi signal strength in dBm")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    uptime: Optional[int] = Field(None, ge=0, description="Uptime in seconds")
    temperature: Optional[float] = Field(None, description="Device temperature")
    memory_usage: Optional[float] = Field(None, ge=0, le=100, description="Memory usage percentage")
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")


class DeviceResponse(BaseResponseSchema):
    """Schema for device response."""
    name: str = Field(..., description="Device name")
    entity_type: str = Field(..., description="Device type")
    description: Optional[str] = Field(None, description="Device description")
    status: str = Field(..., description="Device status")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    properties: Dict[str, Any] = Field(..., description="Device properties")
    location: Optional[str] = Field(None, description="Device location")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    hardware_model: Optional[str] = Field(None, description="Hardware model")
    mac_address: Optional[str] = Field(None, description="MAC address")
    sensors: Optional[List[Dict[str, Any]]] = Field(None, description="Sensor configurations")
    reading_interval: Optional[int] = Field(None, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    last_reading: Optional[datetime] = Field(None, description="Last reading timestamp")
    last_status_update: Optional[datetime] = Field(None, description="Last status update")


class DeviceListResponse(BaseModel):
    """Schema for device list response."""
    devices: List[DeviceResponse] = Field(..., description="List of devices")
    total: int = Field(..., description="Total number of devices")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class DeviceHealthResponse(BaseModel):
    """Schema for device health response."""
    device_id: UUID = Field(..., description="Device ID")
    status: DeviceStatus = Field(..., description="Device status")
    battery_level: Optional[float] = Field(None, description="Battery level percentage")
    wifi_signal_strength: Optional[int] = Field(None, description="WiFi signal strength in dBm")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    firmware_version: str = Field(..., description="Firmware version")
    sensor_count: int = Field(..., description="Number of sensors")
    temperature: Optional[float] = Field(None, description="Device temperature")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    last_reading: Optional[datetime] = Field(None, description="Last reading timestamp")


class DeviceApiKey(BaseModel):
    """Schema for device API key."""
    device_id: UUID = Field(..., description="Device ID")
    api_key: str = Field(..., description="API key")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(True, description="API key active status")
    
    class Config:
        from_attributes = True


class DeviceApiKeyCreate(BaseModel):
    """Schema for device API key creation."""
    device_id: UUID = Field(..., description="Device ID")
    name: Optional[str] = Field(None, description="API key name")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class DeviceQueryParams(PaginationParams):
    """Schema for device query parameters."""
    status: Optional[DeviceStatus] = Field(None, description="Filter by device status")
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    location: Optional[str] = Field(None, description="Filter by location")
    organization_id: Optional[UUID] = Field(None, description="Filter by organization")
    search: Optional[str] = Field(None, description="Search term")
    firmware_version: Optional[str] = Field(None, description="Filter by firmware version")
    hardware_model: Optional[str] = Field(None, description="Filter by hardware model")
    sort_by: Optional[str] = Field("created_at", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class DeviceBulkUpdate(BaseModel):
    """Schema for bulk device updates."""
    device_ids: List[UUID] = Field(..., description="List of device IDs")
    status: Optional[DeviceStatus] = Field(None, description="Device status")
    location: Optional[str] = Field(None, description="Device location")
    reading_interval: Optional[int] = Field(None, ge=60, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    
    @validator('device_ids')
    def validate_device_ids(cls, v):
        """Validate device IDs list."""
        if not v:
            raise ValueError('At least one device ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 devices can be updated at once')
        return v


class DeviceExportParams(BaseModel):
    """Schema for device export parameters."""
    format: str = Field("csv", description="Export format (csv, json, xlsx)")
    include_readings: bool = Field(False, description="Include device readings")
    start_date: Optional[datetime] = Field(None, description="Start date for readings")
    end_date: Optional[datetime] = Field(None, description="End date for readings")
    device_ids: Optional[List[UUID]] = Field(None, description="Specific device IDs to export")


class DeviceConfigResponse(BaseModel):
    """Schema for device configuration response."""
    device_id: UUID = Field(..., description="Device ID")
    reading_interval: int = Field(..., description="Reading interval in seconds")
    alert_thresholds: Dict[str, Any] = Field(default_factory=dict, description="Alert thresholds")
    wifi_config: Optional[Dict[str, Any]] = Field(None, description="WiFi configuration")
    sensor_config: Optional[Dict[str, Any]] = Field(None, description="Sensor configuration")
    firmware_config: Optional[Dict[str, Any]] = Field(None, description="Firmware configuration")
    last_config_update: Optional[datetime] = Field(None, description="Last configuration update")
    
    class Config:
        from_attributes = True


class DeviceConfigUpdate(BaseModel):
    """Schema for device configuration updates."""
    reading_interval: Optional[int] = Field(None, ge=60, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    wifi_config: Optional[Dict[str, Any]] = Field(None, description="WiFi configuration")
    sensor_config: Optional[Dict[str, Any]] = Field(None, description="Sensor configuration")
    firmware_config: Optional[Dict[str, Any]] = Field(None, description="Firmware configuration")
    
    @validator('reading_interval')
    def validate_reading_interval(cls, v):
        """Validate reading interval."""
        if v is not None and v < 60:
            raise ValueError('Reading interval must be at least 60 seconds')
        return v


class DeviceProvisionRequest(BaseModel):
    """Schema for device provisioning request."""
    mac_address: str = Field(..., description="Device MAC address")
    hardware_model: str = Field(..., description="Hardware model")
    firmware_version: str = Field(..., description="Firmware version")
    device_name: Optional[str] = Field(None, description="Device name")
    location: Optional[str] = Field(None, description="Device location")
    sensors: List[Dict[str, Any]] = Field(default_factory=list, description="Sensor configurations")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        """Validate MAC address format."""
        import re
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if not mac_pattern.match(v):
            raise ValueError('Invalid MAC address format')
        return v.upper()


class DeviceProvisionResponse(BaseModel):
    """Schema for device provisioning response."""
    device_id: UUID = Field(..., description="Device ID")
    api_key: str = Field(..., description="Device API key")
    device_name: str = Field(..., description="Device name")
    status: str = Field(..., description="Provisioning status")
    created_at: datetime = Field(..., description="Creation timestamp")
    config_url: str = Field(..., description="Configuration endpoint URL")
    
    class Config:
        from_attributes = True 