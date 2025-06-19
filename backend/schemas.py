from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# Enums
class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class EntityType(str, Enum):
    DEVICE_ESP32 = "device.esp32"
    EQUIPMENT_OVEN = "equipment.oven"
    USER = "user"
    ORGANIZATION = "organization"

# Base Models
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Authentication Models
class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    name: str = Field(..., description="User full name")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")

class UserLogin(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    organization_id: Optional[UUID]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Device Models
class DeviceCreate(BaseModel):
    name: str = Field(..., description="Device name")
    entity_type: EntityType = Field(EntityType.DEVICE_ESP32, description="Device type")
    description: Optional[str] = Field(None, description="Device description")
    location: Optional[str] = Field(None, description="Device location")
    firmware_version: str = Field(..., description="Firmware version")
    hardware_model: str = Field(..., description="Hardware model")
    mac_address: str = Field(..., description="MAC address")
    sensors: List[Dict[str, Any]] = Field(default_factory=list, description="Sensor configurations")
    reading_interval: int = Field(300, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Device name")
    description: Optional[str] = Field(None, description="Device description")
    location: Optional[str] = Field(None, description="Device location")
    status: Optional[DeviceStatus] = Field(None, description="Device status")
    reading_interval: Optional[int] = Field(None, description="Reading interval in seconds")
    alert_thresholds: Optional[Dict[str, Any]] = Field(None, description="Alert thresholds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class DeviceResponse(BaseModel):
    id: UUID
    name: str
    entity_type: str
    description: Optional[str]
    status: str
    organization_id: Optional[UUID]
    properties: Dict[str, Any]
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True

class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int
    page: int
    per_page: int

# Device Status Models
class DeviceStatusUpdate(BaseModel):
    status: DeviceStatus
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    wifi_signal_strength: Optional[int] = Field(None, ge=-100, le=0)
    last_seen: Optional[datetime] = Field(None)

class DeviceHealthResponse(BaseModel):
    device_id: UUID
    status: DeviceStatus
    battery_level: Optional[float]
    wifi_signal_strength: Optional[int]
    last_seen: datetime
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    firmware_version: str
    sensor_count: int

# Sensor Reading Models
class SensorReading(BaseModel):
    sensor_type: str = Field(..., description="Type of sensor (temperature, humidity, etc.)")
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: Optional[datetime] = Field(None, description="Reading timestamp")
    quality: str = Field("good", description="Data quality indicator")
    battery_level: Optional[float] = Field(None, ge=0, le=100)

class DeviceReadingsRequest(BaseModel):
    readings: List[SensorReading] = Field(..., description="List of sensor readings")

class ReadingResponse(BaseModel):
    id: UUID
    device_id: UUID
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    quality: str
    battery_level: Optional[float]

    class Config:
        from_attributes = True

# API Key Models
class DeviceApiKey(BaseModel):
    device_id: UUID
    api_key: str
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True

# Organization Models
class OrganizationCreate(BaseModel):
    name: str = Field(..., description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    member_count: int

    class Config:
        from_attributes = True

# Query Parameters
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

class DeviceQueryParams(PaginationParams):
    status: Optional[DeviceStatus] = Field(None, description="Filter by device status")
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    location: Optional[str] = Field(None, description="Filter by location")

class ReadingQueryParams(PaginationParams):
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    start_time: Optional[datetime] = Field(None, description="Start time for readings")
    end_time: Optional[datetime] = Field(None, description="End time for readings")
    quality: Optional[str] = Field(None, description="Filter by data quality") 