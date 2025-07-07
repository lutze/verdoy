"""
Tests for readings API endpoints.

This module tests the readings endpoints:
- Data ingestion
- Reading retrieval and filtering
- Statistical aggregation
- Data export
- Device-specific readings
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json


class TestReadingsEndpoints:
    """Test suite for readings API endpoints."""

    def test_get_readings_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful readings retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/readings")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["readings"]) > 0

    def test_get_readings_with_filters(self, authenticated_client: TestClient, sample_readings: list):
        """Test readings retrieval with query parameters."""
        # Arrange
        device_id = sample_readings[0].device_id
        
        # Act
        response = authenticated_client.get(
            f"/api/v1/readings?device_id={device_id}&sensor_type=temperature&limit=5"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["readings"]) <= 5
        for reading in data["readings"]:
            assert reading["device_id"] == str(device_id)
            assert reading["sensor_type"] == "temperature"

    def test_get_readings_unauthorized(self, client: TestClient):
        """Test readings retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/readings")
        
        # Assert
        assert response.status_code == 401

    def test_get_latest_readings_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful latest readings retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/readings/latest")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        assert len(data["readings"]) > 0

    def test_get_latest_readings_with_device_filter(self, authenticated_client: TestClient, sample_readings: list):
        """Test latest readings with device filter."""
        # Arrange
        device_id = sample_readings[0].device_id
        
        # Act
        response = authenticated_client.get(f"/api/v1/readings/latest?device_id={device_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        for reading in data["readings"]:
            assert reading["device_id"] == str(device_id)

    def test_get_reading_stats_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful reading statistics retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/readings/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_readings" in data
        assert "devices_count" in data
        assert "sensor_types" in data
        assert "time_range" in data

    def test_get_reading_stats_with_filters(self, authenticated_client: TestClient, sample_readings: list):
        """Test reading statistics with filters."""
        # Arrange
        device_id = sample_readings[0].device_id
        
        # Act
        response = authenticated_client.get(f"/api/v1/readings/stats?device_id={device_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_readings" in data
        assert data["devices_count"] == 1

    def test_get_reading_aggregation_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful reading aggregation."""
        # Act
        response = authenticated_client.get("/api/v1/readings/aggregation?interval=1h&sensor_type=temperature")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "aggregations" in data
        assert "interval" in data
        assert "sensor_type" in data

    def test_get_reading_aggregation_invalid_interval(self, authenticated_client: TestClient):
        """Test reading aggregation with invalid interval fails."""
        # Act
        response = authenticated_client.get("/api/v1/readings/aggregation?interval=invalid")
        
        # Assert
        assert response.status_code == 422

    def test_export_readings_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful readings export."""
        # Act
        response = authenticated_client.post(
            "/api/v1/readings/export",
            json={
                "format": "csv",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert "status" in data
        assert data["status"] == "processing"

    def test_export_readings_invalid_format(self, authenticated_client: TestClient):
        """Test readings export with invalid format fails."""
        # Act
        response = authenticated_client.post(
            "/api/v1/readings/export",
            json={
                "format": "invalid",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            }
        )
        
        # Assert
        assert response.status_code == 422

    def test_get_device_readings_success(self, authenticated_client: TestClient, test_device, sample_readings: list):
        """Test successful device-specific readings retrieval."""
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{test_device.id}/readings")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    def test_get_device_readings_invalid_device(self, authenticated_client: TestClient):
        """Test device readings with invalid device ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/devices/invalid-uuid/readings")
        
        # Assert
        assert response.status_code == 422

    def test_get_device_readings_unauthorized(self, client: TestClient, test_device):
        """Test device readings without authentication fails."""
        # Act
        response = client.get(f"/api/v1/devices/{test_device.id}/readings")
        
        # Assert
        assert response.status_code == 401

    def test_get_latest_device_readings_success(self, authenticated_client: TestClient, test_device, sample_readings: list):
        """Test successful latest device readings retrieval."""
        # Act
        response = authenticated_client.get(f"/api/v1/devices/{test_device.id}/readings/latest")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "readings" in data
        assert len(data["readings"]) > 0

    def test_post_device_readings_success(self, authenticated_client: TestClient, test_device):
        """Test successful device readings submission."""
        # Arrange
        reading_data = {
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "accuracy": 0.1,
                "location": "indoor"
            }
        }
        
        # Act
        response = authenticated_client.post(
            f"/api/v1/devices/{test_device.id}/readings",
            json=reading_data
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["device_id"] == str(test_device.id)
        assert data["sensor_type"] == reading_data["sensor_type"]
        assert data["value"] == reading_data["value"]

    def test_post_device_readings_invalid_data(self, authenticated_client: TestClient, test_device):
        """Test device readings submission with invalid data fails."""
        # Arrange
        reading_data = {
            "sensor_type": "temperature",
            "value": "invalid",  # Should be numeric
            "unit": "celsius"
        }
        
        # Act
        response = authenticated_client.post(
            f"/api/v1/devices/{test_device.id}/readings",
            json=reading_data
        )
        
        # Assert
        assert response.status_code == 422

    def test_post_device_readings_unauthorized(self, client: TestClient, test_device):
        """Test device readings submission without authentication fails."""
        # Arrange
        reading_data = {
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius"
        }
        
        # Act
        response = client.post(
            f"/api/v1/devices/{test_device.id}/readings",
            json=reading_data
        )
        
        # Assert
        assert response.status_code == 401 