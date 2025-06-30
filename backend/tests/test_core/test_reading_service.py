"""
Tests for ReadingService - Sensor data processing and analytics.

This module tests the fully implemented ReadingService functionality:
- Reading data creation and storage
- Data aggregation and statistics
- Time-series data processing
- Data validation and quality checks
- Analytics and reporting
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.reading_service import ReadingService
from app.models.reading import Reading
from app.schemas.reading import ReadingCreate, ReadingUpdate
from app.exceptions import (
    ReadingNotFoundException,
    ValidationException,
    ServiceException
)


class TestReadingService:
    """Test suite for ReadingService functionality."""

    def test_create_reading_success(self, reading_service: ReadingService, test_device):
        """Test successful reading creation."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z",
            "metadata": {
                "accuracy": 0.1,
                "location": "indoor"
            }
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act
        reading = reading_service.create_reading(reading_create)
        
        # Assert
        assert reading is not None
        assert reading.device_id == test_device.id
        assert reading.sensor_type == "temperature"
        assert reading.value == 25.5
        assert reading.unit == "celsius"
        assert reading.metadata["accuracy"] == 0.1
        assert reading.metadata["location"] == "indoor"
        assert reading.created_at is not None

    def test_create_reading_invalid_device(self, reading_service: ReadingService):
        """Test reading creation with invalid device ID fails."""
        # Arrange
        fake_device_id = UUID('00000000-0000-0000-0000-000000000000')
        reading_data = {
            "device_id": fake_device_id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            reading_service.create_reading(reading_create)

    def test_create_reading_invalid_value(self, reading_service: ReadingService, test_device):
        """Test reading creation with invalid value fails."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": "invalid_value",  # Should be numeric
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            reading_service.create_reading(reading_create)

    def test_get_readings_by_device(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting readings by device."""
        # Act
        readings = reading_service.get_readings_by_device(test_device.id)
        
        # Assert
        assert len(readings) == 5  # From sample_readings fixture
        assert all(reading.device_id == test_device.id for reading in readings)

    def test_get_readings_by_device_with_filters(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting readings by device with filters."""
        # Act
        readings = reading_service.get_readings_by_device(
            test_device.id,
            sensor_type="temperature",
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:05:00Z"
        )
        
        # Assert
        assert len(readings) == 5  # All sample readings are temperature
        assert all(reading.sensor_type == "temperature" for reading in readings)

    def test_get_latest_readings(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting latest readings."""
        # Act
        latest_readings = reading_service.get_latest_readings(test_device.id)
        
        # Assert
        assert len(latest_readings) == 1  # Latest reading per sensor type
        assert latest_readings[0].device_id == test_device.id
        assert latest_readings[0].sensor_type == "temperature"

    def test_get_reading_statistics(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting reading statistics."""
        # Act
        stats = reading_service.get_reading_statistics(test_device.id)
        
        # Assert
        assert stats is not None
        assert "total_readings" in stats
        assert "sensor_types" in stats
        assert "value_range" in stats
        assert "average_value" in stats
        assert stats["total_readings"] == 5
        assert "temperature" in stats["sensor_types"]

    def test_get_reading_statistics_with_time_range(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting reading statistics with time range."""
        # Act
        stats = reading_service.get_reading_statistics(
            test_device.id,
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:05:00Z"
        )
        
        # Assert
        assert stats is not None
        assert stats["total_readings"] == 5

    def test_get_hourly_averages(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting hourly averages."""
        # Act
        hourly_avgs = reading_service.get_hourly_averages(
            test_device.id,
            sensor_type="temperature",
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T13:00:00Z"
        )
        
        # Assert
        assert hourly_avgs is not None
        assert len(hourly_avgs) > 0
        assert "hour" in hourly_avgs[0]
        assert "average_value" in hourly_avgs[0]

    def test_get_daily_averages(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting daily averages."""
        # Act
        daily_avgs = reading_service.get_daily_averages(
            test_device.id,
            sensor_type="temperature",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-02T00:00:00Z"
        )
        
        # Assert
        assert daily_avgs is not None
        assert len(daily_avgs) > 0
        assert "date" in daily_avgs[0]
        assert "average_value" in daily_avgs[0]

    def test_get_trends(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting reading trends."""
        # Act
        trends = reading_service.get_trends(
            test_device.id,
            sensor_type="temperature",
            period="1h"
        )
        
        # Assert
        assert trends is not None
        assert "trend" in trends
        assert "change_rate" in trends
        assert "direction" in trends

    def test_get_by_id_success(self, reading_service: ReadingService, test_device):
        """Test successful reading retrieval by ID."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        created_reading = reading_service.create_reading(reading_create)
        
        # Act
        reading = reading_service.get_by_id(created_reading.id)
        
        # Assert
        assert reading is not None
        assert reading.id == created_reading.id
        assert reading.value == 25.5

    def test_get_by_id_not_found(self, reading_service: ReadingService):
        """Test reading retrieval by non-existent ID returns None."""
        # Arrange
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        
        # Act
        reading = reading_service.get_by_id(fake_id)
        
        # Assert
        assert reading is None

    def test_get_by_id_or_raise_success(self, reading_service: ReadingService, test_device):
        """Test successful reading retrieval by ID with exception on not found."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        created_reading = reading_service.create_reading(reading_create)
        
        # Act
        reading = reading_service.get_by_id_or_raise(created_reading.id)
        
        # Assert
        assert reading is not None
        assert reading.id == created_reading.id

    def test_get_by_id_or_raise_not_found(self, reading_service: ReadingService):
        """Test reading retrieval by non-existent ID raises exception."""
        # Arrange
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        
        # Act & Assert
        with pytest.raises(ReadingNotFoundException):
            reading_service.get_by_id_or_raise(fake_id)

    def test_update_reading_success(self, reading_service: ReadingService, test_device):
        """Test successful reading update."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        reading = reading_service.create_reading(reading_create)
        
        update_data = ReadingUpdate(value=26.0, unit="fahrenheit")
        
        # Act
        updated_reading = reading_service.update(reading.id, update_data)
        
        # Assert
        assert updated_reading is not None
        assert updated_reading.value == 26.0
        assert updated_reading.unit == "fahrenheit"

    def test_delete_reading_success(self, reading_service: ReadingService, test_device):
        """Test successful reading deletion."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        reading = reading_service.create_reading(reading_create)
        
        # Act
        success = reading_service.delete(reading.id)
        
        # Assert
        assert success is True
        
        # Verify reading is deleted
        deleted_reading = reading_service.get_by_id(reading.id)
        assert deleted_reading is None

    def test_bulk_create_readings_success(self, reading_service: ReadingService, test_device):
        """Test successful bulk reading creation."""
        # Arrange
        readings_data = []
        for i in range(3):
            reading_data = {
                "device_id": test_device.id,
                "sensor_type": "temperature",
                "value": 20.0 + i,
                "unit": "celsius",
                "timestamp": f"2024-01-01T12:0{i}:00Z"
            }
            readings_data.append(ReadingCreate(**reading_data))
        
        # Act
        readings = reading_service.bulk_create_readings(readings_data)
        
        # Assert
        assert len(readings) == 3
        assert all(reading.device_id == test_device.id for reading in readings)

    def test_get_data_quality_metrics(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting data quality metrics."""
        # Act
        quality_metrics = reading_service.get_data_quality_metrics(test_device.id)
        
        # Assert
        assert quality_metrics is not None
        assert "completeness" in quality_metrics
        assert "accuracy" in quality_metrics
        assert "consistency" in quality_metrics
        assert "timeliness" in quality_metrics

    def test_validate_reading_data_success(self, reading_service: ReadingService, test_device):
        """Test successful reading data validation."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act
        result = reading_service.validate_reading_data(reading_create)
        
        # Assert
        assert result is True

    def test_validate_reading_data_invalid_value(self, reading_service: ReadingService, test_device):
        """Test reading data validation with invalid value fails."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": -999,  # Invalid value
            "unit": "celsius",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            reading_service.validate_reading_data(reading_create)

    def test_validate_reading_data_invalid_unit(self, reading_service: ReadingService, test_device):
        """Test reading data validation with invalid unit fails."""
        # Arrange
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 25.5,
            "unit": "invalid_unit",  # Invalid unit
            "timestamp": "2024-01-01T12:00:00Z"
        }
        reading_create = ReadingCreate(**reading_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            reading_service.validate_reading_data(reading_create)

    def test_get_reading_statistics_by_organization(self, reading_service: ReadingService, test_device, sample_readings):
        """Test getting reading statistics by organization."""
        # Act
        stats = reading_service.get_reading_statistics_by_organization(test_device.organization_id)
        
        # Assert
        assert stats is not None
        assert "total_readings" in stats
        assert "devices" in stats
        assert "sensor_types" in stats
        assert stats["total_readings"] >= 5

    def test_export_readings_csv(self, reading_service: ReadingService, test_device, sample_readings):
        """Test exporting readings to CSV."""
        # Act
        csv_data = reading_service.export_readings_csv(
            test_device.id,
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:05:00Z"
        )
        
        # Assert
        assert csv_data is not None
        assert isinstance(csv_data, str)
        assert "timestamp" in csv_data
        assert "sensor_type" in csv_data
        assert "value" in csv_data

    def test_export_readings_json(self, reading_service: ReadingService, test_device, sample_readings):
        """Test exporting readings to JSON."""
        # Act
        json_data = reading_service.export_readings_json(
            test_device.id,
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:05:00Z"
        )
        
        # Assert
        assert json_data is not None
        assert isinstance(json_data, list)
        assert len(json_data) == 5
        assert "timestamp" in json_data[0]
        assert "sensor_type" in json_data[0]
        assert "value" in json_data[0] 