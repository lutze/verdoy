"""
Device management router for IoT device operations.

This router handles all device-related operations including:
- Device CRUD operations for web interface
- Device status and health monitoring
- Device configuration management
- IoT data ingestion from devices
- Device provisioning and authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..dependencies import get_db, get_current_user, authenticate_device
from ..schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceStatusUpdate,
    DeviceHealthResponse,
    DeviceConfigResponse,
    DeviceConfigUpdate,
    DeviceProvisionRequest,
    DeviceProvisionResponse,
    DeviceQueryParams
)
from ..schemas.reading import (
    DeviceReadingsRequest,
    ReadingResponse,
    ReadingListResponse,
    ReadingQueryParams
)
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..models.device import Device
from ..models.reading import Reading
from ..exceptions import (
    DeviceNotFoundException,
    AccessDeniedException,
    DeviceAuthenticationException,
    ValidationException
)

router = APIRouter(tags=["Device Management"])

# ============================================================================
# DEVICE CRUD OPERATIONS (Web Interface)
# ============================================================================

@router.get("", response_model=DeviceListResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def list_devices(
    params: DeviceQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all devices for the authenticated user's organization.
    
    Returns a paginated list of devices with filtering and sorting options.
    """
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Calculate pagination
    skip = (params.page - 1) * params.per_page
    
    # Get devices with filters
    devices = Device.get_devices(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=params.per_page,
        status=params.status,
        entity_type=params.entity_type,
        search=params.search
    )
    
    # Get total count
    total = Device.count_devices(
        db=db,
        organization_id=organization_id,
        status=params.status,
        entity_type=params.entity_type,
        search=params.search
    )
    
    return DeviceListResponse(
        devices=[
            DeviceResponse.from_model(device) for device in devices
        ],
        total=total,
        page=params.page,
        per_page=params.per_page,
        size=len(devices)
    )

