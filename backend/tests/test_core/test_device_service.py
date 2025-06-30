"""
Tests for DeviceService - Device management and operations.

This module tests the fully implemented DeviceService functionality:
- Device registration and provisioning
- Device status monitoring
- Device configuration management
- Device data collection
- Device command execution
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.device_service import DeviceService
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceStatus
from app.exceptions import (
    DeviceAlreadyExistsException,
    DeviceNotFoundException,
    ValidationException,
    ServiceException
)


class TestDeviceService:
    """Test suite for DeviceService functionality."""

    def test_register_device_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device registration."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        
        # Act
        device = device_service.register_device(device_create, test_organization.id)
        
        # Assert
        assert device is not None
        assert device.name == test_device_data["name"]
        assert device.serial_number == test_device_data["serial_number"]
        assert device.device_type == test_device_data["device_type"]
        assert device.model == test_device_data["model"]
        assert device.firmware_version == test_device_data["firmware_version"]
        assert device.organization_id == test_organization.id
        assert device.status == DeviceStatus.REGISTERED
        assert device.is_active is True
        assert device.created_at is not None

    def test_register_device_duplicate_serial(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device registration with duplicate serial number fails."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device_service.register_device(device_create, test_organization.id)  # First registration
        
        # Act & Assert
        with pytest.raises(DeviceAlreadyExistsException):
            device_service.register_device(device_create, test_organization.id)  # Second registration should fail

    def test_register_device_invalid_data(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device registration with invalid data fails."""
        # Arrange
        test_device_data["serial_number"] = ""  # Invalid empty serial number
        device_create = DeviceCreate(**test_device_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            device_service.register_device(device_create, test_organization.id)

    def test_update_device_status_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device status update."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        new_status = DeviceStatus.ONLINE
        metadata = {"ip_address": "192.168.1.100", "signal_strength": -45}
        
        # Act
        updated_device = device_service.update_device_status(device.id, new_status, metadata)
        
        # Assert
        assert updated_device is not None
        assert updated_device.status == new_status
        assert updated_device.status_metadata == metadata
        assert updated_device.last_status_update is not None
        assert updated_device.last_seen is not None  # Should be updated for ONLINE status

    def test_update_device_status_offline(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device status update to offline."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        updated_device = device_service.update_device_status(device.id, DeviceStatus.OFFLINE)
        
        # Assert
        assert updated_device is not None
        assert updated_device.status == DeviceStatus.OFFLINE
        assert updated_device.last_status_update is not None

    def test_get_devices_by_organization(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test getting devices by organization."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device_service.register_device(device_create, test_organization.id)
        
        # Create second device
        test_device_data["serial_number"] = "TEST987654321"
        test_device_data["name"] = "Test Device 2"
        device_create2 = DeviceCreate(**test_device_data)
        device_service.register_device(device_create2, test_organization.id)
        
        # Act
        devices = device_service.get_devices_by_organization(test_organization.id)
        
        # Assert
        assert len(devices) == 2
        assert all(device.organization_id == test_organization.id for device in devices)

    def test_get_devices_by_organization_with_status_filter(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test getting devices by organization with status filter."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Update device status to ONLINE
        device_service.update_device_status(device.id, DeviceStatus.ONLINE)
        
        # Act
        online_devices = device_service.get_devices_by_organization(test_organization.id, DeviceStatus.ONLINE)
        offline_devices = device_service.get_devices_by_organization(test_organization.id, DeviceStatus.OFFLINE)
        
        # Assert
        assert len(online_devices) == 1
        assert len(offline_devices) == 0
        assert online_devices[0].id == device.id

    def test_get_offline_devices(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test getting offline devices."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Update device status to ONLINE
        device_service.update_device_status(device.id, DeviceStatus.ONLINE)
        
        # Act
        offline_devices = device_service.get_offline_devices(test_organization.id)
        
        # Assert
        assert len(offline_devices) == 0  # Device is online
        
        # Update device status to OFFLINE
        device_service.update_device_status(device.id, DeviceStatus.OFFLINE)
        
        # Act again
        offline_devices = device_service.get_offline_devices(test_organization.id)
        
        # Assert
        assert len(offline_devices) == 1
        assert offline_devices[0].id == device.id

    def test_update_device_configuration_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device configuration update."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        config_data = {
            "reading_interval": 300,
            "sensors": ["temperature", "humidity"],
            "alert_thresholds": {
                "temperature": {"min": 10, "max": 30},
                "humidity": {"min": 20, "max": 80}
            }
        }
        
        # Act
        updated_device = device_service.update_device_configuration(device.id, config_data)
        
        # Assert
        assert updated_device is not None
        assert updated_device.configuration == config_data
        assert updated_device.last_updated is not None

    def test_deactivate_device_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device deactivation."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        success = device_service.deactivate_device(device.id)
        
        # Assert
        assert success is True
        
        # Verify device is deactivated
        updated_device = device_service.get_by_id(device.id)
        assert updated_device.is_active is False

    def test_reactivate_device_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device reactivation."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        device_service.deactivate_device(device.id)
        
        # Act
        success = device_service.reactivate_device(device.id)
        
        # Assert
        assert success is True
        
        # Verify device is reactivated
        updated_device = device_service.get_by_id(device.id)
        assert updated_device.is_active is True

    def test_get_device_by_serial_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device retrieval by serial number."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        created_device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        device = device_service.get_device_by_serial(test_device_data["serial_number"])
        
        # Assert
        assert device is not None
        assert device.id == created_device.id
        assert device.serial_number == test_device_data["serial_number"]

    def test_get_device_by_serial_not_found(self, device_service: DeviceService):
        """Test device retrieval by non-existent serial number returns None."""
        # Act
        device = device_service.get_device_by_serial("NONEXISTENT123")
        
        # Assert
        assert device is None

    def test_device_exists_by_serial_true(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device existence check returns True for existing device."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device_service.register_device(device_create, test_organization.id)
        
        # Act
        exists = device_service.device_exists_by_serial(test_device_data["serial_number"])
        
        # Assert
        assert exists is True

    def test_device_exists_by_serial_false(self, device_service: DeviceService):
        """Test device existence check returns False for non-existent device."""
        # Act
        exists = device_service.device_exists_by_serial("NONEXISTENT123")
        
        # Assert
        assert exists is False

    def test_validate_device_data_success(self, device_service: DeviceService, test_device_data: dict):
        """Test successful device data validation."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        
        # Act
        result = device_service.validate_device_data(device_create)
        
        # Assert
        assert result is True

    def test_validate_device_data_invalid_serial(self, device_service: DeviceService, test_device_data: dict):
        """Test device data validation with invalid serial number fails."""
        # Arrange
        test_device_data["serial_number"] = ""  # Invalid empty serial number
        device_create = DeviceCreate(**test_device_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            device_service.validate_device_data(device_create)

    def test_validate_device_data_invalid_mac(self, device_service: DeviceService, test_device_data: dict):
        """Test device data validation with invalid MAC address fails."""
        # Arrange
        test_device_data["mac_address"] = "invalid-mac"  # Invalid MAC address
        device_create = DeviceCreate(**test_device_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            device_service.validate_device_data(device_create)

    def test_get_device_statistics(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device statistics retrieval."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device_service.register_device(device_create, test_organization.id)
        
        # Act
        stats = device_service.get_device_statistics(test_organization.id)
        
        # Assert
        assert stats is not None
        assert "total_devices" in stats
        assert "active_devices" in stats
        assert "online_devices" in stats
        assert "offline_devices" in stats
        assert stats["total_devices"] >= 1
        assert stats["active_devices"] >= 1

    def test_check_device_health(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test device health check."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        health = device_service.check_device_health(device.id)
        
        # Assert
        assert health is not None
        assert "status" in health
        assert "last_seen" in health
        assert "uptime" in health
        assert "firmware_version" in health
        assert health["firmware_version"] == test_device_data["firmware_version"]

    def test_get_by_id_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device retrieval by ID."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        created_device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        device = device_service.get_by_id(created_device.id)
        
        # Assert
        assert device is not None
        assert device.id == created_device.id
        assert device.name == test_device_data["name"]

    def test_get_by_id_not_found(self, device_service: DeviceService):
        """Test device retrieval by non-existent ID returns None."""
        # Arrange
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        
        # Act
        device = device_service.get_by_id(fake_id)
        
        # Assert
        assert device is None

    def test_get_by_id_or_raise_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device retrieval by ID with exception on not found."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        created_device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        device = device_service.get_by_id_or_raise(created_device.id)
        
        # Assert
        assert device is not None
        assert device.id == created_device.id

    def test_get_by_id_or_raise_not_found(self, device_service: DeviceService):
        """Test device retrieval by non-existent ID raises exception."""
        # Arrange
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        
        # Act & Assert
        with pytest.raises(DeviceNotFoundException):
            device_service.get_by_id_or_raise(fake_id)

    def test_create_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device creation using base service method."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        
        # Act
        device = device_service.create(device_create)
        
        # Assert
        assert device is not None
        assert device.name == test_device_data["name"]
        assert device.serial_number == test_device_data["serial_number"]

    def test_update_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device update using base service method."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        update_data = DeviceUpdate(name="Updated Device Name")
        
        # Act
        updated_device = device_service.update(device.id, update_data)
        
        # Assert
        assert updated_device is not None
        assert updated_device.name == "Updated Device Name"

    def test_delete_success(self, device_service: DeviceService, test_device_data: dict, test_organization):
        """Test successful device deletion using base service method."""
        # Arrange
        device_create = DeviceCreate(**test_device_data)
        device = device_service.register_device(device_create, test_organization.id)
        
        # Act
        success = device_service.delete(device.id)
        
        # Assert
        assert success is True
        
        # Verify device is deleted
        deleted_device = device_service.get_by_id(device.id)
        assert deleted_device is None 