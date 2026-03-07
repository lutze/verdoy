"""
Tests for ReadingService SQL-level filtering.

These tests cover the refactor from Python-side filtering to SQL WHERE clauses
for JSONB sensor_type filtering and timestamp range filtering.
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.reading_service import ReadingService
from app.models.reading import Reading
from app.schemas.reading import ReadingCreate


class TestReadingServiceSensorTypeFiltering:
    """Test JSONB-based sensor_type filtering in SQL."""

    def test_filter_by_sensor_type_returns_only_matching(
        self, reading_service: ReadingService, test_device, db_session: Session
    ):
        """Filtering by sensor_type should return only readings of that type."""
        # Create readings with different sensor types
        for sensor, value in [("temperature", 25.0), ("humidity", 60.0), ("temperature", 26.0)]:
            reading_service.create_reading(ReadingCreate(
                device_id=test_device.id,
                sensor_type=sensor,
                value=value,
                unit="celsius" if sensor == "temperature" else "percent",
                timestamp="2024-01-01T12:00:00Z",
            ))

        temp_readings = reading_service.get_readings_by_device(
            test_device.id, sensor_type="temperature"
        )
        humidity_readings = reading_service.get_readings_by_device(
            test_device.id, sensor_type="humidity"
        )

        assert len(temp_readings) == 2
        assert all(r.get_sensor_type() == "temperature" for r in temp_readings)
        assert len(humidity_readings) == 1
        assert humidity_readings[0].get_sensor_type() == "humidity"

    def test_filter_by_nonexistent_sensor_type_returns_empty(
        self, reading_service: ReadingService, test_device
    ):
        """Filtering by a sensor type with no readings should return empty list."""
        reading_service.create_reading(ReadingCreate(
            device_id=test_device.id,
            sensor_type="temperature",
            value=25.0,
            unit="celsius",
            timestamp="2024-01-01T12:00:00Z",
        ))

        readings = reading_service.get_readings_by_device(
            test_device.id, sensor_type="pressure"
        )
        assert readings == []

    def test_no_sensor_type_filter_returns_all(
        self, reading_service: ReadingService, test_device
    ):
        """No sensor_type filter should return all readings for the device."""
        for sensor in ["temperature", "humidity", "pressure"]:
            reading_service.create_reading(ReadingCreate(
                device_id=test_device.id,
                sensor_type=sensor,
                value=25.0,
                unit="unit",
                timestamp="2024-01-01T12:00:00Z",
            ))

        readings = reading_service.get_readings_by_device(test_device.id)
        assert len(readings) == 3


class TestReadingServiceTimestampFiltering:
    """Test timestamp range filtering in SQL."""

    def _create_readings_over_time(self, reading_service, device_id):
        """Helper to create readings at known timestamps."""
        base = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(5):
            ts = base + timedelta(minutes=i)
            reading_service.create_reading(ReadingCreate(
                device_id=device_id,
                sensor_type="temperature",
                value=20.0 + i,
                unit="celsius",
                timestamp=ts.isoformat() + "Z",
            ))

    def test_start_time_filter_excludes_earlier_readings(
        self, reading_service: ReadingService, test_device
    ):
        """Readings before start_time should be excluded."""
        self._create_readings_over_time(reading_service, test_device.id)

        readings = reading_service.get_readings_by_device(
            test_device.id, start_time="2024-01-01T12:02:00Z"
        )
        # Should get readings at 12:02, 12:03, 12:04
        assert len(readings) == 3

    def test_end_time_filter_excludes_later_readings(
        self, reading_service: ReadingService, test_device
    ):
        """Readings after end_time should be excluded."""
        self._create_readings_over_time(reading_service, test_device.id)

        readings = reading_service.get_readings_by_device(
            test_device.id, end_time="2024-01-01T12:02:00Z"
        )
        # Should get readings at 12:00, 12:01, 12:02
        assert len(readings) == 3

    def test_start_and_end_time_combined(
        self, reading_service: ReadingService, test_device
    ):
        """Both start_time and end_time should work together."""
        self._create_readings_over_time(reading_service, test_device.id)

        readings = reading_service.get_readings_by_device(
            test_device.id,
            start_time="2024-01-01T12:01:00Z",
            end_time="2024-01-01T12:03:00Z",
        )
        # Should get readings at 12:01, 12:02, 12:03
        assert len(readings) == 3

    def test_exact_timestamp_boundary_is_inclusive(
        self, reading_service: ReadingService, test_device
    ):
        """Readings at exactly start_time and end_time should be included."""
        reading_service.create_reading(ReadingCreate(
            device_id=test_device.id,
            sensor_type="temperature",
            value=25.0,
            unit="celsius",
            timestamp="2024-01-01T12:00:00Z",
        ))

        readings = reading_service.get_readings_by_device(
            test_device.id,
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:00:00Z",
        )
        assert len(readings) == 1

    def test_empty_range_returns_empty(
        self, reading_service: ReadingService, test_device
    ):
        """A time range with no readings should return empty list."""
        self._create_readings_over_time(reading_service, test_device.id)

        readings = reading_service.get_readings_by_device(
            test_device.id,
            start_time="2025-01-01T00:00:00Z",
            end_time="2025-01-01T01:00:00Z",
        )
        assert readings == []


class TestReadingServiceCombinedFilters:
    """Test sensor_type + timestamp filters working together."""

    def test_sensor_type_and_time_range_combined(
        self, reading_service: ReadingService, test_device
    ):
        """Combined sensor_type and time range should intersect correctly."""
        base = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(3):
            ts = base + timedelta(minutes=i)
            for sensor in ["temperature", "humidity"]:
                reading_service.create_reading(ReadingCreate(
                    device_id=test_device.id,
                    sensor_type=sensor,
                    value=25.0 + i,
                    unit="unit",
                    timestamp=ts.isoformat() + "Z",
                ))

        # Filter: temperature only, within first 2 minutes
        readings = reading_service.get_readings_by_device(
            test_device.id,
            sensor_type="temperature",
            start_time="2024-01-01T12:00:00Z",
            end_time="2024-01-01T12:01:00Z",
        )
        assert len(readings) == 2
        assert all(r.get_sensor_type() == "temperature" for r in readings)
