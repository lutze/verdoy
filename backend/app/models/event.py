"""
Event model for VerdoyLab API.

This module defines the Event model which represents system events
and stores event data in the data JSON column.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .base import Base
from ..database import JSONType, UUIDType


class Event(Base):
    """
    Event model for tracking system events.
    
    Events are used to track important system activities like:
    - User actions (login, logout, data changes)
    - Device events (connect, disconnect, errors)
    - System events (backups, maintenance, alerts)
    - Data events (imports, exports, processing)
    """
    
    __tablename__ = "events"
    
    # Match the exact database schema from 001_initial_schema.sql
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUIDType, nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    data = Column(JSONType, nullable=False)
    event_metadata = Column(JSONType, default={})
    source_node = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Note: user information can be stored in the data JSONB field if needed
    
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
            user_id: ID of the user who triggered the event (stored in data field)
            
        Returns:
            Created Event instance
        """
        event_data = data or {}
        if user_id:
            event_data['user_id'] = str(user_id)
            
        event = cls(
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            data=event_data,
            event_metadata=event_metadata or {}
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
            cls.entity_type == entity_type
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
            cls.event_type == event_type
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_events_by_user(cls, db, user_id, limit=100):
        """
        Get events by user ID (searches in data JSONB field).
        
        Args:
            db: Database session
            user_id: User ID to search for
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)
        elif not isinstance(user_id, str):
            try:
                user_id = str(user_id)
            except Exception:
                return []
                
        return db.query(cls).filter(
            cls.data['user_id'].astext == user_id
        ).order_by(cls.timestamp.desc()).limit(limit).all() 