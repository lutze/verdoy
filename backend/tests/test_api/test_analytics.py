"""
Tests for analytics API endpoints.

This module tests the analytics endpoints:
- Dashboard data and metrics
- Trend analysis and forecasting
- Performance monitoring
- Data visualization endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json


class TestAnalyticsEndpoints:
    """Test suite for analytics API endpoints."""

    def test_get_dashboard_data_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful dashboard data retrieval."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/dashboard")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "recent_activity" in data
        assert "device_status" in data
        assert "alerts_summary" in data

    def test_get_dashboard_data_unauthorized(self, client: TestClient):
        """Test dashboard data retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/analytics/dashboard")
        
        # Assert
        assert response.status_code == 401

    def test_get_trends_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful trends analysis."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/trends?sensor_type=temperature&period=7d")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "period" in data
        assert "sensor_type" in data
        assert "data_points" in data

    def test_get_trends_invalid_period(self, authenticated_client: TestClient):
        """Test trends analysis with invalid period fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/trends?period=invalid")
        
        # Assert
        assert response.status_code == 422

    def test_get_trends_unauthorized(self, client: TestClient):
        """Test trends analysis without authentication fails."""
        # Act
        response = client.get("/api/v1/analytics/trends")
        
        # Assert
        assert response.status_code == 401

    def test_get_performance_metrics_success(self, authenticated_client: TestClient, test_device):
        """Test successful performance metrics retrieval."""
        # Act
        response = authenticated_client.get(f"/api/v1/analytics/performance?device_id={test_device.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
        assert "uptime" in data
        assert "response_time" in data
        assert "error_rate" in data
        assert "data_quality" in data

    def test_get_performance_metrics_invalid_device(self, authenticated_client: TestClient):
        """Test performance metrics with invalid device ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/performance?device_id=invalid-uuid")
        
        # Assert
        assert response.status_code == 422

    def test_get_performance_metrics_unauthorized(self, client: TestClient, test_device):
        """Test performance metrics without authentication fails."""
        # Act
        response = client.get(f"/api/v1/analytics/performance?device_id={test_device.id}")
        
        # Assert
        assert response.status_code == 401

    def test_get_forecast_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful forecasting."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/forecast?sensor_type=temperature&horizon=24h")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "horizon" in data
        assert "sensor_type" in data
        assert "predictions" in data

    def test_get_forecast_invalid_horizon(self, authenticated_client: TestClient):
        """Test forecasting with invalid horizon fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/forecast?horizon=invalid")
        
        # Assert
        assert response.status_code == 422

    def test_get_forecast_unauthorized(self, client: TestClient):
        """Test forecasting without authentication fails."""
        # Act
        response = client.get("/api/v1/analytics/forecast")
        
        # Assert
        assert response.status_code == 401

    def test_get_device_analytics_success(self, authenticated_client: TestClient, test_device, sample_readings: list):
        """Test successful device-specific analytics."""
        # Act
        response = authenticated_client.get(f"/api/v1/analytics/devices/{test_device.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
        assert "readings_summary" in data
        assert "performance_metrics" in data
        assert "trends" in data

    def test_get_device_analytics_invalid_device(self, authenticated_client: TestClient):
        """Test device analytics with invalid device ID fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/devices/invalid-uuid")
        
        # Assert
        assert response.status_code == 422

    def test_get_device_analytics_unauthorized(self, client: TestClient, test_device):
        """Test device analytics without authentication fails."""
        # Act
        response = client.get(f"/api/v1/analytics/devices/{test_device.id}")
        
        # Assert
        assert response.status_code == 401

    def test_get_comparison_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful data comparison."""
        # Act
        response = authenticated_client.get(
            "/api/v1/analytics/comparison?sensor_type=temperature&period1=7d&period2=30d"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        assert "period1" in data
        assert "period2" in data
        assert "differences" in data

    def test_get_comparison_invalid_periods(self, authenticated_client: TestClient):
        """Test data comparison with invalid periods fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/comparison?period1=invalid")
        
        # Assert
        assert response.status_code == 422

    def test_get_comparison_unauthorized(self, client: TestClient):
        """Test data comparison without authentication fails."""
        # Act
        response = client.get("/api/v1/analytics/comparison")
        
        # Assert
        assert response.status_code == 401

    def test_get_anomaly_detection_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful anomaly detection."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/anomalies?sensor_type=temperature&threshold=2.0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert "threshold" in data
        assert "sensor_type" in data
        assert "detection_method" in data

    def test_get_anomaly_detection_invalid_threshold(self, authenticated_client: TestClient):
        """Test anomaly detection with invalid threshold fails."""
        # Act
        response = authenticated_client.get("/api/v1/analytics/anomalies?threshold=invalid")
        
        # Assert
        assert response.status_code == 422

    def test_get_anomaly_detection_unauthorized(self, client: TestClient):
        """Test anomaly detection without authentication fails."""
        # Act
        response = client.get("/api/v1/analytics/anomalies")
        
        # Assert
        assert response.status_code == 401

    def test_get_export_analytics_success(self, authenticated_client: TestClient, sample_readings: list):
        """Test successful analytics export."""
        # Act
        response = authenticated_client.post(
            "/api/v1/analytics/export",
            json={
                "report_type": "dashboard",
                "format": "pdf",
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-12-31T23:59:59Z"
                }
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert "status" in data
        assert data["status"] == "processing"

    def test_get_export_analytics_invalid_format(self, authenticated_client: TestClient):
        """Test analytics export with invalid format fails."""
        # Act
        response = authenticated_client.post(
            "/api/v1/analytics/export",
            json={
                "report_type": "dashboard",
                "format": "invalid",
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-12-31T23:59:59Z"
                }
            }
        )
        
        # Assert
        assert response.status_code == 422

    def test_get_export_analytics_unauthorized(self, client: TestClient):
        """Test analytics export without authentication fails."""
        # Act
        response = client.post(
            "/api/v1/analytics/export",
            json={
                "report_type": "dashboard",
                "format": "pdf"
            }
        )
        
        # Assert
        assert response.status_code == 401 