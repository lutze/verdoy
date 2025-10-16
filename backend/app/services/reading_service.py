"""
Reading service for sensor data processing and analytics.

This service handles:
- Sensor data ingestion and storage
- Data validation and processing
- Time-series data analysis
- Data aggregation and statistics
- Data export and reporting
"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging
import json

from .base import BaseService
from ..models.reading import Reading
from ..models.device import Device
from ..schemas.reading import ReadingCreate, ReadingUpdate
from ..exceptions import (
    ServiceException,
    ValidationException,
    DeviceNotFoundException,
    DataProcessingException,
    ReadingNotFoundException
)

logger = logging.getLogger(__name__)


class ReadingService(BaseService[Reading]):
    """
    Reading service for sensor data processing and analytics.
    
    This service provides business logic for:
    - Sensor data ingestion and validation
    - Time-series data storage and retrieval
    - Data aggregation and statistical analysis
    - Data export and reporting
    - Real-time data processing
    """
    
    @property
    def model_class(self) -> type[Reading]:
        """Return the Reading model class."""
        return Reading
    
    def ingest_reading(self, reading_data: ReadingCreate, device_id: UUID) -> Reading:
        """
        Ingest a new sensor reading.
        
        Args:
            reading_data: Sensor reading data
            device_id: Device ID that generated the reading
            
        Returns:
            The created reading
            
        Raises:
            DeviceNotFoundException: If device not found
            ValidationException: If data validation fails
            ServiceException: If ingestion fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate reading data
            self.validate_reading_data(reading_data)
            
            # Verify device exists and is active
            device = self.db.query(Device).filter(
                Device.id == device_id,
                Device.is_active == True
            ).first()
            
            if not device:
                raise DeviceNotFoundException(f"Device {device_id} not found or inactive")
            
            # Create reading entity
            reading = Reading(
                entity_id=device_id,
                entity_type="device.esp32",
                event_type="sensor.reading",
                timestamp=reading_data.timestamp or datetime.utcnow(),
                data={
                    'sensorType': reading_data.sensor_type,
                    'value': reading_data.value,
                    'unit': reading_data.unit,
                    'quality': getattr(reading_data, 'quality', 'good'),
                    'location': getattr(reading_data, 'location', None),
                    'batteryLevel': getattr(reading_data, 'battery_level', None),
                    'metadata': reading_data.metadata or {}
                },
                event_metadata={
                    'organization_id': str(device.organization_id) if device.organization_id else None
                }
            )
            
            # Save to database
            self.db.add(reading)
            self.db.commit()
            self.db.refresh(reading)
            
            # Audit log
            self.audit_log("reading_ingested", reading.id, {
                "device_id": str(device_id),
                "sensor_type": reading.sensor_type,
                "value": reading.value,
                "timestamp": reading.timestamp.isoformat()
            })
            
            # Performance monitoring
            self.performance_monitor("reading_ingestion", start_time)
            
            logger.info(f"Reading ingested: {reading.sensor_type} = {reading.value} {reading.unit}")
            return reading
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during reading ingestion: {e}")
            raise ServiceException("Failed to ingest reading")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during reading ingestion: {e}")
            raise ServiceException("Failed to ingest reading")
    
    def create_reading(self, reading_data: ReadingCreate) -> Reading:
        """
        Create a new sensor reading.
        
        Args:
            reading_data: Sensor reading data
            
        Returns:
            The created reading
            
        Raises:
            ValidationException: If data validation fails
            ServiceException: If creation fails
        """
        try:
            # Validate reading data
            self.validate_reading_data(reading_data)
            
            # Verify device exists and is active
            device = self.db.query(Device).filter(
                Device.id == reading_data.device_id,
                Device.is_active == True
            ).first()
            
            if not device:
                raise ValidationException(f"Device {reading_data.device_id} not found or inactive")
            
            # Create reading entity
            # Ensure timestamp is timezone-aware
            timestamp = reading_data.timestamp or datetime.utcnow()
            if timestamp.tzinfo is None:
                from datetime import timezone
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            reading = Reading(
                entity_id=reading_data.device_id,
                entity_type="device.esp32",
                event_type="sensor.reading",
                timestamp=timestamp,
                data={
                    'sensorType': reading_data.sensor_type,
                    'value': reading_data.value,
                    'unit': reading_data.unit,
                    'quality': getattr(reading_data, 'quality', 'good'),
                    'location': getattr(reading_data, 'location', None),
                    'batteryLevel': getattr(reading_data, 'battery_level', None),
                    'metadata': reading_data.metadata or {}
                },
                event_metadata={
                    'organization_id': str(device.organization_id) if device.organization_id else None
                }
            )
            
            # Save to database
            self.db.add(reading)
            self.db.commit()
            self.db.refresh(reading)
            
            logger.info(f"Reading created: {reading.get_sensor_type()} = {reading.get_value()} {reading.get_unit()}")
            return reading
            
        except ValidationException:
            # Re-raise validation exceptions as-is
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during reading creation: {e}")
            raise ServiceException("Failed to create reading")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during reading creation: {e}")
            raise ServiceException("Failed to create reading")
    
    def bulk_ingest_readings(self, readings_data: List[ReadingCreate], device_id: UUID) -> List[Reading]:
        """
        Ingest multiple sensor readings in a single transaction.
        
        Args:
            readings_data: List of sensor reading data
            device_id: Device ID that generated the readings
            
        Returns:
            List of created readings
            
        Raises:
            DeviceNotFoundException: If device not found
            ValidationException: If data validation fails
            ServiceException: If ingestion fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Verify device exists and is active
            device = self.db.query(Device).filter(
                Device.id == device_id,
                Device.is_active == True
            ).first()
            
            if not device:
                raise DeviceNotFoundException(f"Device {device_id} not found or inactive")
            
            readings = []
            
            for reading_data in readings_data:
                # Validate reading data
                self.validate_reading_data(reading_data)
                
                # Create reading entity
                reading = Reading(
                    device_id=device_id,
                    sensor_type=reading_data.sensor_type,
                    value=reading_data.value,
                    unit=reading_data.unit,
                    timestamp=reading_data.timestamp or datetime.utcnow(),
                    metadata=reading_data.metadata or {},
                    organization_id=device.organization_id
                )
                
                readings.append(reading)
                self.db.add(reading)
            
            # Save all readings
            self.db.commit()
            
            # Refresh all readings
            for reading in readings:
                self.db.refresh(reading)
            
            # Audit log
            self.audit_log("bulk_readings_ingested", device_id, {
                "device_id": str(device_id),
                "count": len(readings),
                "sensor_types": list(set(r.sensor_type for r in readings))
            })
            
            # Performance monitoring
            self.performance_monitor("bulk_reading_ingestion", start_time)
            
            logger.info(f"Bulk readings ingested: {len(readings)} readings for device {device_id}")
            return readings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during bulk reading ingestion: {e}")
            raise ServiceException("Failed to ingest readings")
    
    def get_readings_by_device(
        self, 
        device_id: UUID, 
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Reading]:
        """
        Get readings for a specific device with optional filtering.
        
        Args:
            device_id: Device ID
            sensor_type: Optional sensor type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of readings to return
            
        Returns:
            List of readings
        """
        try:
            logger.debug(f"Starting get_readings_by_device for device {device_id}")
            # Get all readings for the device
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            logger.debug(f"Retrieved {len(readings)} readings from database for device {device_id}")
            
            # Apply filters in Python for database-agnostic approach
            if sensor_type:
                logger.debug(f"Applying sensor_type filter: {sensor_type}")
                readings = [r for r in readings if r.get_sensor_type() == sensor_type]
                logger.debug(f"After sensor_type filter: {len(readings)} readings")
            
            if start_time:
                # Convert string timestamp to datetime if needed
                if isinstance(start_time, str):
                    # Parse the timestamp and ensure it's timezone-aware
                    if start_time.endswith('Z'):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        start_time = datetime.fromisoformat(start_time)
                # Make sure both timestamps are timezone-aware for comparison
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                
                # Convert database timestamps to timezone-aware for comparison
                readings = [r for r in readings if r.timestamp.replace(tzinfo=timezone.utc) >= start_time]
            
            if end_time:
                # Convert string timestamp to datetime if needed
                if isinstance(end_time, str):
                    # Parse the timestamp and ensure it's timezone-aware
                    if end_time.endswith('Z'):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        end_time = datetime.fromisoformat(end_time)
                # Make sure both timestamps are timezone-aware for comparison
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                
                # Convert database timestamps to timezone-aware for comparison
                readings = [r for r in readings if r.timestamp.replace(tzinfo=timezone.utc) <= end_time]
            
            # Sort by timestamp (most recent first) and limit
            readings.sort(key=lambda x: x.timestamp, reverse=True)
            readings = readings[:limit]
            
            logger.debug(f"Retrieved {len(readings)} readings for device {device_id}")
            return readings
            
        except Exception as e:
            logger.error(f"Error getting readings by device: {e}")
            return []
    
    def get_readings_by_organization(
        self, 
        organization_id: UUID,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Reading]:
        """
        Get readings for a specific organization with optional filtering.
        
        Args:
            organization_id: Organization ID
            sensor_type: Optional sensor type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of readings to return
            
        Returns:
            List of readings
        """
        try:
            from ..models.device import Device
            query = self.db.query(Reading).join(Device, Reading.entity_id == Device.id).filter(Device.organization_id == organization_id)
            
            # Note: sensor_type filtering will be done in Python after the join
            
            if start_time:
                query = query.filter(Reading.timestamp >= start_time)
            
            if end_time:
                query = query.filter(Reading.timestamp <= end_time)
            
            readings = query.order_by(desc(Reading.timestamp)).all()
            
            # Apply sensor_type filter in Python if specified
            if sensor_type:
                readings = [r for r in readings if r.get_sensor_type() == sensor_type]
            
            # Apply limit
            readings = readings[:limit]
            
            logger.debug(f"Retrieved {len(readings)} readings for organization {organization_id}")
            return readings
            
        except Exception as e:
            logger.error(f"Error getting readings by organization: {e}")
            return []
    
    def get_latest_readings(self, device_id: UUID, sensor_types: Optional[List[str]] = None) -> Dict[str, Reading]:
        """
        Get the latest reading for each sensor type on a device.
        
        Args:
            device_id: Device ID
            sensor_types: Optional list of sensor types to filter
            
        Returns:
            Dictionary mapping sensor types to their latest readings
        """
        try:
            # Get all readings for the device
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            
            # Filter by sensor types if provided
            if sensor_types:
                readings = [r for r in readings if r.get_sensor_type() in sensor_types]
            
            # Group by sensor type and get the latest for each
            latest_readings = {}
            for reading in readings:
                sensor_type = reading.get_sensor_type()
                if sensor_type not in latest_readings or reading.timestamp > latest_readings[sensor_type].timestamp:
                    latest_readings[sensor_type] = reading
            
            logger.debug(f"Retrieved latest readings for {len(latest_readings)} sensor types")
            return latest_readings
            
        except Exception as e:
            logger.error(f"Error getting latest readings: {e}")
            return {}
    
    def get_statistics(
        self, 
        device_id: UUID, 
        sensor_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get statistical analysis for a sensor type on a device.
        
        Args:
            device_id: Device ID
            sensor_type: Sensor type
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary containing statistical data
        """
        try:
            # Get all readings for the device
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            
            # Filter by sensor type and time range in Python
            filtered_readings = []
            for reading in readings:
                if reading.get_sensor_type() == sensor_type:
                    if start_time and reading.timestamp < start_time:
                        continue
                    if end_time and reading.timestamp > end_time:
                        continue
                    filtered_readings.append(reading)
            
            if not filtered_readings:
                return {
                    "count": 0,
                    "average": None,
                    "minimum": None,
                    "maximum": None,
                    "stddev": None,
                    "range": None
                }
            
            # Calculate statistics in Python
            values = [reading.get_value() for reading in filtered_readings]
            count = len(values)
            average = sum(values) / count
            minimum = min(values)
            maximum = max(values)
            
            # Calculate standard deviation
            variance = sum((x - average) ** 2 for x in values) / count
            stddev = variance ** 0.5
            
            return {
                "count": count,
                "average": float(average),
                "minimum": float(minimum),
                "maximum": float(maximum),
                "stddev": float(stddev),
                "range": float(maximum - minimum)
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "count": 0,
                "average": None,
                "minimum": None,
                "maximum": None,
                "stddev": None,
                "range": None
            }
    
    def get_hourly_averages(
        self, 
        device_id: UUID, 
        sensor_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get hourly averages for a sensor type over a time period.
        
        Args:
            device_id: Device ID
            sensor_type: Sensor type
            start_time: Start time
            end_time: End time
            
        Returns:
            List of hourly average data points
        """
        try:
            # Convert string timestamps to datetime if needed
            if isinstance(start_time, str):
                if start_time.endswith('Z'):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start_time)
            
            if isinstance(end_time, str):
                if end_time.endswith('Z'):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                else:
                    end_time = datetime.fromisoformat(end_time)
            
            # Generate hourly intervals
            intervals = []
            current_time = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_time <= end_time:
                next_hour = current_time + timedelta(hours=1)
                intervals.append((current_time, next_hour))
                current_time = next_hour
            
            hourly_averages = []
            
            # Get all readings for the device and sensor type
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            sensor_readings = [r for r in readings if r.get_sensor_type() == sensor_type]
            
            for interval_start, interval_end in intervals:
                # Filter readings for this hour
                # Make sure database timestamps are timezone-aware for comparison
                hour_readings = [
                    r for r in sensor_readings 
                    if interval_start <= r.timestamp.replace(tzinfo=timezone.utc) < interval_end
                ]
                
                # Calculate average for this hour
                if hour_readings:
                    values = [r.get_value() for r in hour_readings]
                    average = sum(values) / len(values)
                else:
                    average = None
                
                hourly_averages.append({
                    "timestamp": interval_start.isoformat(),
                    "average_value": float(average) if average is not None else None,
                    "hour": interval_start.hour,
                    "date": interval_start.date().isoformat()
                })
            
            return hourly_averages
            
        except Exception as e:
            logger.error(f"Error getting hourly averages: {e}")
            return []
    
    def get_daily_averages(
        self, 
        device_id: UUID, 
        sensor_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get daily averages for a sensor type over a date range.
        
        Args:
            device_id: Device ID
            sensor_type: Sensor type
            start_time: Start time
            end_time: End time
            
        Returns:
            List of daily average data points
        """
        try:
            # Convert string timestamps to datetime if needed
            if isinstance(start_time, str):
                if start_time.endswith('Z'):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start_time)
            
            if isinstance(end_time, str):
                if end_time.endswith('Z'):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                else:
                    end_time = datetime.fromisoformat(end_time)
            
            # Generate daily intervals
            intervals = []
            current_date = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            while current_date <= end_time:
                next_day = current_date + timedelta(days=1)
                intervals.append((current_date, next_day))
                current_date = next_day
            
            daily_averages = []
            
            # Get all readings for the device and sensor type
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            sensor_readings = [r for r in readings if r.get_sensor_type() == sensor_type]
            
            for interval_start, interval_end in intervals:
                # Filter readings for this day
                # Make sure database timestamps are timezone-aware for comparison
                day_readings = [
                    r for r in sensor_readings 
                    if interval_start <= r.timestamp.replace(tzinfo=timezone.utc) < interval_end
                ]
                
                # Calculate average for this day
                if day_readings:
                    values = [r.get_value() for r in day_readings]
                    average = sum(values) / len(values)
                else:
                    average = None
                
                daily_averages.append({
                    "date": interval_start.date().isoformat(),
                    "average_value": float(average) if average is not None else None,
                    "day_of_week": interval_start.strftime("%A"),
                    "month": interval_start.strftime("%B")
                })
            
            return daily_averages
            
        except Exception as e:
            logger.error(f"Error getting daily averages: {e}")
            return []
    
    def validate_reading_data(self, reading_data: ReadingCreate) -> bool:
        """
        Validate sensor reading data.
        
        Args:
            reading_data: Sensor reading data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if not reading_data.sensor_type:
            raise ValidationException("Sensor type is required")
        
        if reading_data.value is None:
            raise ValidationException("Reading value is required")
        
        if not isinstance(reading_data.value, (int, float)):
            raise ValidationException("Reading value must be numeric")
        
        # Validate unit based on sensor type
        valid_units = {
            "temperature": ["celsius", "fahrenheit", "kelvin"],
            "humidity": ["percent", "rh"],
            "pressure": ["pascal", "bar", "psi", "atm"],
            "ph": ["ph"],
            "dissolved_oxygen": ["mg/l", "ppm", "percent"],
            "turbidity": ["ntu", "ftu"],
            "conductivity": ["ms/cm", "us/cm", "s/m"],
            "flow": ["l/min", "ml/min", "gpm"],
            "level": ["cm", "m", "in", "ft"],
            "weight": ["g", "kg", "lb", "oz"],
            "volume": ["ml", "l", "gal", "qt"],
            "light": ["lux", "lumens", "fc"],
            "sound": ["db", "dba"],
            "motion": ["count", "events"],
            "vibration": ["g", "m/s2", "in/s2"]
        }
        
        if reading_data.sensor_type in valid_units:
            if reading_data.unit not in valid_units[reading_data.sensor_type]:
                raise ValidationException(f"Invalid unit '{reading_data.unit}' for sensor type '{reading_data.sensor_type}'. Valid units: {valid_units[reading_data.sensor_type]}")
        
        # Validate value ranges based on sensor type
        value_ranges = {
            "temperature": (-50, 200),  # Celsius range
            "humidity": (0, 100),  # Percentage
            "pressure": (0, 10000),  # Pascal range
            "ph": (0, 14),  # pH scale
            "dissolved_oxygen": (0, 20),  # mg/L range
            "turbidity": (0, 1000),  # NTU range
            "conductivity": (0, 10000),  # µS/cm range
        }
        
        if reading_data.sensor_type in value_ranges:
            min_val, max_val = value_ranges[reading_data.sensor_type]
            if not (min_val <= reading_data.value <= max_val):
                raise ValidationException(f"Value {reading_data.value} is outside valid range [{min_val}, {max_val}] for sensor type '{reading_data.sensor_type}'")
        
        if reading_data.timestamp:
            # Convert to UTC if timezone-aware, or assume UTC if naive
            if reading_data.timestamp.tzinfo is not None:
                # Timezone-aware datetime - convert to UTC
                utc_timestamp = reading_data.timestamp.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                # Timezone-naive datetime - assume it's UTC
                utc_timestamp = reading_data.timestamp
            
            # Compare with current UTC time
            if utc_timestamp > datetime.utcnow() + timedelta(minutes=5):
                raise ValidationException("Reading timestamp cannot be in the future")
        
        return True
    
    def get_reading_statistics(self, device_id: UUID, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get reading statistics for analytics.
        
        Args:
            device_id: Device ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary containing reading statistics
        """
        try:
            # Get all readings for the device
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            
            # Apply time filters if provided
            if start_time:
                # Convert string timestamp to datetime if needed
                if isinstance(start_time, str):
                    if start_time.endswith('Z'):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        start_time = datetime.fromisoformat(start_time)
                # Make sure both timestamps are timezone-aware for comparison
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                
                readings = [r for r in readings if r.timestamp.replace(tzinfo=timezone.utc) >= start_time]
            if end_time:
                # Convert string timestamp to datetime if needed
                if isinstance(end_time, str):
                    if end_time.endswith('Z'):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        end_time = datetime.fromisoformat(end_time)
                # Make sure both timestamps are timezone-aware for comparison
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                
                readings = [r for r in readings if r.timestamp.replace(tzinfo=timezone.utc) <= end_time]
            
            total_readings = len(readings)
            
            # Get readings in last 24 hours
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_readings = len([r for r in readings if r.timestamp.replace(tzinfo=timezone.utc) >= twenty_four_hours_ago])
            
            # Get unique sensor types and value range
            unique_sensor_types = set()
            all_values = []
            for reading in readings:
                unique_sensor_types.add(reading.get_sensor_type())
                all_values.append(reading.get_value())
            sensor_types = len(unique_sensor_types)
            
            # Calculate value range and average
            value_range = None
            average_value = None
            if all_values:
                value_range = max(all_values) - min(all_values)
                average_value = sum(all_values) / len(all_values)
            
            return {
                "total_readings": total_readings,
                "readings_24h": recent_readings,
                "sensor_types": sensor_types,
                "unique_devices": 1,  # Single device
                "readings_per_hour": recent_readings / 24 if recent_readings > 0 else 0,
                "value_range": float(value_range) if value_range is not None else None,
                "average_value": float(average_value) if average_value is not None else None
            }
            
        except Exception as e:
            logger.error(f"Error getting reading statistics: {e}")
            return {
                "total_readings": 0,
                "readings_24h": 0,
                "sensor_types": 0,
                "unique_devices": 0,
                "readings_per_hour": 0,
                "value_range": None,
                "average_value": None
            }
    
    def bulk_create_readings(self, readings_data: List[ReadingCreate]) -> List[Reading]:
        """
        Create multiple sensor readings in a single transaction.
        
        Args:
            readings_data: List of sensor reading data
            
        Returns:
            List of created readings
            
        Raises:
            ValidationException: If data validation fails
            ServiceException: If creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            readings = []
            
            for reading_data in readings_data:
                # Validate reading data
                self.validate_reading_data(reading_data)
                
                # Create reading entity
                timestamp = reading_data.timestamp or datetime.utcnow()
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                reading = Reading(
                    entity_id=reading_data.device_id,
                    entity_type="device.esp32",
                    event_type="sensor.reading",
                    timestamp=timestamp,
                    data={
                        'sensorType': reading_data.sensor_type,
                        'value': reading_data.value,
                        'unit': reading_data.unit,
                        'quality': getattr(reading_data, 'quality', 'good'),
                        'location': getattr(reading_data, 'location', None),
                        'batteryLevel': getattr(reading_data, 'battery_level', None),
                        'metadata': reading_data.metadata or {}
                    },
                    event_metadata={}
                )
                
                readings.append(reading)
                self.db.add(reading)
            
            # Save all readings
            self.db.commit()
            
            # Refresh all readings
            for reading in readings:
                self.db.refresh(reading)
            
            # Performance monitoring
            self.performance_monitor("bulk_reading_creation", start_time)
            
            logger.info(f"Bulk readings created: {len(readings)} readings")
            return readings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during bulk reading creation: {e}")
            raise ServiceException("Failed to create readings")
    
    def get_data_quality_metrics(self, device_id: UUID) -> Dict[str, Any]:
        """
        Get data quality metrics for a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Dictionary containing data quality metrics
        """
        try:
            # Get all readings for the device
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            
            if not readings:
                return {
                    "completeness": 0.0,
                    "accuracy": 0.0,
                    "consistency": 0.0,
                    "timeliness": 0.0
                }
            
            # Calculate completeness (percentage of expected readings)
            # Assume 1 reading per hour is expected
            hours_span = 24  # Last 24 hours
            expected_readings = hours_span
            actual_readings = len(readings)
            completeness = min(actual_readings / expected_readings, 1.0) if expected_readings > 0 else 0.0
            
            # Calculate accuracy (based on value ranges and outliers)
            values = [r.get_value() for r in readings if r.get_value() is not None]
            if values:
                # Simple accuracy based on value consistency
                mean_value = sum(values) / len(values)
                variance = sum((x - mean_value) ** 2 for x in values) / len(values)
                accuracy = max(0.0, 1.0 - (variance / (mean_value ** 2 + 1e-6)))
            else:
                accuracy = 0.0
            
            # Calculate consistency (based on timestamp intervals)
            if len(readings) > 1:
                timestamps = sorted([r.timestamp for r in readings])
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
                if intervals:
                    mean_interval = sum(intervals) / len(intervals)
                    interval_variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                    consistency = max(0.0, 1.0 - (interval_variance / (mean_interval ** 2 + 1e-6)))
                else:
                    consistency = 1.0
            else:
                consistency = 1.0
            
            # Calculate timeliness (based on how recent the latest reading is)
            if readings:
                latest_reading = max(readings, key=lambda x: x.timestamp)
                time_since_latest = (datetime.utcnow() - latest_reading.timestamp).total_seconds()
                # Timeliness decreases as time since latest reading increases
                timeliness = max(0.0, 1.0 - (time_since_latest / 3600))  # 1 hour = 0 timeliness
            else:
                timeliness = 0.0
            
            return {
                "completeness": float(completeness),
                "accuracy": float(accuracy),
                "consistency": float(consistency),
                "timeliness": float(timeliness)
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics: {e}")
            return {
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "timeliness": 0.0
            }
    
    def get_trends(
        self, 
        device_id: UUID, 
        sensor_type: str,
        period: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get trend analysis for a sensor type over a time period.
        
        Args:
            device_id: Device ID
            sensor_type: Sensor type
            period: Time period for analysis (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            # Calculate time range based on period
            now = datetime.now(timezone.utc)
            if period == "1h":
                start_time = now - timedelta(hours=1)
            elif period == "24h":
                start_time = now - timedelta(hours=24)
            elif period == "7d":
                start_time = now - timedelta(days=7)
            else:
                start_time = now - timedelta(hours=1)  # Default to 1 hour
            
            # Get readings for the time period
            readings = self.db.query(Reading).filter(Reading.entity_id == device_id).all()
            sensor_readings = [
                r for r in readings 
                if r.get_sensor_type() == sensor_type 
                and start_time <= r.timestamp.replace(tzinfo=timezone.utc) <= now
            ]
            
            if len(sensor_readings) < 2:
                return {
                    "trend": "insufficient_data",
                    "slope": 0.0,
                    "direction": "stable",
                    "confidence": 0.0,
                    "r_squared": 0.0
                }
            
            # Sort by timestamp
            sensor_readings.sort(key=lambda x: x.timestamp)
            
            # Simple linear trend calculation
            values = [r.get_value() for r in sensor_readings]
            timestamps = [r.timestamp for r in sensor_readings]
            
            # Convert timestamps to numeric values (seconds since start)
            start_timestamp = timestamps[0]
            numeric_times = [(t - start_timestamp).total_seconds() for t in timestamps]
            
            # Calculate linear regression
            n = len(values)
            sum_x = sum(numeric_times)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(numeric_times, values))
            sum_x2 = sum(x * x for x in numeric_times)
            
            # Calculate slope and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate R-squared
            y_mean = sum_y / n
            ss_tot = sum((y - y_mean) ** 2 for y in values)
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(numeric_times, values))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Determine trend direction
            if abs(slope) < 0.001:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
            
            # Calculate confidence based on R-squared and data points
            confidence = min(r_squared * (len(values) / 10), 1.0)  # More data points = higher confidence
            
            return {
                "trend": direction,
                "slope": float(slope),
                "direction": direction,
                "confidence": float(confidence),
                "r_squared": float(r_squared),
                "data_points": len(values),
                "intercept": float(intercept),
                "change_rate": float(slope)  # Change rate is the slope
            }
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return {
                "trend": "error",
                "slope": 0.0,
                "direction": "unknown",
                "confidence": 0.0,
                "r_squared": 0.0,
                "change_rate": 0.0
            }
    
    def get_reading_statistics_by_organization(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get reading statistics for a specific organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary containing reading statistics
        """
        try:
            from ..models.device import Device
            
            # Get all readings for the organization
            readings = self.db.query(Reading).join(Device, Reading.entity_id == Device.id).filter(Device.organization_id == organization_id).all()
            
            if not readings:
                return {
                    "total_readings": 0,
                    "devices": 0,
                    "sensor_types": 0,
                    "average_per_device": 0.0,
                    "readings_24h": 0
                }
            
            # Calculate statistics
            total_readings = len(readings)
            unique_devices = len(set(r.entity_id for r in readings))
            unique_sensor_types = len(set(r.get_sensor_type() for r in readings))
            average_per_device = total_readings / unique_devices if unique_devices > 0 else 0
            
            # Get readings in last 24 hours
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_readings = len([
                r for r in readings 
                if r.timestamp.replace(tzinfo=timezone.utc) >= twenty_four_hours_ago
            ])
            
            return {
                "total_readings": total_readings,
                "devices": unique_devices,
                "sensor_types": unique_sensor_types,
                "average_per_device": float(average_per_device),
                "readings_24h": recent_readings
            }
            
        except Exception as e:
            logger.error(f"Error getting reading statistics by organization: {e}")
            return {
                "total_readings": 0,
                "devices": 0,
                "sensor_types": 0,
                "average_per_device": 0.0,
                "readings_24h": 0
            }
    
    def export_readings_csv(
        self, 
        device_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """
        Export readings to CSV format.
        
        Args:
            device_id: Device ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            CSV data as string
        """
        try:
            import csv
            import io
            
            # Get readings
            readings = self.get_readings_by_device(device_id, start_time=start_time, end_time=end_time)
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['timestamp', 'sensor_type', 'value', 'unit', 'quality', 'location', 'battery_level'])
            
            # Write data
            for reading in readings:
                writer.writerow([
                    reading.timestamp.isoformat(),
                    reading.get_sensor_type(),
                    reading.get_value(),
                    reading.get_unit(),
                    reading.data.get('quality', ''),
                    reading.data.get('location', ''),
                    reading.data.get('batteryLevel', '')
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting readings to CSV: {e}")
            return ""
    
    def export_readings_json(
        self, 
        device_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export readings to JSON format.
        
        Args:
            device_id: Device ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of reading dictionaries
        """
        try:
            # Get readings
            readings = self.get_readings_by_device(device_id, start_time=start_time, end_time=end_time)
            
            # Convert to JSON format
            json_data = []
            for reading in readings:
                json_data.append({
                    'timestamp': reading.timestamp.isoformat(),
                    'sensor_type': reading.get_sensor_type(),
                    'value': reading.get_value(),
                    'unit': reading.get_unit(),
                    'quality': reading.data.get('quality', ''),
                    'location': reading.data.get('location', ''),
                    'battery_level': reading.data.get('batteryLevel', ''),
                    'metadata': reading.data.get('metadata', {})
                })
            
            return json_data
            
        except Exception as e:
            logger.error(f"Error exporting readings to JSON: {e}")
            return []
    
    def update_reading(self, reading_id: UUID, update_data: ReadingUpdate) -> Reading:
        """
        Update a reading with new data.
        
        Args:
            reading_id: Reading ID
            update_data: Updated reading data
            
        Returns:
            Updated reading
            
        Raises:
            ReadingNotFoundException: If reading not found
            ServiceException: If update fails
        """
        try:
            # Get existing reading
            reading = self.db.query(Reading).filter(Reading.id == reading_id).first()
            if not reading:
                raise ReadingNotFoundException(f"Reading with ID {reading_id} not found")
            
            # Update data fields
            if update_data.value is not None:
                reading.data['value'] = update_data.value
            if update_data.unit is not None:
                reading.data['unit'] = update_data.unit
            if update_data.sensor_type is not None:
                reading.data['sensorType'] = update_data.sensor_type
            if update_data.quality is not None:
                reading.data['quality'] = update_data.quality
            if update_data.location is not None:
                reading.data['location'] = update_data.location
            if update_data.battery_level is not None:
                reading.data['batteryLevel'] = update_data.battery_level
            if update_data.metadata is not None:
                reading.data['metadata'] = update_data.metadata
            
            # Save changes
            self.db.commit()
            self.db.refresh(reading)
            
            logger.info(f"Reading updated: {reading.get_sensor_type()} = {reading.get_value()} {reading.get_unit()}")
            return reading
            
        except ReadingNotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating reading: {e}")
            raise ServiceException("Failed to update reading")
    
    def update(self, id: UUID, data: ReadingUpdate) -> Reading:
        """
        Update a reading using the base service interface.
        
        Args:
            id: Reading ID
            data: Updated reading data
            
        Returns:
            Updated reading
        """
        return self.update_reading(id, data) 