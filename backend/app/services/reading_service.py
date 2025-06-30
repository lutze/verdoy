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
from datetime import datetime, timedelta
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
    DataProcessingException
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
                device_id=device_id,
                sensor_type=reading_data.sensor_type,
                value=reading_data.value,
                unit=reading_data.unit,
                timestamp=reading_data.timestamp or datetime.utcnow(),
                metadata=reading_data.metadata or {},
                organization_id=device.organization_id
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
            
            # Create reading entity
            reading = Reading(
                device_id=reading_data.device_id,
                sensor_type=reading_data.sensor_type,
                value=reading_data.value,
                unit=reading_data.unit,
                timestamp=reading_data.timestamp or datetime.utcnow(),
                metadata=reading_data.metadata or {}
            )
            
            # Save to database
            self.db.add(reading)
            self.db.commit()
            self.db.refresh(reading)
            
            logger.info(f"Reading created: {reading.sensor_type} = {reading.value} {reading.unit}")
            return reading
            
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
            query = self.db.query(Reading).filter(Reading.device_id == device_id)
            
            if sensor_type:
                query = query.filter(Reading.sensor_type == sensor_type)
            
            if start_time:
                query = query.filter(Reading.timestamp >= start_time)
            
            if end_time:
                query = query.filter(Reading.timestamp <= end_time)
            
            readings = query.order_by(desc(Reading.timestamp)).limit(limit).all()
            
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
            query = self.db.query(Reading).filter(Reading.organization_id == organization_id)
            
            if sensor_type:
                query = query.filter(Reading.sensor_type == sensor_type)
            
            if start_time:
                query = query.filter(Reading.timestamp >= start_time)
            
            if end_time:
                query = query.filter(Reading.timestamp <= end_time)
            
            readings = query.order_by(desc(Reading.timestamp)).limit(limit).all()
            
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
            query = self.db.query(Reading).filter(Reading.device_id == device_id)
            
            if sensor_types:
                query = query.filter(Reading.sensor_type.in_(sensor_types))
            
            # Get the latest reading for each sensor type
            latest_readings = {}
            
            # Get distinct sensor types
            sensor_types_result = query.with_entities(Reading.sensor_type).distinct().all()
            
            for (sensor_type,) in sensor_types_result:
                latest = query.filter(Reading.sensor_type == sensor_type)\
                    .order_by(desc(Reading.timestamp))\
                    .first()
                if latest:
                    latest_readings[sensor_type] = latest
            
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
            query = self.db.query(Reading).filter(
                Reading.device_id == device_id,
                Reading.sensor_type == sensor_type
            )
            
            if start_time:
                query = query.filter(Reading.timestamp >= start_time)
            
            if end_time:
                query = query.filter(Reading.timestamp <= end_time)
            
            # Calculate statistics
            stats = query.with_entities(
                func.count(Reading.id).label('count'),
                func.avg(Reading.value).label('average'),
                func.min(Reading.value).label('minimum'),
                func.max(Reading.value).label('maximum'),
                func.stddev(Reading.value).label('stddev')
            ).first()
            
            if not stats or stats.count == 0:
                return {
                    "count": 0,
                    "average": None,
                    "minimum": None,
                    "maximum": None,
                    "stddev": None,
                    "range": None
                }
            
            return {
                "count": stats.count,
                "average": float(stats.average) if stats.average else None,
                "minimum": float(stats.minimum) if stats.minimum else None,
                "maximum": float(stats.maximum) if stats.maximum else None,
                "stddev": float(stats.stddev) if stats.stddev else None,
                "range": float(stats.maximum - stats.minimum) if stats.maximum and stats.minimum else None
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
            # Generate hourly intervals
            intervals = []
            current_time = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_time <= end_time:
                next_hour = current_time + timedelta(hours=1)
                intervals.append((current_time, next_hour))
                current_time = next_hour
            
            hourly_averages = []
            
            for interval_start, interval_end in intervals:
                # Get average for this hour
                avg_result = self.db.query(func.avg(Reading.value)).filter(
                    Reading.device_id == device_id,
                    Reading.sensor_type == sensor_type,
                    Reading.timestamp >= interval_start,
                    Reading.timestamp < interval_end
                ).scalar()
                
                hourly_averages.append({
                    "timestamp": interval_start.isoformat(),
                    "average": float(avg_result) if avg_result else None,
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
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get daily averages for a sensor type over a date range.
        
        Args:
            device_id: Device ID
            sensor_type: Sensor type
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily average data points
        """
        try:
            # Generate daily intervals
            intervals = []
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            while current_date <= end_date:
                next_day = current_date + timedelta(days=1)
                intervals.append((current_date, next_day))
                current_date = next_day
            
            daily_averages = []
            
            for interval_start, interval_end in intervals:
                # Get average for this day
                avg_result = self.db.query(func.avg(Reading.value)).filter(
                    Reading.device_id == device_id,
                    Reading.sensor_type == sensor_type,
                    Reading.timestamp >= interval_start,
                    Reading.timestamp < interval_end
                ).scalar()
                
                daily_averages.append({
                    "date": interval_start.date().isoformat(),
                    "average": float(avg_result) if avg_result else None,
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
        
        if reading_data.timestamp and reading_data.timestamp > datetime.utcnow() + timedelta(minutes=5):
            raise ValidationException("Reading timestamp cannot be in the future")
        
        return True
    
    def get_reading_statistics(self, organization_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get reading statistics for analytics.
        
        Args:
            organization_id: Optional organization filter
            
        Returns:
            Dictionary containing reading statistics
        """
        try:
            query = self.db.query(Reading)
            
            if organization_id:
                query = query.filter(Reading.organization_id == organization_id)
            
            total_readings = query.count()
            
            # Get readings in last 24 hours
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_readings = query.filter(Reading.timestamp >= twenty_four_hours_ago).count()
            
            # Get unique sensor types
            sensor_types = query.with_entities(Reading.sensor_type).distinct().count()
            
            # Get unique devices
            unique_devices = query.with_entities(Reading.device_id).distinct().count()
            
            return {
                "total_readings": total_readings,
                "readings_24h": recent_readings,
                "unique_sensor_types": sensor_types,
                "unique_devices": unique_devices,
                "readings_per_hour": recent_readings / 24 if recent_readings > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting reading statistics: {e}")
            return {
                "total_readings": 0,
                "readings_24h": 0,
                "unique_sensor_types": 0,
                "unique_devices": 0,
                "readings_per_hour": 0
            } 