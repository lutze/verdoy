"""
Device model for VerdoyLab API.

This module contains the Device model and related functionality
for ESP32 device management and IoT operations.
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel
from .entity import Entity
from ..database import JSONType


class Device(Entity):
    """
    Device model for ESP32 devices.
    
    Maps to the existing entities table with entity_type = 'device.esp32'
    and stores device configuration in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'device.esp32',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for devices
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'device.esp32'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_by_device_name(cls, db, name: str):
        """
        Get device by name.
        
        Args:
            db: Database session
            name: Device name
            
        Returns:
            Device instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "device.esp32",
            cls.name == name
        ).first()
    
    @classmethod
    def get_by_device_id(cls, db, device_id: str):
        """
        Get device by device ID.
        
        Args:
            db: Database session
            device_id: Device ID (ESP32_XXXXXXXX format)
            
        Returns:
            Device instance or None
        """
        # Get all devices and filter in Python to avoid JSONB operator issues
        devices = db.query(cls).filter(cls.entity_type == "device.esp32").all()
        for device in devices:
            if device.get_property('name') == device_id:
                return device
        return None
    
    @classmethod
    def get_by_api_key(cls, db, api_key: str):
        """
        Get device by API key (stored in properties).
        
        Args:
            db: Database session
            api_key: Device API key
            
        Returns:
            Device instance or None
        """
        # Get all devices and filter in Python to avoid JSONB operator issues
        devices = db.query(cls).filter(cls.entity_type == "device.esp32").all()
        for device in devices:
            if device.get_property('apiKey') == api_key:
                return device
        return None
    
    @classmethod
    def get_online_devices(cls, db, user_id=None, organization_id=None):
        """
        Get all online devices.
        
        Args:
            db: Database session
            user_id: Optional user ID filter
            organization_id: Optional organization ID filter
            
        Returns:
            List of online device instances
        """
        # Get all devices and filter in Python to avoid JSONB operator issues
        devices = db.query(cls).filter(cls.entity_type == "device.esp32").all()
        
        # Filter by status
        online_devices = [device for device in devices if device.get_property('status') == "online"]
        
        # Apply additional filters
        if user_id:
            online_devices = [device for device in online_devices if device.organization_id == user_id]
        
        if organization_id:
            online_devices = [device for device in online_devices if device.organization_id == organization_id]
        
        return online_devices
    
    @classmethod
    def get_user_devices(cls, db, user_id, skip: int = 0, limit: int = 100):
        """
        Get devices belonging to a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of device instances
        """
        return db.query(cls).filter(
            cls.entity_type == "device.esp32",
            cls.organization_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_device_id(self) -> str:
        """
        Get device ID from properties.
        
        Returns:
            Device ID string
        """
        return self.get_property('name', '')
    
    def get_status(self) -> str:
        """
        Get device status from properties.
        
        Returns:
            Device status string
        """
        return self.get_property('status', 'offline')
    
    def update_status(self, status: str, **kwargs):
        """
        Update device status and related fields.
        
        Args:
            status: New status
            **kwargs: Additional fields to update
        """
        self.set_property('status', status)
        self.set_property('lastSeen', datetime.utcnow().isoformat())
        
        for key, value in kwargs.items():
            self.set_property(key, value)
    
    def is_online(self) -> bool:
        """
        Check if device is online.
        
        Returns:
            True if device is online, False otherwise
        """
        return self.get_status() == "online"
    
    def get_firmware_version(self) -> str:
        """
        Get firmware version from properties.
        
        Returns:
            Firmware version string
        """
        firmware = self.get_property('firmware', {})
        return firmware.get('version', '') if isinstance(firmware, dict) else ''
    
    def get_hardware_model(self) -> str:
        """
        Get hardware model from properties.
        
        Returns:
            Hardware model string
        """
        hardware = self.get_property('hardware', {})
        return hardware.get('model', '') if isinstance(hardware, dict) else ''
    
    def get_mac_address(self) -> str:
        """
        Get MAC address from properties.
        
        Returns:
            MAC address string
        """
        hardware = self.get_property('hardware', {})
        return hardware.get('macAddress', '') if isinstance(hardware, dict) else ''
    
    def get_sensors(self) -> list:
        """
        Get sensors list from properties.
        
        Returns:
            List of sensor configurations
        """
        hardware = self.get_property('hardware', {})
        return hardware.get('sensors', []) if isinstance(hardware, dict) else []
    
    def get_config(self) -> dict:
        """
        Get device configuration from properties.
        
        Returns:
            Device configuration dictionary
        """
        return self.get_property('config', {})
    
    def get_config_value(self, key: str, default=None):
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.get_config()
        return config.get(key, default) if isinstance(config, dict) else default
    
    def set_config_value(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        config = self.get_config()
        if not isinstance(config, dict):
            config = {}
        config[key] = value
        self.set_property('config', config)
    
    def get_location(self) -> str:
        """
        Get device location from properties.
        
        Returns:
            Device location string
        """
        return self.get_property('location', '')
    
    def get_battery_level(self) -> str:
        """
        Get battery level from properties.
        
        Returns:
            Battery level string
        """
        return self.get_property('batteryLevel', '')
    
    def get_last_seen(self) -> str:
        """
        Get last seen timestamp from properties.
        
        Returns:
            Last seen timestamp string
        """
        return self.get_property('lastSeen', '')
    
    def __repr__(self):
        """String representation of the device."""
        return f"<Device(id={self.id}, name={self.name}, status={self.get_status()})>" 