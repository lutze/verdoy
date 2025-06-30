"""
Commands router for device command and control operations.

This router handles all device command operations including:
- Command queuing and management
- Device control operations
- Command execution tracking
- Bulk command operations
- Command templates and scheduling
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..dependencies import get_db, get_current_user, authenticate_device
from ..schemas.command import (
    CommandCreate,
    CommandResponse,
    CommandListResponse,
    CommandUpdate,
    CommandExecutionResponse,
    CommandTemplateCreate,
    CommandTemplateResponse,
    CommandQueryParams
)
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..models.device import Device
from ..models.command import Command
from ..exceptions import (
    DeviceNotFoundException,
    AccessDeniedException,
    CommandNotFoundException,
    ValidationException
)

router = APIRouter(tags=["commands"])

# ============================================================================
# COMMAND MANAGEMENT (Web Interface)
# ============================================================================

@router.get("", response_model=CommandListResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}
})
async def list_commands(
    params: CommandQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List commands across all devices.
    
    Returns a paginated list of commands with filtering options.
    """
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Get commands with filters
    commands = Command.get_commands(
        db=db,
        organization_id=organization_id,
        device_id=params.device_id,
        status=params.status,
        command_type=params.command_type,
        limit=params.limit,
        offset=params.offset
    )
    
    # Get total count
    total = Command.count_commands(
        db=db,
        organization_id=organization_id,
        device_id=params.device_id,
        status=params.status,
        command_type=params.command_type
    )
    
    return CommandListResponse(
        commands=[CommandResponse.from_model(command) for command in commands],
        total=total
    )

