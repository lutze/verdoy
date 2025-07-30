"""
Bioreactor schemas for LMS Core API.

This module contains Pydantic schemas for bioreactor operations
including creation, updates, responses, and specialized operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class SensorConfig(BaseModel):
    """Schema for sensor configuration."""
    type: str = Field(..., description="Sensor type (temperature, pH, dissolved_oxygen, etc.)")
    unit: str = Field(..., description="Measurement unit")
    range: Optional[Dict[str, float]] = Field(None, description="Sensor range (min, max)")
    calibration_date: Optional[datetime] = Field(None, description="Last calibration date")
    status: str = Field("active", description="Sensor status")


class ActuatorConfig(BaseModel):
    """Schema for actuator configuration."""
    type: str = Field(..., description="Actuator type (pump, heater, stirrer, etc.)")
    unit: str = Field(..., description="Control unit")
    range: Optional[Dict[str, float]] = Field(None, description="Control range (min, max)")
    status: str = Field("active", description="Actuator status")
    safety_required: bool = Field(False, description="Whether safety confirmation is required")


class SafetyLimits(BaseModel):
    """Schema for safety limits."""
    temperature: Optional[Dict[str, float]] = Field(None, description="Temperature limits")
    ph: Optional[Dict[str, float]] = Field(None, description="pH limits")
    dissolved_oxygen: Optional[Dict[str, float]] = Field(None, description="Dissolved oxygen limits")
    pressure: Optional[Dict[str, float]] = Field(None, description="Pressure limits")
    flow_rate: Optional[Dict[str, float]] = Field(None, description="Flow rate limits")


class OperatingParameters(BaseModel):
    """Schema for operating parameters."""
    temperature: Optional[float] = Field(None, description="Current temperature")
    ph: Optional[float] = Field(None, description="Current pH")
    dissolved_oxygen: Optional[float] = Field(None, description="Current dissolved oxygen")
    pressure: Optional[float] = Field(None, description="Current pressure")
    flow_rate: Optional[float] = Field(None, description="Current flow rate")
    agitation_speed: Optional[float] = Field(None, description="Agitation speed")
    aeration_rate: Optional[float] = Field(None, description="Aeration rate")


class MaintenanceSchedule(BaseModel):
    """Schema for maintenance schedule."""
    calibration_interval_days: int = Field(30, description="Calibration interval in days")
    cleaning_interval_days: int = Field(7, description="Cleaning interval in days")
    last_calibration: Optional[datetime] = Field(None, description="Last calibration date")
    last_cleaning: Optional[datetime] = Field(None, description="Last cleaning date")
    next_calibration: Optional[datetime] = Field(None, description="Next calibration date")
    next_cleaning: Optional[datetime] = Field(None, description="Next cleaning date")


class BioreactorCreate(BaseModel):
    """Schema for creating a new bioreactor."""
    name: str = Field(..., min_length=1, max_length=255, description="Bioreactor name")
    description: Optional[str] = Field(None, description="Bioreactor description")
    location: Optional[str] = Field(None, description="Bioreactor location")
    organization_id: UUID = Field(..., description="Organization ID")
    
    # Bioreactor-specific properties
    bioreactor_type: str = Field("standard", description="Bioreactor type")
    vessel_volume: float = Field(..., gt=0, description="Vessel volume in liters")
    working_volume: Optional[float] = Field(None, gt=0, description="Working volume in liters")
    
    # Hardware configuration
    sensors: List[SensorConfig] = Field(default_factory=list, description="Sensor configurations")
    actuators: List[ActuatorConfig] = Field(default_factory=list, description="Actuator configurations")
    
    # Safety and operating parameters
    safety_limits: Optional[SafetyLimits] = Field(None, description="Safety limits")
    operating_parameters: Optional[OperatingParameters] = Field(None, description="Initial operating parameters")
    maintenance_schedule: Optional[MaintenanceSchedule] = Field(None, description="Maintenance schedule")
    
    # Device configuration
    firmware_version: str = Field(..., description="Firmware version")
    hardware_model: str = Field(..., description="Hardware model")
    mac_address: str = Field(..., description="Device MAC address")
    reading_interval: int = Field(300, ge=60, le=3600, description="Reading interval in seconds")
    
    @validator('working_volume')
    def validate_working_volume(cls, v, values):
        """Validate working volume is not greater than vessel volume."""
        if v is not None and 'vessel_volume' in values and v > values['vessel_volume']:
            raise ValueError('Working volume cannot be greater than vessel volume')
        return v


class BioreactorUpdate(BaseModel):
    """Schema for updating a bioreactor."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Bioreactor name")
    description: Optional[str] = Field(None, description="Bioreactor description")
    location: Optional[str] = Field(None, description="Bioreactor location")
    
    # Bioreactor-specific properties
    bioreactor_type: Optional[str] = Field(None, description="Bioreactor type")
    vessel_volume: Optional[float] = Field(None, gt=0, description="Vessel volume in liters")
    working_volume: Optional[float] = Field(None, gt=0, description="Working volume in liters")
    
    # Hardware configuration
    sensors: Optional[List[SensorConfig]] = Field(None, description="Sensor configurations")
    actuators: Optional[List[ActuatorConfig]] = Field(None, description="Actuator configurations")
    
    # Safety and operating parameters
    safety_limits: Optional[SafetyLimits] = Field(None, description="Safety limits")
    operating_parameters: Optional[OperatingParameters] = Field(None, description="Operating parameters")
    maintenance_schedule: Optional[MaintenanceSchedule] = Field(None, description="Maintenance schedule")
    
    # Device configuration
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    reading_interval: Optional[int] = Field(None, ge=60, le=3600, description="Reading interval in seconds")


