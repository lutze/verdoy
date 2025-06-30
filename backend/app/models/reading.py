"""
Reading model for LMS Core API.

This module contains the Reading model and related functionality
for storing and retrieving sensor data from ESP32 devices.
"""

from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel
from .event import Event


class Reading(Event):
    """
    Reading model for sensor data storage.
    
    Maps to the existing events table with event_type = 'sensor.reading'
    and stores sensor data in the data JSONB column.
    """
    
    def __init__(self, *args, **kwargs):
        # Set default event_type for sensor readings
        if 'event_type' not in kwargs:
            kwargs['event_type'] = 'sensor.reading'
        super().__init__(*args, **kwargs)
    
    @classmethod
    def get_device_readings(
        cls, 
        db, 
        device_id, 
        sensor_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ):
        """
        Get readings for a specific device with optional filtering.
        
        Args:
            db: Database session
            device_id: Device entity ID
            sensor_type: Optional sensor type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of readings to return
            
        Returns:
            List of reading instances
        """
        query = db.query(cls).filter(
            cls.event_type == "sensor.reading",
            cls.entity_id == device_id
        )
        
        if sensor_type:
            query = query.filter(cls.data['sensorType'].astext == sensor_type)
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_latest_readings(cls, db, device_id, sensor_types: list = None):
        """
        Get latest readings for a device.
        
        Args:
            db: Database session
            device_id: Device entity ID
            sensor_types: Optional list of sensor types
            
        Returns:
            List of latest reading instances
        """
        query = db.query(cls).filter(
            cls.event_type == "sensor.reading",
            cls.entity_id == device_id
        )
        
        if sensor_types:
            query = query.filter(cls.data['sensorType'].astext.in_(sensor_types))
        
        # Get the latest reading for each sensor type
        latest_readings = []
        for reading in query.order_by(cls.data['sensorType'].astext, cls.timestamp.desc()).all():
            sensor_type = reading.get_data_value('sensorType')
            # Check if we already have a reading for this sensor type
            if not any(r.get_data_value('sensorType') == sensor_type for r in latest_readings):
                latest_readings.append(reading)
        
        return latest_readings
    
    @classmethod
    def get_readings_statistics(
        cls, 
        db, 
        device_id, 
        sensor_type: str,
        start_time: datetime = None,
        end_time: datetime = None
    ):
        """
        Get statistical summary of readings.
        
        Args:
            db: Database session
            device_id: Device entity ID
            sensor_type: Sensor type
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func
        
        query = db.query(cls).filter(
            cls.event_type == "sensor.reading",
            cls.entity_id == device_id,
            cls.data['sensorType'].astext == sensor_type
        )
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        
        stats = query.with_entities(
            func.count(cls.id).label('count'),
            func.avg(cls.data['value'].astext.cast(Float)).label('avg'),
            func.min(cls.data['value'].astext.cast(Float)).label('min'),
            func.max(cls.data['value'].astext.cast(Float)).label('max'),
            func.stddev(cls.data['value'].astext.cast(Float)).label('stddev')
        ).first()
        
        return {
            'count': stats.count or 0,
            'average': float(stats.avg) if stats.avg else 0.0,
            'minimum': float(stats.min) if stats.min else 0.0,
            'maximum': float(stats.max) if stats.max else 0.0,
            'std_deviation': float(stats.stddev) if stats.stddev else 0.0
        }
    
    @classmethod
    def create_batch_readings(cls, db, device_id, readings_data: list):
        """
        Create multiple readings in a batch.
        
        Args:
            db: Database session
            device_id: Device entity ID
            readings_data: List of reading dictionaries
            
        Returns:
            List of created reading instances
        """
        readings = []
        for data in readings_data:
            reading = cls(
                entity_id=device_id,
                entity_type="device.esp32",
                event_type="sensor.reading",
                timestamp=data.get('timestamp', datetime.utcnow()),
                data={
                    'sensorType': data['sensor_type'],
                    'value': data['value'],
                    'unit': data.get('unit'),
                    'quality': data.get('quality', 'good'),
                    'location': data.get('location'),
                    'batteryLevel': data.get('battery_level'),
                    'metadata': data.get('metadata', {})
                },
                event_metadata=data.get('event_metadata', {}),
                source_node=data.get('source_node')
            )
            readings.append(reading)
        
        db.add_all(readings)
        db.commit()
        
        return readings
    
    def get_sensor_type(self) -> str:
        """
        Get sensor type from data.
        
        Returns:
            Sensor type string
        """
        return self.get_data_value('sensorType', '')
    
    def get_value(self) -> float:
        """
        Get sensor value from data.
        
        Returns:
            Sensor value as float
        """
        value = self.get_data_value('value')
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def get_unit(self) -> str:
        """
        Get sensor unit from data.
        
        Returns:
            Sensor unit string
        """
        return self.get_data_value('unit', '')
    
    def get_quality(self) -> str:
        """
        Get reading quality from data.
        
        Returns:
            Reading quality string
        """
        return self.get_data_value('quality', 'good')
    
    def get_location(self) -> str:
        """
        Get sensor location from data.
        
        Returns:
            Sensor location string
        """
        return self.get_data_value('location', '')
    
    def get_battery_level(self) -> str:
        """
        Get battery level from data.
        
        Returns:
            Battery level string
        """
        return self.get_data_value('batteryLevel', '')
    
    def is_valid(self) -> bool:
        """
        Check if reading is valid based on quality and value.
        
        Returns:
            True if reading is valid, False otherwise
        """
        return self.get_quality() != "bad" and self.get_value() is not None
    
    def __repr__(self):
        """String representation of the reading."""
        return f"<Reading(id={self.id}, sensor_type={self.get_sensor_type()}, value={self.get_value()})>" 