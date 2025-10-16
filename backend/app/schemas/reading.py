"""
Reading schemas for VerdoyLab API.

This module contains Pydantic schemas for sensor readings,
data validation, and time-series data management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseResponseSchema, PaginationParams, TimeRangeParams


class DataQuality(str, Enum):
    """Data quality enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    BAD = "bad"


class SensorType(str, Enum):
    """Sensor type enumeration."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    LIGHT = "light"
    SOUND = "sound"
    MOTION = "motion"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    ENERGY = "energy"
    CUSTOM = "custom"


class SensorReading(BaseModel):
    """Schema for individual sensor reading."""
    sensor_type: str = Field(..., description="Type of sensor (temperature, humidity, etc.)")
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: Optional[datetime] = Field(None, description="Reading timestamp")
    quality: DataQuality = Field(DataQuality.GOOD, description="Data quality indicator")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Battery level percentage")
    location: Optional[str] = Field(None, description="Sensor location")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('value')
    def validate_value(cls, v):
        """Validate sensor value."""
        if not isinstance(v, (int, float)):
            raise ValueError('Value must be a number')
        if v == float('inf') or v == float('-inf'):
            raise ValueError('Value cannot be infinite')
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        """Validate unit of measurement."""
        valid_units = [
            '°C', '°F', 'K',  # Temperature
            '%', 'g/m³', 'ppm',  # Humidity
            'Pa', 'hPa', 'bar', 'atm',  # Pressure
            'lux', 'lm', 'cd',  # Light
            'dB', 'dB(A)',  # Sound
            'V', 'mV',  # Voltage
            'A', 'mA',  # Current
            'W', 'kW',  # Power
            'kWh', 'J',  # Energy
            'count', 'boolean', 'string'  # Other
        ]
        if v not in valid_units:
            raise ValueError(f'Invalid unit: {v}. Must be one of {valid_units}')
        return v


class DeviceReadingsRequest(BaseModel):
    """Schema for device readings submission."""
    device_id: UUID = Field(..., description="Device ID")
    readings: List[SensorReading] = Field(..., description="List of sensor readings")
    timestamp: Optional[datetime] = Field(None, description="Batch timestamp")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Device battery level")
    wifi_signal_strength: Optional[int] = Field(None, ge=-100, le=0, description="WiFi signal strength")
    device_temperature: Optional[float] = Field(None, description="Device temperature")
    
    @validator('readings')
    def validate_readings(cls, v):
        """Validate readings list."""
        if not v:
            raise ValueError('At least one reading must be provided')
        if len(v) > 50:
            raise ValueError('Maximum 50 readings per batch')
        return v


class ReadingResponse(BaseResponseSchema):
    """Schema for reading response."""
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    value: float = Field(..., description="Reading value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="Reading timestamp")
    quality: str = Field(..., description="Data quality")
    battery_level: Optional[float] = Field(None, description="Battery level")
    location: Optional[str] = Field(None, description="Sensor location")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    event_id: UUID = Field(..., description="Associated event ID")


class ReadingListResponse(BaseModel):
    """Schema for reading list response."""
    readings: List[ReadingResponse] = Field(..., description="List of readings")
    total: int = Field(..., description="Total number of readings")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    start_time: Optional[datetime] = Field(None, description="Query start time")
    end_time: Optional[datetime] = Field(None, description="Query end time")


class ReadingQueryParams(PaginationParams, TimeRangeParams):
    """Schema for reading query parameters."""
    device_id: Optional[UUID] = Field(None, description="Filter by device ID")
    sensor_type: Optional[str] = Field(None, description="Filter by sensor type")
    quality: Optional[DataQuality] = Field(None, description="Filter by data quality")
    min_value: Optional[float] = Field(None, description="Minimum value filter")
    max_value: Optional[float] = Field(None, description="Maximum value filter")
    unit: Optional[str] = Field(None, description="Filter by unit")
    location: Optional[str] = Field(None, description="Filter by location")
    sort_by: Optional[str] = Field("timestamp", description="Sort by field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")


class ReadingStatsResponse(BaseModel):
    """Schema for reading statistics response."""
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    count: int = Field(..., description="Number of readings")
    min_value: float = Field(..., description="Minimum value")
    max_value: float = Field(..., description="Maximum value")
    avg_value: float = Field(..., description="Average value")
    std_dev: float = Field(..., description="Standard deviation")
    unit: str = Field(..., description="Unit of measurement")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    quality_distribution: Dict[str, int] = Field(..., description="Quality distribution")


class ReadingAggregationParams(BaseModel):
    """Schema for reading aggregation parameters."""
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    interval: str = Field("1h", description="Aggregation interval (1m, 5m, 15m, 1h, 1d)")
    aggregation: str = Field("avg", description="Aggregation function (avg, min, max, sum, count)")
    
    @validator('interval')
    def validate_interval(cls, v):
        """Validate aggregation interval."""
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '6h', '12h', '1d', '1w', '1M']
        if v not in valid_intervals:
            raise ValueError(f'Invalid interval: {v}. Must be one of {valid_intervals}')
        return v
    
    @validator('aggregation')
    def validate_aggregation(cls, v):
        """Validate aggregation function."""
        valid_aggregations = ['avg', 'min', 'max', 'sum', 'count', 'stddev', 'percentile_95']
        if v not in valid_aggregations:
            raise ValueError(f'Invalid aggregation: {v}. Must be one of {valid_aggregations}')
        return v


class ReadingAggregationResponse(BaseModel):
    """Schema for reading aggregation response."""
    device_id: UUID = Field(..., description="Device ID")
    sensor_type: str = Field(..., description="Sensor type")
    interval: str = Field(..., description="Aggregation interval")
    aggregation: str = Field(..., description="Aggregation function")
    data_points: List[Dict[str, Any]] = Field(..., description="Aggregated data points")
    unit: str = Field(..., description="Unit of measurement")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")


class ReadingExportParams(BaseModel):
    """Schema for reading export parameters."""
    device_id: Optional[UUID] = Field(None, description="Device ID")
    sensor_type: Optional[str] = Field(None, description="Sensor type")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    format: str = Field("csv", description="Export format (csv, json, xlsx)")
    include_metadata: bool = Field(False, description="Include metadata columns")
    quality_filter: Optional[DataQuality] = Field(None, description="Filter by minimum quality")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate export format."""
        valid_formats = ['csv', 'json', 'xlsx']
        if v not in valid_formats:
            raise ValueError(f'Invalid format: {v}. Must be one of {valid_formats}')
        return v