class BioreactorResponse(BaseModel):
    """Schema for bioreactor response."""
    id: UUID = Field(..., description="Bioreactor ID")
    name: str = Field(..., description="Bioreactor name")
    description: Optional[str] = Field(None, description="Bioreactor description")
    location: Optional[str] = Field(None, description="Bioreactor location")
    organization_id: UUID = Field(..., description="Organization ID")
    status: str = Field(..., description="Bioreactor status")
    
    # Bioreactor-specific properties
    bioreactor_type: str = Field(..., description="Bioreactor type")
    vessel_volume: float = Field(..., description="Vessel volume in liters")
    working_volume: Optional[float] = Field(None, description="Working volume in liters")
    
    # Hardware configuration
    sensors: List[SensorConfig] = Field(..., description="Sensor configurations")
    actuators: List[ActuatorConfig] = Field(..., description="Actuator configurations")
    
    # Safety and operating parameters
    safety_limits: Optional[SafetyLimits] = Field(None, description="Safety limits")
    operating_parameters: Optional[OperatingParameters] = Field(None, description="Current operating parameters")
    maintenance_schedule: Optional[MaintenanceSchedule] = Field(None, description="Maintenance schedule")
    
    # Device information
    firmware_version: str = Field(..., description="Firmware version")
    hardware_model: str = Field(..., description="Hardware model")
    mac_address: str = Field(..., description="Device MAC address")
    reading_interval: int = Field(..., description="Reading interval in seconds")
    
    # Operational status
    control_mode: str = Field(..., description="Current control mode")
    experiment_id: Optional[UUID] = Field(None, description="Associated experiment ID")
    is_operational: bool = Field(..., description="Whether bioreactor is operational")
    is_running_experiment: bool = Field(..., description="Whether running an experiment")
    can_start_experiment: bool = Field(..., description="Whether can start an experiment")
    
    # Safety status
    safety_status: Dict[str, Any] = Field(..., description="Current safety status")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    last_calibration: Optional[datetime] = Field(None, description="Last calibration timestamp")
    
    class Config:
        from_attributes = True


