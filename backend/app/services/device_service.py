"""
Device service for IoT device management and operations.

This service handles:
- Device registration and provisioning
- Device status monitoring
- Device configuration management
- Device data collection
- Device command execution
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from uuid import UUID
import logging

from .base import BaseService
from ..models.device import Device
from ..models.organization import Organization
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceStatus
from ..exceptions import (
    ServiceException,
    ValidationException,
    DeviceAlreadyExistsException,
    DeviceNotFoundException,
    DeviceOfflineException
)

logger = logging.getLogger(__name__)


class DeviceService(BaseService[Device]):
    """
    Device service for IoT device management and operations.
    
    This service provides business logic for:
    - Device registration and provisioning
    - Device status monitoring and management
    - Device configuration and settings
    - Device data collection and processing
    - Device command execution and control
    """
    
    @property
    def model_class(self) -> type[Device]:
        """Return the Device model class."""
        return Device
    
    def register_device(self, device_data: DeviceCreate, organization_id: UUID) -> Device:
        """
        Register a new IoT device.
        
        Args:
            device_data: Device registration data
            organization_id: Organization ID for the device
            
        Returns:
            The created device
            
        Raises:
            DeviceAlreadyExistsException: If device already exists
            ValidationException: If data validation fails
            ServiceException: If registration fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate device data
            self.validate_device_data(device_data)
            
            # Check if device already exists
            if self.device_exists_by_serial(device_data.serial_number):
                raise DeviceAlreadyExistsException(f"Device with serial {device_data.serial_number} already exists")
            
            # Create device entity
            device = Device(
                name=device_data.name,
                serial_number=device_data.serial_number,
                device_type=device_data.device_type,
                model=device_data.model,
                firmware_version=device_data.firmware_version,
                organization_id=organization_id,
                status=DeviceStatus.REGISTERED,
                is_active=True
            )
            
            # Save to database
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            
            # Audit log
            self.audit_log("device_registered", device.id, {
                "serial_number": device.serial_number,
                "name": device.name,
                "device_type": device.device_type,
                "organization_id": str(organization_id)
            })
            
            # Performance monitoring
            self.performance_monitor("device_registration", start_time)
            
            logger.info(f"Device registered successfully: {device.serial_number}")
            return device
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during device registration: {e}")
            raise DeviceAlreadyExistsException("Device with this serial number already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during device registration: {e}")
            raise ServiceException("Failed to register device")
    
    def update_device_status(self, device_id: UUID, status: DeviceStatus, metadata: Optional[Dict] = None) -> Device:
        """
        Update device status and metadata.
        
        Args:
            device_id: The device ID
            status: New device status
            metadata: Optional status metadata
            
        Returns:
            The updated device
            
        Raises:
            DeviceNotFoundException: If device not found
            ServiceException: If update fails
        """
        try:
            # Get device
            device = self.get_by_id_or_raise(device_id)
            
            # Update status
            device.status = status
            device.last_status_update = datetime.utcnow()
            
            # Update metadata if provided
            if metadata:
                device.status_metadata = metadata
            
            # Update last seen if device is online
            if status in [DeviceStatus.ONLINE, DeviceStatus.ACTIVE]:
                device.last_seen = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(device)
            
            # Audit log
            self.audit_log("status_updated", device.id, {
                "serial_number": device.serial_number,
                "old_status": device.status,
                "new_status": status,
                "metadata": metadata
            })
            
            logger.info(f"Device status updated: {device.serial_number} -> {status}")
            return device
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating device status: {e}")
            raise ServiceException("Failed to update device status")
    
    def get_devices_by_organization(self, organization_id: UUID, status: Optional[DeviceStatus] = None) -> List[Device]:
        """
        Get devices for a specific organization.
        
        Args:
            organization_id: Organization ID
            status: Optional status filter
            
        Returns:
            List of devices
        """
        try:
            query = self.db.query(Device).filter(Device.organization_id == organization_id)
            
            if status:
                query = query.filter(Device.status == status)
            
            devices = query.all()
            logger.debug(f"Retrieved {len(devices)} devices for organization {organization_id}")
            return devices
            
        except Exception as e:
            logger.error(f"Error getting devices by organization: {e}")
            return []
    
    def get_offline_devices(self, organization_id: Optional[UUID] = None, hours_threshold: int = 24) -> List[Device]:
        """
        Get devices that haven't been seen recently.
        
        Args:
            organization_id: Optional organization filter
            hours_threshold: Hours threshold for offline detection
            
        Returns:
            List of offline devices
        """
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)
            
            query = self.db.query(Device).filter(
                Device.last_seen < threshold_time,
                Device.is_active == True
            )
            
            if organization_id:
                query = query.filter(Device.organization_id == organization_id)
            
            offline_devices = query.all()
            logger.debug(f"Found {len(offline_devices)} offline devices")
            return offline_devices
            
        except Exception as e:
            logger.error(f"Error getting offline devices: {e}")
            return []
    
    def update_device_configuration(self, device_id: UUID, config_data: Dict[str, Any]) -> Device:
        """
        Update device configuration.
        
        Args:
            device_id: The device ID
            config_data: Configuration data
            
        Returns:
            The updated device
            
        Raises:
            DeviceNotFoundException: If device not found
            ServiceException: If update fails
        """
        try:
            # Get device
            device = self.get_by_id_or_raise(device_id)
            
            # Update configuration
            device.configuration = config_data
            device.config_updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(device)
            
            # Audit log
            self.audit_log("configuration_updated", device.id, {
                "serial_number": device.serial_number,
                "config_keys": list(config_data.keys())
            })
            
            logger.info(f"Device configuration updated: {device.serial_number}")
            return device
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating device configuration: {e}")
            raise ServiceException("Failed to update device configuration")
    
    def deactivate_device(self, device_id: UUID) -> bool:
        """
        Deactivate a device.
        
        Args:
            device_id: The device ID
            
        Returns:
            True if device deactivated successfully
            
        Raises:
            DeviceNotFoundException: If device not found
            ServiceException: If deactivation fails
        """
        try:
            # Get device
            device = self.get_by_id_or_raise(device_id)
            
            # Deactivate device
            device.is_active = False
            device.deactivated_at = datetime.utcnow()
            device.status = DeviceStatus.DEACTIVATED
            
            self.db.commit()
            
            # Audit log
            self.audit_log("device_deactivated", device.id, {
                "serial_number": device.serial_number,
                "deactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Device deactivated: {device.serial_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating device: {e}")
            raise ServiceException("Failed to deactivate device")
    
    def reactivate_device(self, device_id: UUID) -> bool:
        """
        Reactivate a device.
        
        Args:
            device_id: The device ID
            
        Returns:
            True if device reactivated successfully
            
        Raises:
            DeviceNotFoundException: If device not found
            ServiceException: If reactivation fails
        """
        try:
            # Get device
            device = self.get_by_id_or_raise(device_id)
            
            # Reactivate device
            device.is_active = True
            device.deactivated_at = None
            device.status = DeviceStatus.REGISTERED
            
            self.db.commit()
            
            # Audit log
            self.audit_log("device_reactivated", device.id, {
                "serial_number": device.serial_number,
                "reactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Device reactivated: {device.serial_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating device: {e}")
            raise ServiceException("Failed to reactivate device")
    
    def get_device_by_serial(self, serial_number: str) -> Optional[Device]:
        """
        Get device by serial number.
        
        Args:
            serial_number: Device serial number
            
        Returns:
            Device if found, None otherwise
        """
        try:
            return self.db.query(Device).filter(Device.serial_number == serial_number).first()
        except Exception as e:
            logger.error(f"Error getting device by serial: {e}")
            return None
    
    def device_exists_by_serial(self, serial_number: str) -> bool:
        """
        Check if device exists by serial number.
        
        Args:
            serial_number: Device serial number
            
        Returns:
            True if device exists, False otherwise
        """
        try:
            return self.db.query(Device).filter(Device.serial_number == serial_number).first() is not None
        except Exception as e:
            logger.error(f"Error checking device existence by serial: {e}")
            return False
    
    def validate_device_data(self, device_data: DeviceCreate) -> bool:
        """
        Validate device registration data.
        
        Args:
            device_data: Device registration data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if not device_data.name:
            raise ValidationException("Device name is required")
        
        if not device_data.serial_number:
            raise ValidationException("Device serial number is required")
        
        if not device_data.device_type:
            raise ValidationException("Device type is required")
        
        if not device_data.model:
            raise ValidationException("Device model is required")
        
        return True
    
    def get_device_statistics(self, organization_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get device statistics for analytics.
        
        Args:
            organization_id: Optional organization filter
            
        Returns:
            Dictionary containing device statistics
        """
        try:
            query = self.db.query(Device)
            
            if organization_id:
                query = query.filter(Device.organization_id == organization_id)
            
            total_devices = query.count()
            active_devices = query.filter(Device.is_active == True).count()
            online_devices = query.filter(Device.status == DeviceStatus.ONLINE).count()
            offline_devices = query.filter(Device.status == DeviceStatus.OFFLINE).count()
            
            # Get devices registered in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_devices = query.filter(Device.created_at >= thirty_days_ago).count()
            
            return {
                "total_devices": total_devices,
                "active_devices": active_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,
                "new_devices_30_days": new_devices,
                "online_rate": (online_devices / active_devices * 100) if active_devices > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting device statistics: {e}")
            return {
                "total_devices": 0,
                "active_devices": 0,
                "online_devices": 0,
                "offline_devices": 0,
                "new_devices_30_days": 0,
                "online_rate": 0
            }
    
    def check_device_health(self, device_id: UUID) -> Dict[str, Any]:
        """
        Check device health status.
        
        Args:
            device_id: The device ID
            
        Returns:
            Dictionary containing device health information
            
        Raises:
            DeviceNotFoundException: If device not found
        """
        try:
            device = self.get_by_id_or_raise(device_id)
            
            # Calculate time since last seen
            time_since_last_seen = None
            if device.last_seen:
                time_since_last_seen = (datetime.utcnow() - device.last_seen).total_seconds()
            
            # Determine health status
            health_status = "healthy"
            if not device.is_active:
                health_status = "deactivated"
            elif device.status == DeviceStatus.OFFLINE:
                health_status = "offline"
            elif time_since_last_seen and time_since_last_seen > 3600:  # 1 hour
                health_status = "warning"
            
            return {
                "device_id": device.id,
                "serial_number": device.serial_number,
                "status": device.status,
                "health_status": health_status,
                "is_active": device.is_active,
                "last_seen": device.last_seen,
                "time_since_last_seen_seconds": time_since_last_seen,
                "firmware_version": device.firmware_version,
                "model": device.model
            }
            
        except Exception as e:
            logger.error(f"Error checking device health: {e}")
            raise ServiceException("Failed to check device health") 