class ReadingValidationError(BaseModel):
    """Schema for reading validation error."""
    reading_index: int = Field(..., description="Index of the invalid reading")
    field: str = Field(..., description="Field with error")
    error: str = Field(..., description="Error message")
    value: Any = Field(..., description="Invalid value")


class ReadingValidationResponse(BaseModel):
    """Schema for reading validation response."""
    valid: bool = Field(..., description="Whether all readings are valid")
    total_readings: int = Field(..., description="Total number of readings")
    valid_readings: int = Field(..., description="Number of valid readings")
    invalid_readings: int = Field(..., description="Number of invalid readings")
    errors: List[ReadingValidationError] = Field(default_factory=list, description="Validation errors")


class ReadingCreate(BaseModel):
    """Schema for creating a new reading."""
    device_id: UUID
    sensor_type: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None
    quality: Optional[DataQuality] = DataQuality.GOOD
    battery_level: Optional[float] = None
    location: Optional[str] = None
    metadata: Optional[dict] = None


class ReadingUpdate(BaseModel):
    """Schema for updating an existing reading."""
    sensor_type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None
    quality: Optional[DataQuality] = None
    battery_level: Optional[float] = None
    location: Optional[str] = None
    metadata: Optional[dict] = None


class ReadingExportRequest(BaseModel):
    """Schema for reading export request."""
    device_id: Optional[UUID] = Field(None, description="Device ID")
    sensor_type: Optional[str] = Field(None, description="Sensor type")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    format: str = Field("csv", description="Export format (csv, json, xlsx)")
    include_metadata: bool = Field(False, description="Include metadata columns")
    quality_filter: Optional[DataQuality] = Field(None, description="Filter by minimum quality") 