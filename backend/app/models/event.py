"""
Event model for LMS Core API.

This module defines the canonical Event model that maps to the events table.
All event types (alerts, readings, commands, etc.) are stored in this single table
and differentiated by the event_type field.
"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
import uuid

from .base import Base


class Event(Base):
    """
    Canonical Event model for the events table.
    
    This model stores all types of events in the system:
    - Sensor readings (event_type = 'sensor.reading')
    - Alert triggers (event_type = 'alert.triggered')
    - Device commands (event_type = 'device.command')
    - System events (event_type = 'system.*')
    - Audit events (event_type = 'audit.*')
    """
    
    __tablename__ = "events"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(100), nullable=False)
    entity_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    entity_type = Column(String(100), nullable=False)
    data = Column(JSONB, nullable=False)
    event_metadata = Column(JSONB, default={})
    source_node = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_data_value(self, key: str, default=None):
        """
        Get data value from JSONB data.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        return self.data.get(key, default) if self.data else default
    
    def set_data_value(self, key: str, value):
        """
        Set data value in JSONB data.
        
        Args:
            key: Data key
            value: Data value
        """
        if not self.data:
            self.data = {}
        self.data[key] = value
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {
            'id': str(self.id),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'entity_id': str(self.entity_id),
            'entity_type': self.entity_type,
            'data': self.data,
            'event_metadata': self.event_metadata,
            'source_node': self.source_node,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        return result
    
    def __repr__(self):
        """String representation of the model."""
        return f"<Event(id={self.id}, type={self.event_type}, entity={self.entity_id})>" 