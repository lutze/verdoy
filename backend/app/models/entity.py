"""
Entity model for LMS Core API.

This module defines the Entity model which represents generic entities
in the system with flexible properties stored as JSON.
"""

from sqlalchemy import Column, DateTime, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import uuid

from .base import BaseModel
from ..database import JSONType


class Entity(BaseModel):
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
    entity_type = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    properties = Column(JSONType, nullable=False, default={})
    status = Column(String(50), default="active")
    organization_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Bi-directional one-to-one relationship to User (for user entities)
    user = relationship("User", back_populates="entity", uselist=False, foreign_keys="User.entity_id")  # Only applies if this entity is a user
    
    def get_property(self, key, default=None):
        """
        Get property value from JSON properties.
        
        Args:
            key: Property key
            default: Default value if key doesn't exist
            
        Returns:
            Property value or default
        """
        return self.properties.get(key, default) if self.properties else default
    
    def set_property(self, key, value):
        """
        Set property value in JSON properties.
        
        Args:
            key: Property key
            value: Property value
        """
        if self.properties is None:
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