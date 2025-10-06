"""
Process schemas for the VerdoyLab system.

This module defines Pydantic schemas for Process and ProcessInstance models,
including validation rules and serialization formats.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class ProcessType(str, Enum):
    """Process type enumeration."""
    FERMENTATION = "fermentation"
    CULTIVATION = "cultivation"
    PURIFICATION = "purification"
    ANALYSIS = "analysis"
    CALIBRATION = "calibration"
    CLEANING = "cleaning"
    CUSTOM = "custom"


class ProcessStatus(str, Enum):
    """Process status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ProcessInstanceStatus(str, Enum):
    """Process instance status enumeration."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Step type enumeration."""
    TEMPERATURE_CONTROL = "temperature_control"
    PH_CONTROL = "ph_control"
    DISSOLVED_OXYGEN_CONTROL = "dissolved_oxygen_control"
    STIRRING = "stirring"
    FEEDING = "feeding"
    SAMPLING = "sampling"
    ANALYSIS = "analysis"
    WAIT = "wait"
    CUSTOM = "custom"


class ProcessStep(BaseModel):
    """Schema for a process step."""
    name: str = Field(..., description="Step name")
    step_type: StepType = Field(..., description="Type of step")
    description: Optional[str] = Field(None, description="Step description")
    duration: Optional[int] = Field(None, description="Step duration in minutes")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    order: int = Field(..., description="Step order in process")
    required: bool = Field(default=True, description="Whether step is required")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Temperature Ramp",
                "step_type": "temperature_control",
                "description": "Ramp temperature to 37°C",
                "duration": 30,
                "parameters": {
                    "target_temperature": 37.0,
                    "ramp_rate": 1.0,
                    "tolerance": 0.5
                },
                "order": 1,
                "required": True
            }
        }


class ProcessDefinition(BaseModel):
    """Schema for process definition."""
    steps: List[ProcessStep] = Field(default_factory=list, description="Process steps")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Process parameters")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Process requirements")
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict, description="Expected outcomes")
    
    class Config:
        schema_extra = {
            "example": {
                "steps": [
                    {
                        "name": "Temperature Ramp",
                        "step_type": "temperature_control",
                        "description": "Ramp temperature to 37°C",
                        "duration": 30,
                        "parameters": {
                            "target_temperature": 37.0,
                            "ramp_rate": 1.0,
                            "tolerance": 0.5
                        },
                        "order": 1,
                        "required": True
                    }
                ],
                "parameters": {
                    "culture_volume": 1000,
                    "strain": "E. coli BL21",
                    "medium": "LB"
                },
                "estimated_duration": 480,
                "requirements": {
                    "bioreactor_type": "stirred_tank",
                    "sensors": ["temperature", "ph", "dissolved_oxygen"],
                    "actuators": ["heater", "stirrer", "pump"]
                },
                "expected_outcomes": {
                    "final_od": ">2.0",
                    "productivity": ">0.5 g/L/h"
                }
            }
        }


class ProcessCreate(BaseModel):
    """Schema for creating a new process."""
    name: str = Field(..., min_length=1, max_length=200, description="Process name")
    version: str = Field(..., description="Process version")
    process_type: ProcessType = Field(..., description="Process type")
    definition: ProcessDefinition = Field(..., description="Process definition")
    description: Optional[str] = Field(None, description="Process description")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_template: bool = Field(default=False, description="Whether this is a template")
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        if not v or len(v) > 20:
            raise ValueError("Version must be between 1 and 20 characters")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "E. coli Fermentation Protocol",
                "version": "1.0.0",
                "process_type": "fermentation",
                "definition": {
                    "steps": [
                        {
                            "name": "Temperature Ramp",
                            "step_type": "temperature_control",
                            "description": "Ramp temperature to 37°C",
                            "duration": 30,
                            "parameters": {
                                "target_temperature": 37.0,
                                "ramp_rate": 1.0,
                                "tolerance": 0.5
                            },
                            "order": 1,
                            "required": True
                        }
                    ],
                    "parameters": {
                        "culture_volume": 1000,
                        "strain": "E. coli BL21",
                        "medium": "LB"
                    },
                    "estimated_duration": 480,
                    "requirements": {
                        "bioreactor_type": "stirred_tank",
                        "sensors": ["temperature", "ph", "dissolved_oxygen"],
                        "actuators": ["heater", "stirrer", "pump"]
                    },
                    "expected_outcomes": {
                        "final_od": ">2.0",
                        "productivity": ">0.5 g/L/h"
                    }
                },
                "description": "Standard E. coli fermentation protocol",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_template": True
            }
        }