@router.post("", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def create_command(
    command_data: CommandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new command.
    
    Queues a command for execution on one or more devices.
    """
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Create command
    command = Command.create_command(
        db=db,
        command_data=command_data,
        organization_id=organization_id,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

@router.get("/{command_id}", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_command(
    command_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get command details.
    
    Returns detailed information about a specific command.
    """
    command = Command.get_command(db, command_id)
    if not command:
        raise CommandNotFoundException(detail="Command not found")
    
    # Check organization access
    if not current_user.has_access_to_device(command.device):
        raise AccessDeniedException(detail="Access denied to this command")
    
    return CommandResponse.from_model(command)

@router.put("/{command_id}", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def update_command(
    command_id: UUID,
    command_data: CommandUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update command details.
    
    Updates command information and parameters.
    """
    command = Command.get_command(db, command_id)
    if not command:
        raise CommandNotFoundException(detail="Command not found")
    
    # Check organization access
    if not current_user.has_access_to_device(command.device):
        raise AccessDeniedException(detail="Access denied to this command")
    
    # Update command
    updated_command = Command.update_command(db, command_id, command_data)
    
    return CommandResponse.from_model(updated_command)

@router.delete("/{command_id}", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def delete_command(
    command_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a command.
    
    Removes a command from the queue if it hasn't been executed yet.
    """
    command = Command.get_command(db, command_id)
    if not command:
        raise CommandNotFoundException(detail="Command not found")
    
    # Check organization access
    if not current_user.has_access_to_device(command.device):
        raise AccessDeniedException(detail="Access denied to this command")
    
    # Delete command
    Command.delete_command(db, command_id)
    
    return BaseResponse(
        message="Command successfully deleted",
        success=True
    )

# ============================================================================
# DEVICE-SPECIFIC COMMANDS
# ============================================================================

@router.get("/devices/{device_id}/commands", response_model=CommandListResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def get_device_commands(
    device_id: UUID,
    status: Optional[str] = Query(None, description="Filter by command status"),
    limit: int = Query(50, description="Number of commands to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get commands for a specific device.
    
    Returns commands queued for a specific device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Get device commands
    commands = Command.get_device_commands(
        db=db,
        device_id=device_id,
        status=status,
        limit=limit
    )
    
    return CommandListResponse(
        commands=[CommandResponse.from_model(command) for command in commands],
        total=len(commands)
    )

@router.post("/devices/{device_id}/commands", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def create_device_command(
    device_id: UUID,
    command_data: CommandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a command for a specific device.
    
    Queues a command for execution on a specific device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Create command for specific device
    command = Command.create_device_command(
        db=db,
        device_id=device_id,
        command_data=command_data,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

# ============================================================================
# DEVICE COMMAND POLLING (Device → Server)
# ============================================================================

@router.get("/devices/{device_id}/poll", response_model=List[CommandResponse], responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def poll_device_commands(
    device_id: UUID,
    device: Device = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """
    Poll for pending commands.
    
    Endpoint for devices to check for pending commands.
    Returns commands that are ready for execution.
    """
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device ID mismatch"
        )
    
    # Get pending commands for device
    commands = Command.get_pending_commands(db, device_id)
    
    return [CommandResponse.from_model(command) for command in commands]

@router.put("/devices/{device_id}/commands/{command_id}/execute", response_model=CommandExecutionResponse, responses={
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def mark_command_executed(
    device_id: UUID,
    command_id: UUID,
    execution_result: dict,
    device: Device = Depends(authenticate_device),
    db: Session = Depends(get_db)
):
    """
    Mark command as executed.
    
    Endpoint for devices to report command execution results.
    """
    # Verify device ID matches authenticated device
    if str(device.id) != str(device_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device ID mismatch"
        )
    
    # Mark command as executed
    command = Command.mark_executed(
        db=db,
        command_id=command_id,
        device_id=device_id,
        execution_result=execution_result
    )
    
    return CommandExecutionResponse.from_model(command)

# ============================================================================
# DEVICE CONTROL OPERATIONS
# ============================================================================

@router.post("/devices/{device_id}/control/restart", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def restart_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send restart command to device.
    
    Queues a restart command for the specified device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Create restart command
    command = Command.create_restart_command(
        db=db,
        device_id=device_id,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

@router.post("/devices/{device_id}/control/update-firmware", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def update_device_firmware(
    device_id: UUID,
    firmware_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send firmware update command to device.
    
    Queues a firmware update command for the specified device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Create firmware update command
    command = Command.create_firmware_update_command(
        db=db,
        device_id=device_id,
        firmware_url=firmware_url,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

@router.post("/devices/{device_id}/control/calibrate", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def calibrate_device(
    device_id: UUID,
    sensor_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send calibration command to device.
    
    Queues a sensor calibration command for the specified device.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Create calibration command
    command = Command.create_calibration_command(
        db=db,
        device_id=device_id,
        sensor_type=sensor_type,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

@router.post("/devices/{device_id}/control/set-reading-interval", response_model=CommandResponse, responses={
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse}
})
async def set_reading_interval(
    device_id: UUID,
    interval_seconds: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set device reading interval.
    
    Queues a command to change the sensor reading interval.
    """
    device = Device.get_device(db, device_id)
    if not device:
        raise DeviceNotFoundException(detail="Device not found")
    
    # Check organization access
    if not current_user.has_access_to_device(device):
        raise AccessDeniedException(detail="Access denied to this device")
    
    # Validate interval
    if interval_seconds < 60:
        raise ValidationException(detail="Reading interval must be at least 60 seconds")
    
    # Create interval change command
    command = Command.create_interval_command(
        db=db,
        device_id=device_id,
        interval_seconds=interval_seconds,
        created_by=current_user.email
    )
    
    return CommandResponse.from_model(command)

# ============================================================================
# COMMAND TEMPLATES
# ============================================================================

@router.get("/templates", response_model=List[CommandTemplateResponse], responses={
    401: {"model": ErrorResponse}
})
async def list_command_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List command templates.
    
    Returns available command templates for quick command creation.
    """
    templates = Command.get_templates(db)
    return [CommandTemplateResponse.from_model(template) for template in templates]

@router.post("/templates", response_model=CommandTemplateResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def create_command_template(
    template_data: CommandTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a command template.
    
    Creates a reusable command template for common operations.
    """
    template = Command.create_template(
        db=db,
        template_data=template_data,
        created_by=current_user.email
    )
    
    return CommandTemplateResponse.from_model(template)

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk", response_model=List[CommandResponse], responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def create_bulk_commands(
    device_ids: List[UUID],
    command_data: CommandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create commands for multiple devices.
    
    Queues the same command for multiple devices simultaneously.
    """
    # Get user's organization
    organization_id = current_user.entity.organization_id if current_user.entity else None
    
    # Create bulk commands
    commands = Command.create_bulk_commands(
        db=db,
        device_ids=device_ids,
        command_data=command_data,
        organization_id=organization_id,
        created_by=current_user.email
    )
    
    return [CommandResponse.from_model(command) for command in commands] 