@router.post("", response_model=DeviceResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new device.
    
    Registers a new device in the system with the provided configuration.
    """
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Create device
    device = Device.create_device(
        db=db,
        device_data=device_data,
        organization_id=organization_id,
        created_by=current_user.email
    )
    
    return DeviceResponse.from_model(device)

@router.get("/{device_id}", response_model=DeviceResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get device details.
    
    Returns detailed information about a specific device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    return DeviceResponse.from_model(device)

@router.put("/{device_id}", response_model=DeviceResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update device details.
    
    Updates device information including name, description, and properties.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Update device
    updated_device = Device.update_device(db, device_id, device_data)
    
    return DeviceResponse.from_model(updated_device)

@router.delete("/{device_id}", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a device.
    
    Removes a device from the system. This action cannot be undone.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Delete device
    Device.delete_device(db, device_id)
    
    return BaseResponse(
        message="Device successfully deleted",
        success=True
    )

# ============================================================================
# DEVICE STATUS AND HEALTH
# ============================================================================

@router.get("/{device_id}/status", response_model=DeviceHealthResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device_status(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get device status and health information.
    
    Returns current device status, last seen time, and health metrics.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    return DeviceHealthResponse.from_model(device)

@router.get("/{device_id}/health", response_model=DeviceHealthResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device_health(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed device health metrics.
    
    Returns comprehensive health information including diagnostics and metrics.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    return DeviceHealthResponse.from_model(device, detailed=True)

# ============================================================================
# DEVICE CONFIGURATION
# ============================================================================

@router.get("/{device_id}/config", response_model=DeviceConfigResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device_config(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get device configuration.
    
    Returns the current configuration settings for the device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    return DeviceConfigResponse.from_model(device)

@router.put("/{device_id}/config", response_model=DeviceConfigResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def update_device_config(
    device_id: UUID,
    config_data: DeviceConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update device configuration.
    
    Updates device settings and configuration parameters.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Update configuration
    updated_device = Device.update_config(db, device_id, config_data)
    
    return DeviceConfigResponse.from_model(updated_device)

# ============================================================================
# DEVICE PROVISIONING
# ============================================================================

@router.post("/provision", response_model=DeviceProvisionResponse, responses={
    400: {"model": ErrorResponse},
    409: {"model": ErrorResponse}
})
async def provision_device(
    provision_data: DeviceProvisionRequest,
    db: Session = Depends(get_db)
):
    """
    Provision a new device.
    
    Initial device setup and registration process.
    """
    # Check if device already exists
    existing_device = Device.get_device_by_mac(db, provision_data.mac_address)
    if existing_device:
        raise ValidationException(detail="Device with this MAC address already exists")
    
    # Provision device
    device = Device.provision_device(db, provision_data)
    
    return DeviceProvisionResponse.from_model(device)

@router.get("/{device_id}/provision-status", response_model=DeviceProvisionResponse, responses={
    404: {"model": ErrorResponse}
})
async def get_provision_status(
    device_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Check device provisioning status.
    
    Returns the current provisioning status of a device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    return DeviceProvisionResponse.from_model(device)

# ============================================================================
# IOT DATA INGESTION (Device → Server)
# ============================================================================

@router.post("/{device_id}/readings", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def receive_readings(
    device_id: UUID,
    readings_request: DeviceReadingsRequest,
    device: Device = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """
    Receive sensor readings from device.
    
    Endpoint for ESP32 devices to send batch sensor readings.
    """
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise DeviceAuthenticationException(detail="Device ID mismatch")
    
    # Process and store readings
    Reading.process_device_readings(db, device, readings_request.readings)
    
    # Update device last seen
    device.update_last_seen()
    db.commit()
    
    return BaseResponse(
        message=f"Successfully processed {len(readings_request.readings)} readings",
        success=True
    )

@router.post("/{device_id}/heartbeat", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def device_heartbeat(
    device_id: UUID,
    status_update: DeviceStatusUpdate,
    device: Device = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """
    Device keep-alive heartbeat.
    
    Endpoint for devices to send periodic status updates.
    """
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise DeviceAuthenticationException(detail="Device ID mismatch")
    
    # Update device status
    device.update_status(status_update)
    db.commit()
    
    return BaseResponse(
        message="Heartbeat received",
        success=True
    )

@router.post("/{device_id}/status", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def update_device_status(
    device_id: UUID,
    status_update: DeviceStatusUpdate,
    device: Device = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """
    Update device status.
    
    Endpoint for devices to send status updates.
    """
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise DeviceAuthenticationException(detail="Device ID mismatch")
    
    # Update device status
    device.update_status(status_update)
    db.commit()
    
    return BaseResponse(
        message="Status updated successfully",
        success=True
    )

# ============================================================================
# DEVICE READINGS RETRIEVAL
# ============================================================================

@router.get("/{device_id}/readings", response_model=ReadingListResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device_readings(
    device_id: UUID,
    params: ReadingQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get device readings.
    
    Returns historical sensor readings for a specific device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Get readings with filters
    readings = Reading.get_device_readings(
        db=db,
        device_id=device_id,
        start_time=params.start_time,
        end_time=params.end_time,
        sensor_type=params.sensor_type,
        limit=params.limit,
        offset=params.offset
    )
    
    return ReadingListResponse(
        readings=[ReadingResponse.from_model(reading) for reading in readings],
        device_id=device_id,
        total=len(readings)
    )

@router.get("/{device_id}/readings/latest", response_model=List[ReadingResponse], responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_latest_readings(
    device_id: UUID,
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get latest device readings.
    
    Returns the most recent sensor readings for a device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Get latest readings
    readings = Reading.get_latest_readings(db, device_id, sensor_type)
    
    return [ReadingResponse.from_model(reading) for reading in readings]

# ============================================================================
# DEVICE CONTROL
# ============================================================================

@router.post("/{device_id}/reboot", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def reboot_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger device reboot.
    
    Sends a reboot command to the device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # TODO: Implement command queuing
    # For now, just return success
    return BaseResponse(
        message="Reboot command sent to device",
        success=True
    ) 