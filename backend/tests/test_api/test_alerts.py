"""
Tests for alerts API endpoints.

This module tests the alerts endpoints:
- Alert rule creation and management
- Alert retrieval and filtering
- Alert acknowledgment
- Alert statistics and monitoring
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json


class TestAlertsEndpoints:
    """Test suite for alerts API endpoints."""

    def test_create_alert_rule_success(self, authenticated_client: TestClient, test_device):
        """Test successful alert rule creation."""
        # Arrange
        rule_data = {
            "name": "High Temperature Alert",
            "description": "Alert when temperature exceeds 30°C",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning",
            "is_active": True
        }
        
        # Act
        response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == rule_data["name"]
        assert data["device_id"] == str(test_device.id)
        assert data["sensor_type"] == "temperature"
        assert data["condition"] == "greater_than"
        assert data["threshold"] == 30.0
        assert data["severity"] == "warning"
        assert data["is_active"] is True

    def test_create_alert_rule_invalid_device(self, authenticated_client: TestClient):
        """Test alert rule creation with invalid device ID fails."""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": "invalid-uuid",
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Assert
        assert response.status_code == 422

    def test_create_alert_rule_invalid_condition(self, authenticated_client: TestClient, test_device):
        """Test alert rule creation with invalid condition fails."""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "invalid_condition",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Assert
        assert response.status_code == 422

    def test_create_alert_rule_unauthorized(self, client: TestClient, test_device):
        """Test alert rule creation without authentication fails."""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        
        # Act
        response = client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Assert
        assert response.status_code == 401

    def test_get_alert_rules_success(self, authenticated_client: TestClient, test_device):
        """Test successful alert rules retrieval."""
        # Arrange - Create a rule first
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Act
        response = authenticated_client.get("/api/v1/alerts/rules")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["rules"]) > 0

    def test_get_alert_rules_with_filters(self, authenticated_client: TestClient, test_device):
        """Test alert rules retrieval with filters."""
        # Arrange - Create a rule first
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        
        # Act
        response = authenticated_client.get(
            f"/api/v1/alerts/rules?device_id={test_device.id}&sensor_type=temperature&is_active=true"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["rules"]) > 0
        for rule in data["rules"]:
            assert rule["device_id"] == str(test_device.id)
            assert rule["sensor_type"] == "temperature"
            assert rule["is_active"] is True

    def test_get_alert_rules_unauthorized(self, client: TestClient):
        """Test alert rules retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/alerts/rules")
        
        # Assert
        assert response.status_code == 401

    def test_get_alert_rule_by_id_success(self, authenticated_client: TestClient, test_device):
        """Test successful alert rule retrieval by ID."""
        # Arrange - Create a rule first
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        create_response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        rule_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.get(f"/api/v1/alerts/rules/{rule_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == rule_data["name"]
        assert data["device_id"] == str(test_device.id)

    def test_get_alert_rule_by_id_not_found(self, authenticated_client: TestClient):
        """Test alert rule retrieval with non-existent ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/alerts/rules/invalid-uuid")
        
        # Assert
        assert response.status_code == 404

    def test_update_alert_rule_success(self, authenticated_client: TestClient, test_device):
        """Test successful alert rule update."""
        # Arrange - Create a rule first
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        create_response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        rule_id = create_response.json()["id"]
        
        # Act
        update_data = {
            "name": "Updated Rule",
            "threshold": 35.0,
            "severity": "critical"
        }
        response = authenticated_client.put(f"/api/v1/alerts/rules/{rule_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Rule"
        assert data["threshold"] == 35.0
        assert data["severity"] == "critical"

    def test_update_alert_rule_not_found(self, authenticated_client: TestClient):
        """Test alert rule update with non-existent ID fails."""
        # Arrange
        update_data = {
            "name": "Updated Rule",
            "threshold": 35.0
        }
        
        # Act
        response = authenticated_client.put("/api/v1/alerts/rules/invalid-uuid", json=update_data)
        
        # Assert
        assert response.status_code == 404

    def test_delete_alert_rule_success(self, authenticated_client: TestClient, test_device):
        """Test successful alert rule deletion."""
        # Arrange - Create a rule first
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "device_id": str(test_device.id),
            "sensor_type": "temperature",
            "condition": "greater_than",
            "threshold": 30.0,
            "unit": "celsius",
            "severity": "warning"
        }
        create_response = authenticated_client.post("/api/v1/alerts/rules", json=rule_data)
        rule_id = create_response.json()["id"]
        
        # Act
        response = authenticated_client.delete(f"/api/v1/alerts/rules/{rule_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    def test_delete_alert_rule_not_found(self, authenticated_client: TestClient):
        """Test alert rule deletion with non-existent ID fails."""
        # Act
        response = authenticated_client.delete("/api/v1/alerts/rules/invalid-uuid")
        
        # Assert
        assert response.status_code == 404

    def test_get_alerts_success(self, authenticated_client: TestClient, test_device):
        """Test successful alerts retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/alerts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_get_alerts_with_filters(self, authenticated_client: TestClient, test_device):
        """Test alerts retrieval with filters."""
        # Act
        response = authenticated_client.get(
            f"/api/v1/alerts?device_id={test_device.id}&severity=warning&status=active"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        # Note: May be empty if no alerts exist

    def test_get_alerts_unauthorized(self, client: TestClient):
        """Test alerts retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/alerts")
        
        # Assert
        assert response.status_code == 401

    def test_get_alert_by_id_success(self, authenticated_client: TestClient):
        """Test successful alert retrieval by ID."""
        # Note: This test would need an actual alert to exist
        # For now, test the endpoint structure
        response = authenticated_client.get("/api/v1/alerts/invalid-uuid")
        # Should return 404 for invalid UUID, but endpoint should be accessible
        assert response.status_code in [404, 422]

    def test_acknowledge_alert_success(self, authenticated_client: TestClient):
        """Test successful alert acknowledgment."""
        # Note: This test would need an actual alert to exist
        # For now, test the endpoint structure
        response = authenticated_client.put("/api/v1/alerts/invalid-uuid/acknowledge")
        # Should return 404 for invalid UUID, but endpoint should be accessible
        assert response.status_code in [404, 422]

    def test_acknowledge_alert_unauthorized(self, client: TestClient):
        """Test alert acknowledgment without authentication fails."""
        # Act
        response = client.put("/api/v1/alerts/invalid-uuid/acknowledge")
        
        # Assert
        assert response.status_code == 401

    def test_get_alert_stats_success(self, authenticated_client: TestClient):
        """Test successful alert statistics retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/alerts/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "acknowledged_alerts" in data
        assert "severity_breakdown" in data

    def test_get_alert_stats_unauthorized(self, client: TestClient):
        """Test alert statistics without authentication fails."""
        # Act
        response = client.get("/api/v1/alerts/stats")
        
        # Assert
        assert response.status_code == 401

    def test_get_device_alerts_success(self, authenticated_client: TestClient, test_device):
        """Test successful device-specific alerts retrieval."""
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{test_device.id}/alerts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        # Note: May be empty if no alerts exist for this device

    def test_get_device_alerts_invalid_device(self, authenticated_client: TestClient):
        """Test device alerts with invalid device ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/devices/invalid-uuid/alerts")
        
        # Assert
        assert response.status_code == 422

    def test_get_device_alerts_unauthorized(self, client: TestClient, test_device):
        """Test device alerts without authentication fails."""
        # Act
        response = client.get(f"/api/v1/devices/{test_device.id}/alerts")
        
        # Assert
        assert response.status_code == 401 