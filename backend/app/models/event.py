"""
Event model for LMS Core API.

This module defines the Event model which represents system events
and stores event data in the data JSON column.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import BaseModel
from ..database import JSONType


class Event(BaseModel):
    """
    Event model for tracking system events.
    
    Events are used to track important system activities like:
    - User actions (login, logout, data changes)
    - Device events (connect, disconnect, errors)
    - System events (backups, maintenance, alerts)
    - Data events (imports, exports, processing)
    """
    
    __tablename__ = "events"
    
    # Event details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    
    # Event data and metadata
    data = Column(JSONType, nullable=False)
    event_metadata = Column(JSONType, default={})
    
    # Relationships
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User")
    
    def get_data_value(self, key, default=None):
        """
        Get data value from JSON data.
        
        Args:
            key: Key to retrieve from data
            default: Default value if key doesn't exist
            
        Returns:
            Value from data or default
        """
        return self.data.get(key, default) if self.data else default
    
    def set_data_value(self, key, value):
        """
        Set data value in JSON data.
        
        Args:
            key: Key to set in data
            value: Value to set
        """
        if self.data is None:
            self.data = {}
        self.data[key] = value
    
    def add_metadata(self, key, value):
        """
        Add metadata to the event.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.event_metadata is None:
            self.event_metadata = {}
        self.event_metadata[key] = value
    
    def get_metadata(self, key, default=None):
        """
        Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key doesn't exist
            
        Returns:
            Metadata value or default
        """
        return self.event_metadata.get(key, default) if self.event_metadata else default
    
    @classmethod
    def create_event(cls, db, event_type, entity_id, entity_type, data=None, 
                    event_metadata=None, user_id=None):
        """
        Create a new event.
        
        Args:
            db: Database session
            event_type: Type of event
            entity_id: ID of the entity involved
            entity_type: Type of the entity
            data: Event data dictionary
            event_metadata: Event metadata dictionary
            user_id: ID of the user who triggered the event
            
        Returns:
            Created Event instance
        """
        event = cls(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            data=data or {},
            event_metadata=event_metadata or {},
            user_id=user_id
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @classmethod
    def get_events_by_entity(cls, db, entity_id, entity_type, limit=100):
        if isinstance(entity_id, str):
            try:
                entity_id = uuid.UUID(entity_id)
            except Exception:
                pass
        return db.query(cls).filter(
            cls.entity_id == entity_id,
            cls.entity_type == entity_type,
            cls.is_active == True
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_events_by_type(cls, db, event_type, limit=100):
        """
        Get events by type.
        
        Args:
            db: Database session
            event_type: Event type to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        return db.query(cls).filter(
            cls.event_type == event_type,
            cls.is_active == True
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_events_by_user(cls, db, user_id, limit=100):
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except Exception:
                pass
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.is_active == True
        ).order_by(cls.timestamp.desc()).limit(limit).all() 