class BioreactorListResponse(BaseModel):
    """Schema for bioreactor list response."""
    bioreactors: List[BioreactorResponse] = Field(..., description="List of bioreactors")
    total_count: int = Field(..., description="Total number of bioreactors")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


class BioreactorEnrollmentStep1(BaseModel):
    """Schema for bioreactor enrollment step 1 - Basic information."""
    name: str = Field(..., min_length=1, max_length=255, description="Bioreactor name")
    description: Optional[str] = Field(None, description="Bioreactor description")
    location: Optional[str] = Field(None, description="Bioreactor location")
    bioreactor_type: str = Field("standard", description="Bioreactor type")
    vessel_volume: float = Field(..., gt=0, description="Vessel volume in liters")
    working_volume: Optional[float] = Field(None, gt=0, description="Working volume in liters")


class BioreactorEnrollmentStep2(BaseModel):
    """Schema for bioreactor enrollment step 2 - Hardware configuration."""
    sensors: List[SensorConfig] = Field(..., description="Sensor configurations")
    actuators: List[ActuatorConfig] = Field(..., description="Actuator configurations")
    firmware_version: str = Field(..., description="Firmware version")
    hardware_model: str = Field(..., description="Hardware model")
    mac_address: str = Field(..., description="Device MAC address")


class BioreactorEnrollmentStep3(BaseModel):
    """Schema for bioreactor enrollment step 3 - Safety and operating parameters."""
    safety_limits: Optional[SafetyLimits] = Field(None, description="Safety limits")
    operating_parameters: Optional[OperatingParameters] = Field(None, description="Initial operating parameters")
    maintenance_schedule: Optional[MaintenanceSchedule] = Field(None, description="Maintenance schedule")
    reading_interval: int = Field(300, ge=60, le=3600, description="Reading interval in seconds")


class BioreactorControlRequest(BaseModel):
    """Schema for bioreactor control requests."""
    control_type: str = Field(..., description="Type of control (setpoint, emergency_stop, etc.)")
    parameter: Optional[str] = Field(None, description="Parameter to control")
    value: Optional[float] = Field(None, description="Control value")
    safety_confirmation: Optional[bool] = Field(None, description="Safety confirmation for critical operations")
    
    @validator('safety_confirmation')
    def validate_safety_confirmation(cls, v, values):
        """Validate safety confirmation for critical operations."""
        control_type = values.get('control_type')
        if control_type in ['emergency_stop', 'shutdown'] and not v:
            raise ValueError('Safety confirmation required for critical operations')
        return v


class BioreactorControlResponse(BaseModel):
    """Schema for bioreactor control response."""
    success: bool = Field(..., description="Whether control operation was successful")
    message: str = Field(..., description="Response message")
    control_id: Optional[str] = Field(None, description="Control operation ID")
    timestamp: datetime = Field(..., description="Control operation timestamp")


class BioreactorStatusResponse(BaseModel):
    """Schema for bioreactor status response."""
    id: UUID = Field(..., description="Bioreactor ID")
    name: str = Field(..., description="Bioreactor name")
    status: str = Field(..., description="Current status")
    control_mode: str = Field(..., description="Current control mode")
    operating_parameters: Optional[OperatingParameters] = Field(None, description="Current operating parameters")
    safety_status: Dict[str, Any] = Field(..., description="Current safety status")
    is_operational: bool = Field(..., description="Whether bioreactor is operational")
    is_running_experiment: bool = Field(..., description="Whether running an experiment")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    experiment_id: Optional[UUID] = Field(None, description="Associated experiment ID")


class BioreactorEnrollmentResponse(BaseModel):
    """Schema for bioreactor enrollment response."""
    bioreactor: BioreactorResponse = Field(..., description="Created bioreactor")
    enrollment_complete: bool = Field(..., description="Whether enrollment is complete")
    next_steps: List[str] = Field(..., description="Next steps for enrollment")
    api_key: str = Field(..., description="API key for device authentication")
    device_id: str = Field(..., description="Device ID for API access") 