class ProcessUpdate(BaseModel):
    """Schema for updating a process."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Process name")
    version: Optional[str] = Field(None, description="Process version")
    process_type: Optional[ProcessType] = Field(None, description="Process type")
    definition: Optional[ProcessDefinition] = Field(None, description="Process definition")
    description: Optional[str] = Field(None, description="Process description")
    status: Optional[ProcessStatus] = Field(None, description="Process status")
    is_template: Optional[bool] = Field(None, description="Whether this is a template")
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        if v is not None and (not v or len(v) > 20):
            raise ValueError("Version must be between 1 and 20 characters")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated E. coli Fermentation Protocol",
                "version": "1.1.0",
                "process_type": "fermentation",
                "description": "Updated fermentation protocol with improved parameters",
                "status": "active",
                "is_template": True
            }
        }


class ProcessResponse(BaseModel):
    """Schema for process response."""
    id: UUID = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    version: str = Field(..., description="Process version")
    process_type: ProcessType = Field(..., description="Process type")
    definition: ProcessDefinition = Field(..., description="Process definition")
    status: ProcessStatus = Field(..., description="Process status")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    created_by: Optional[UUID] = Field(None, description="Created by user ID")
    description: Optional[str] = Field(None, description="Process description")
    is_template: bool = Field(..., description="Whether this is a template")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    step_count: int = Field(..., description="Number of steps in process")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "E. coli Fermentation Protocol",
                "version": "1.0.0",
                "process_type": "fermentation",
                "definition": {
                    "steps": [
                        {
                            "name": "Temperature Ramp",
                            "step_type": "temperature_control",
                            "description": "Ramp temperature to 37°C",
                            "duration": 30,
                            "parameters": {
                                "target_temperature": 37.0,
                                "ramp_rate": 1.0,
                                "tolerance": 0.5
                            },
                            "order": 1,
                            "required": True
                        }
                    ],
                    "parameters": {
                        "culture_volume": 1000,
                        "strain": "E. coli BL21",
                        "medium": "LB"
                    },
                    "estimated_duration": 480,
                    "requirements": {
                        "bioreactor_type": "stirred_tank",
                        "sensors": ["temperature", "ph", "dissolved_oxygen"],
                        "actuators": ["heater", "stirrer", "pump"]
                    },
                    "expected_outcomes": {
                        "final_od": ">2.0",
                        "productivity": ">0.5 g/L/h"
                    }
                },
                "status": "active",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_by": "123e4567-e89b-12d3-a456-426614174000",
                "description": "Standard E. coli fermentation protocol",
                "is_template": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "step_count": 1,
                "estimated_duration": 480
            }
        }


class ProcessInstanceCreate(BaseModel):
    """Schema for creating a new process instance."""
    process_id: UUID = Field(..., description="Process ID")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Instance-specific parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "process_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "BATCH-2024-001",
                "parameters": {
                    "culture_volume": 1000,
                    "strain": "E. coli BL21",
                    "medium": "LB",
                    "target_od": 2.0
                }
            }
        }


class ProcessInstanceUpdate(BaseModel):
    """Schema for updating a process instance."""
    status: Optional[ProcessInstanceStatus] = Field(None, description="Instance status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Instance parameters")
    results: Optional[Dict[str, Any]] = Field(None, description="Execution results")
    current_step: Optional[str] = Field(None, description="Current step")
    step_results: Optional[Dict[str, Any]] = Field(None, description="Step results")
    error_message: Optional[str] = Field(None, description="Error message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "running",
                "current_step": "Temperature Ramp",
                "step_results": {
                    "Temperature Ramp": {
                        "started_at": "2024-01-01T10:00:00Z",
                        "completed_at": "2024-01-01T10:30:00Z",
                        "actual_temperature": 37.2
                    }
                }
            }
        }


class ProcessInstanceResponse(BaseModel):
    """Schema for process instance response."""
    id: UUID = Field(..., description="Instance ID")
    process_id: UUID = Field(..., description="Process ID")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    status: ProcessInstanceStatus = Field(..., description="Instance status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    parameters: Dict[str, Any] = Field(..., description="Instance parameters")
    results: Dict[str, Any] = Field(..., description="Execution results")
    current_step: Optional[str] = Field(None, description="Current step")
    step_results: Dict[str, Any] = Field(..., description="Step results")
    error_message: Optional[str] = Field(None, description="Error message")
    created_by: Optional[UUID] = Field(None, description="Created by user ID")
    duration: Optional[int] = Field(None, description="Execution duration in minutes")
    process: Optional[ProcessResponse] = Field(None, description="Associated process")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "process_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "BATCH-2024-001",
                "status": "running",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": None,
                "parameters": {
                    "culture_volume": 1000,
                    "strain": "E. coli BL21",
                    "medium": "LB",
                    "target_od": 2.0
                },
                "results": {},
                "current_step": "Temperature Ramp",
                "step_results": {
                    "Temperature Ramp": {
                        "started_at": "2024-01-01T10:00:00Z",
                        "completed_at": "2024-01-01T10:30:00Z",
                        "actual_temperature": 37.2
                    }
                },
                "error_message": None,
                "created_by": "123e4567-e89b-12d3-a456-426614174000",
                "duration": 30,
                "process": None
            }
        }


class ProcessListResponse(BaseModel):
    """Schema for process list response."""
    processes: List[ProcessResponse] = Field(..., description="List of processes")
    total: int = Field(..., description="Total number of processes")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    
    class Config:
        schema_extra = {
            "example": {
                "processes": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "E. coli Fermentation Protocol",
                        "version": "1.0.0",
                        "process_type": "fermentation",
                        "status": "active",
                        "step_count": 5,
                        "estimated_duration": 480
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
        }


class ProcessInstanceListResponse(BaseModel):
    """Schema for process instance list response."""
    instances: List[ProcessInstanceResponse] = Field(..., description="List of process instances")
    total: int = Field(..., description="Total number of instances")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    
    class Config:
        schema_extra = {
            "example": {
                "instances": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "process_id": "123e4567-e89b-12d3-a456-426614174000",
                        "batch_id": "BATCH-2024-001",
                        "status": "running",
                        "started_at": "2024-01-01T10:00:00Z",
                        "duration": 30
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
        } 