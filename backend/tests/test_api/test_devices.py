"""
Tests for device management API endpoints.

This module tests the device management endpoints:
- Device registration
- Device listing and retrieval
- Device status updates
- Device configuration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestDeviceEndpoints:
    """Test suite for device management API endpoints."""

    def test_register_device_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device registration endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        
        # Act
        response = authenticated_client.post("/api/v1/devices", json=device_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == test_device_data["name"]
        assert data["serial_number"] == test_device_data["serial_number"]
        assert data["device_type"] == test_device_data["device_type"]

    def test_register_device_duplicate_serial(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test device registration with duplicate serial number fails."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        authenticated_client.post("/api/v1/devices", json=device_data)  # First registration
        
        # Act
        response = authenticated_client.post("/api/v1/devices", json=device_data)  # Second registration
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"].lower()

    def test_register_device_invalid_data(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test device registration with invalid data fails."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        device_data["serial_number"] = ""  # Invalid empty serial number
        
        # Act
        response = authenticated_client.post("/api/v1/devices", json=device_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_register_device_unauthorized(self, client: TestClient, test_device_data: dict, test_organization):
        """Test device registration without authentication fails."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        
        # Act
        response = client.post("/api/v1/devices", json=device_data)
        
        # Assert
        assert response.status_code == 401

    def test_get_devices_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device listing endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        authenticated_client.post("/api/v1/devices", json=device_data)
        
        # Act
        response = authenticated_client.get("/api/v1/devices")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert len(data["devices"]) >= 1
        assert data["devices"][0]["name"] == test_device_data["name"]

    def test_get_devices_unauthorized(self, client: TestClient):
        """Test device listing without authentication fails."""
        # Act
        response = client.get("/api/v1/devices")
        
        # Assert
        assert response.status_code == 401

    def test_get_device_by_id_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device retrieval by ID endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{device_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == device_id
        assert data["name"] == test_device_data["name"]
        assert data["serial_number"] == test_device_data["serial_number"]

    def test_get_device_by_id_not_found(self, authenticated_client: TestClient):
        """Test device retrieval by non-existent ID fails."""
        # Arrange
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{fake_device_id}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_get_device_by_id_unauthorized(self, client: TestClient):
        """Test device retrieval without authentication fails."""
        # Arrange
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = client.get(f"/api/v1/devices/{fake_device_id}")
        
        # Assert
        assert response.status_code == 401

    def test_update_device_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device update endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        update_data = {
            "name": "Updated Device Name",
            "description": "Updated description"
        }
        
        # Act
        response = authenticated_client.put(f"/api/v1/devices/{device_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Device Name"
        assert data["description"] == "Updated description"

    def test_update_device_not_found(self, authenticated_client: TestClient):
        """Test device update with non-existent ID fails."""
        # Arrange
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Updated Name"}
        
        # Act
        response = authenticated_client.put(f"/api/v1/devices/{fake_device_id}", json=update_data)
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_delete_device_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device deletion endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.delete(f"/api/v1/devices/{device_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    def test_delete_device_not_found(self, authenticated_client: TestClient):
        """Test device deletion with non-existent ID fails."""
        # Arrange
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = authenticated_client.delete(f"/api/v1/devices/{fake_device_id}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_get_device_status_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device status retrieval endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{device_id}/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_seen" in data
        assert "uptime" in data

    def test_get_device_status_not_found(self, authenticated_client: TestClient):
        """Test device status retrieval with non-existent ID fails."""
        # Arrange
        fake_device_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{fake_device_id}/status")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_update_device_status_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device status update endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        status_data = {
            "status": "online",
            "metadata": {
                "ip_address": "192.168.1.100",
                "signal_strength": -45
            }
        }
        
        # Act
        response = authenticated_client.post(f"/api/v1/devices/{device_id}/status", json=status_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "metadata" in data

    def test_get_device_config_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device configuration retrieval endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{device_id}/config")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "configuration" in data

    def test_update_device_config_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device configuration update endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        config_data = {
            "reading_interval": 300,
            "sensors": ["temperature", "humidity"],
            "alert_thresholds": {
                "temperature": {"min": 10, "max": 30}
            }
        }
        
        # Act
        response = authenticated_client.put(f"/api/v1/devices/{device_id}/config", json=config_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["configuration"]["reading_interval"] == 300
        assert "temperature" in data["configuration"]["sensors"]

    def test_get_device_health_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device health check endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{device_id}/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "firmware_version" in data
        assert "uptime" in data

    def test_reboot_device_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device reboot endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        create_response = authenticated_client.post("/api/v1/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.post(f"/api/v1/devices/{device_id}/reboot")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reboot" in data["message"].lower()

    def test_get_devices_by_organization_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device listing by organization endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        authenticated_client.post("/api/v1/devices", json=device_data)
        
        # Act
        response = authenticated_client.get(f"/api/v1/organizations/{test_organization.id}/devices")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert len(data["devices"]) >= 1
        assert data["devices"][0]["organization_id"] == str(test_organization.id)

    def test_get_device_statistics_success(self, authenticated_client: TestClient, test_device_data: dict, test_organization):
        """Test successful device statistics endpoint."""
        # Arrange
        device_data = {**test_device_data, "organization_id": str(test_organization.id)}
        authenticated_client.post("/api/v1/devices", json=device_data)
        
        # Act
        response = authenticated_client.get(f"/api/v1/organizations/{test_organization.id}/devices/statistics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_devices" in data
        assert "active_devices" in data
        assert "online_devices" in data
        assert "offline_devices" in data
        assert data["total_devices"] >= 1 