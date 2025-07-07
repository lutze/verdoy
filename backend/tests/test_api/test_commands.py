"""
Tests for device control and commands API endpoints.

This module tests the commands endpoints:
- Command creation and management
- Command execution and status tracking
- Device-specific commands
- Command history and retrieval
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json


class TestCommandsEndpoints:
    """Test suite for device control and commands API endpoints."""

    def test_create_command_success(self, authenticated_client: TestClient, test_device):
        """Test successful command creation."""
        # Arrange
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {
                "delay": 5,
                "reason": "scheduled maintenance"
            },
            "priority": "normal"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["device_id"] == str(test_device.id)
        assert data["command_type"] == "reboot"
        assert data["status"] == "pending"
        assert "created_at" in data

    def test_create_command_invalid_device(self, authenticated_client: TestClient):
        """Test command creation with invalid device ID fails."""
        # Arrange
        command_data = {
            "device_id": "invalid-uuid",
            "command_type": "reboot",
            "parameters": {}
        }
        
        # Act
        response = authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Assert
        assert response.status_code == 422

    def test_create_command_invalid_type(self, authenticated_client: TestClient, test_device):
        """Test command creation with invalid command type fails."""
        # Arrange
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "invalid_command",
            "parameters": {}
        }
        
        # Act
        response = authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Assert
        assert response.status_code == 422

    def test_create_command_unauthorized(self, client: TestClient, test_device):
        """Test command creation without authentication fails."""
        # Arrange
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        
        # Act
        response = client.post("/api/v1/commands", json=command_data)
        
        # Assert
        assert response.status_code == 401

    def test_get_commands_success(self, authenticated_client: TestClient, test_device):
        """Test successful commands retrieval."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Act
        response = authenticated_client.get("/api/v1/commands")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "commands" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["commands"]) > 0

    def test_get_commands_with_filters(self, authenticated_client: TestClient, test_device):
        """Test commands retrieval with filters."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Act
        response = authenticated_client.get(
            f"/api/v1/commands?device_id={test_device.id}&status=pending&limit=5"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["commands"]) <= 5
        for command in data["commands"]:
            assert command["device_id"] == str(test_device.id)
            assert command["status"] == "pending"

    def test_get_commands_unauthorized(self, client: TestClient):
        """Test commands retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/commands")
        
        # Assert
        assert response.status_code == 401

    def test_get_command_by_id_success(self, authenticated_client: TestClient, test_device):
        """Test successful command retrieval by ID."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/commands/{command_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == command_id
        assert data["device_id"] == str(test_device.id)
        assert data["command_type"] == "reboot"

    def test_get_command_by_id_not_found(self, authenticated_client: TestClient):
        """Test command retrieval with non-existent ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/commands/invalid-uuid")
        
        # Assert
        assert response.status_code == 404

    def test_update_command_status_success(self, authenticated_client: TestClient, test_device):
        """Test successful command status update."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Act
        status_data = {
            "status": "executing",
            "result": {
                "message": "Command is being executed"
            }
        }
        response = authenticated_client.put(f"/api/v1/commands/{command_id}/status", json=status_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "executing"
        assert "result" in data

    def test_update_command_status_invalid_status(self, authenticated_client: TestClient, test_device):
        """Test command status update with invalid status fails."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Act
        status_data = {
            "status": "invalid_status",
            "result": {}
        }
        response = authenticated_client.put(f"/api/v1/commands/{command_id}/status", json=status_data)
        
        # Assert
        assert response.status_code == 422

    def test_cancel_command_success(self, authenticated_client: TestClient, test_device):
        """Test successful command cancellation."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.post(f"/api/v1/commands/{command_id}/cancel")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert "cancelled_at" in data

    def test_cancel_command_already_executed(self, authenticated_client: TestClient, test_device):
        """Test command cancellation of already executed command fails."""
        # Arrange - Create and execute a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Execute the command
        status_data = {"status": "completed", "result": {}}
        authenticated_client.put(f"/api/v1/commands/{command_id}/status", json=status_data)
        
        # Act - Try to cancel
        response = authenticated_client.post(f"/api/v1/commands/{command_id}/cancel")
        
        # Assert
        assert response.status_code == 400

    def test_get_device_commands_success(self, authenticated_client: TestClient, test_device):
        """Test successful device-specific commands retrieval."""
        # Arrange - Create a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        authenticated_client.post("/api/v1/commands", json=command_data)
        
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{test_device.id}/commands")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "commands" in data
        assert "total" in data
        assert len(data["commands"]) > 0
        for command in data["commands"]:
            assert command["device_id"] == str(test_device.id)

    def test_get_device_commands_invalid_device(self, authenticated_client: TestClient):
        """Test device commands with invalid device ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/devices/invalid-uuid/commands")
        
        # Assert
        assert response.status_code == 422

    def test_get_device_commands_unauthorized(self, client: TestClient, test_device):
        """Test device commands without authentication fails."""
        # Act
        response = client.get(f"/api/v1/devices/{test_device.id}/commands")
        
        # Assert
        assert response.status_code == 401

    def test_execute_device_command_success(self, authenticated_client: TestClient, test_device):
        """Test successful device command execution."""
        # Arrange
        command_data = {
            "command_type": "reboot",
            "parameters": {
                "delay": 10,
                "reason": "test execution"
            }
        }
        
        # Act
        response = authenticated_client.post(
            f"/api/v1/devices/{test_device.id}/commands/execute",
            json=command_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "command_id" in data
        assert "status" in data
        assert data["status"] == "pending"

    def test_execute_device_command_invalid_type(self, authenticated_client: TestClient, test_device):
        """Test device command execution with invalid type fails."""
        # Arrange
        command_data = {
            "command_type": "invalid_command",
            "parameters": {}
        }
        
        # Act
        response = authenticated_client.post(
            f"/api/v1/devices/{test_device.id}/commands/execute",
            json=command_data
        )
        
        # Assert
        assert response.status_code == 422

    def test_execute_device_command_unauthorized(self, client: TestClient, test_device):
        """Test device command execution without authentication fails."""
        # Arrange
        command_data = {
            "command_type": "reboot",
            "parameters": {}
        }
        
        # Act
        response = client.post(
            f"/api/v1/devices/{test_device.id}/commands/execute",
            json=command_data
        )
        
        # Assert
        assert response.status_code == 401

    def test_get_command_history_success(self, authenticated_client: TestClient, test_device):
        """Test successful command history retrieval."""
        # Arrange - Create and execute a command first
        command_data = {
            "device_id": str(test_device.id),
            "command_type": "reboot",
            "parameters": {}
        }
        create_response = authenticated_client.post("/api/v1/commands", json=command_data)
        command_id = create_response.json()["id"]
        
        # Execute the command
        status_data = {"status": "completed", "result": {"success": True}}
        authenticated_client.put(f"/api/v1/commands/{command_id}/status", json=status_data)
        
        # Act
        response = authenticated_client.get(f"/api/v1/commands/{command_id}/history")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) > 0
        assert "status" in data["history"][0]
        assert "timestamp" in data["history"][0]

    def test_get_command_history_not_found(self, authenticated_client: TestClient):
        """Test command history with non-existent command fails."""
        # Act
        response = authenticated_client.get("/api/v1/commands/invalid-uuid/history")
        
        # Assert
        assert response.status_code == 404 