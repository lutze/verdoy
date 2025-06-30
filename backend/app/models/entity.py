"""
Entity model for LMS Core API.

This module defines the canonical Entity model that maps to the entities table.
All entity types (users, devices, organizations, etc.) are stored in this single table
and differentiated by the entity_type field.
"""

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
import uuid

from .base import Base


class Entity(Base):
    """
    Canonical Entity model for the entities table.
    
    This model stores all types of entities in the system:
    - Users (entity_type = 'user')
    - Devices (entity_type = 'device.esp32')
    - Organizations (entity_type = 'organization')
    - Alert rules (entity_type = 'alert.rule')
    - Billing accounts (entity_type = 'billing.account')
    - Subscriptions (entity_type = 'billing.subscription')
    """
    
    __tablename__ = "entities"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    properties = Column(JSONB, nullable=False, default={})
    status = Column(String(50), default="active")
    organization_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_property(self, key: str, default=None):
        """
        Get property value from JSONB properties.
        
        Args:
            key: Property key
            default: Default value if key not found
            
        Returns:
            Property value or default
        """
        return self.properties.get(key, default) if self.properties else default
    
    def set_property(self, key: str, value):
        """
        Set property value in JSONB properties.
        
        Args:
            key: Property key
            value: Property value
        """
        if not self.properties:
            self.properties = {}
        self.properties[key] = value
        self.last_updated = datetime.utcnow()
    
    def update_properties(self, **kwargs):
        """
        Update multiple properties at once.
        
        Args:
            **kwargs: Properties to update
        """
        if not self.properties:
            self.properties = {}
        self.properties.update(kwargs)
        self.last_updated = datetime.utcnow()
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'name': self.name,
            'description': self.description,
            'properties': self.properties,
            'status': self.status,
            'organization_id': str(self.organization_id) if self.organization_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        return result
    
    def __repr__(self):
        """String representation of the model."""
        return f"<Entity(id={self.id}, type={self.entity_type}, name={self.name})>" 