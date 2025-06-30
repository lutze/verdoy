from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from database import get_db
from auth import get_current_active_user, authenticate_device
from schemas import (
    DeviceCreate, 
    DeviceUpdate, 
    DeviceResponse, 
    DeviceListResponse,
    DeviceStatusUpdate,
    DeviceHealthResponse,
    DeviceReadingsRequest,
    DeviceQueryParams,
    ReadingQueryParams
)
from crud import DeviceCRUD, ReadingCRUD
from models import User, Entity

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

# Device CRUD Operations (Web Interface)
@router.get("", response_model=DeviceListResponse)
def list_devices(
    params: DeviceQueryParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all devices for the authenticated user's organization."""
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Calculate pagination
    skip = (params.page - 1) * params.per_page
    
    # Get devices
    devices = DeviceCRUD.get_devices(
        db=db,
        organization_id=organization_id,
        skip=skip,
        limit=params.per_page,
        status=params.status.value if params.status else None,
        entity_type=params.entity_type.value if params.entity_type else None
    )
    
    # Get total count
    total_query = db.query(Entity).filter(Entity.entity_type == "device.esp32")
    if organization_id:
        total_query = total_query.filter(Entity.organization_id == organization_id)
    total = total_query.count()
    
    return DeviceListResponse(
        devices=[
            DeviceResponse(
                id=device.id,
                name=device.name,
                entity_type=device.entity_type,
                description=device.description,
                status=device.properties.get("status", "unknown") if device.properties else "unknown",
                organization_id=device.organization_id,
                properties=device.properties or {},
                created_at=device.created_at,
                last_updated=device.last_updated
            ) for device in devices
        ],
        total=total,
        page=params.page,
        per_page=params.per_page
    )

@router.post("", response_model=DeviceResponse)
def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new device."""
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Create device
    device = DeviceCRUD.create_device(
        db=db,
        device_data=device_data,
        organization_id=organization_id,
        created_by=current_user.email
    )
    
    return DeviceResponse(
        id=device.id,
        name=device.name,
        entity_type=device.entity_type,
        description=device.description,
        status=device.properties.get("status", "unknown") if device.properties else "unknown",
        organization_id=device.organization_id,
        properties=device.properties or {},
        created_at=device.created_at,
        last_updated=device.last_updated
    )

@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get device details."""
    device = DeviceCRUD.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check organization access
    if current_user.entity.organization_id != device.organization_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this device"
        )
    
    return DeviceResponse(
        id=device.id,
        name=device.name,
        entity_type=device.entity_type,
        description=device.description,
        status=device.properties.get("status", "unknown") if device.properties else "unknown",
        organization_id=device.organization_id,
        properties=device.properties or {},
        created_at=device.created_at,
        last_updated=device.last_updated
    )

@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update device details."""
    device = DeviceCRUD.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check organization access
    if current_user.entity.organization_id != device.organization_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this device"
        )
    
    # Update device
    updated_device = DeviceCRUD.update_device(db, device_id, device_data)
    if not updated_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return DeviceResponse(
        id=updated_device.id,
        name=updated_device.name,
        entity_type=updated_device.entity_type,
        description=updated_device.description,
        status=updated_device.properties.get("status", "unknown") if updated_device.properties else "unknown",
        organization_id=updated_device.organization_id,
        properties=updated_device.properties or {},
        created_at=updated_device.created_at,
        last_updated=updated_device.last_updated
    )

@router.delete("/{device_id}")
def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a device."""
    device = DeviceCRUD.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check organization access
    if current_user.entity.organization_id != device.organization_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this device"
        )
    
    # Delete device
    success = DeviceCRUD.delete_device(db, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": "Device deleted successfully"}

# Device Status and Health
@router.get("/{device_id}/status", response_model=DeviceHealthResponse)
def get_device_status(
    device_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get device status and health information."""
    device = DeviceCRUD.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check organization access
    if current_user.entity.organization_id != device.organization_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this device"
        )
    
    properties = device.properties or {}
    
    # Convert lastSeen string to datetime if it exists
    last_seen = None
    if properties.get("lastSeen"):
        try:
            last_seen = datetime.fromisoformat(properties["lastSeen"].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            last_seen = None
    
    return DeviceHealthResponse(
        device_id=device.id,
        status=properties.get("status", "offline"),
        battery_level=properties.get("batteryLevel"),
        wifi_signal_strength=properties.get("config", {}).get("wifi", {}).get("signalStrength"),
        last_seen=last_seen,
        uptime=None,  # Would need to be calculated from events
        firmware_version=properties.get("firmware", {}).get("version", "unknown"),
        sensor_count=len(properties.get("hardware", {}).get("sensors", []))
    )

# IoT Data Ingestion (Device → Server)
@router.post("/{device_id}/readings")
def receive_readings(
    device_id: UUID,
    readings_request: DeviceReadingsRequest,
    device: Entity = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """Receive sensor readings from ESP32 device."""
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )
    
    # Store readings
    readings_data = []
    for reading in readings_request.readings:
        reading_dict = reading.dict()
        reading_dict["timestamp"] = reading.timestamp or datetime.utcnow()
        readings_data.append(reading_dict)
    
    events = ReadingCRUD.store_readings(db, device_id, readings_data)
    
    # Update device last seen
    DeviceCRUD.update_device_status(
        db, 
        device_id, 
        "online",
        battery_level=readings_request.readings[0].battery_level if readings_request.readings else None
    )
    
    return {
        "status": "ok",
        "readings_stored": len(events),
        "device_id": str(device_id)
    }

@router.post("/{device_id}/heartbeat")
def device_heartbeat(
    device_id: UUID,
    status_update: DeviceStatusUpdate,
    device: Entity = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """Device heartbeat/keep-alive."""
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID mismatch"
        )
    
    # Update device status
    DeviceCRUD.update_device_status(
        db,
        device_id,
        status_update.status.value,
        battery_level=status_update.battery_level
    )
    
    return {"status": "ok", "device_id": str(device_id)}

# Data Retrieval
@router.get("/{device_id}/readings")
def get_device_readings(
    device_id: UUID,
    params: ReadingQueryParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical readings for a device."""
    device = DeviceCRUD.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Check organization access
    if current_user.entity.organization_id != device.organization_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this device"
        )
    
    # Calculate pagination
    skip = (params.page - 1) * params.per_page
    
    # Get readings
    readings = ReadingCRUD.get_readings(
        db=db,
        device_id=device_id,
        start_time=params.start_time,
        end_time=params.end_time,
        sensor_type=params.sensor_type,
        skip=skip,
        limit=params.per_page
    )
    
    return {
        "readings": [
            {
                "id": reading.id,
                "device_id": str(reading.entity_id),
                "sensor_type": reading.data.get("sensor_type"),
                "value": reading.data.get("value"),
                "unit": reading.data.get("unit"),
                "timestamp": reading.timestamp,
                "quality": reading.data.get("quality", "good"),
                "battery_level": reading.data.get("battery_level")
            } for reading in readings
        ],
        "total": len(readings),  # This should be a count query in production
        "page": params.page,
        "per_page": params.per_page
    } 