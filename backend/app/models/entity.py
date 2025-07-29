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
    
    # Entity-specific fields (inherits id, created_at, updated_at, is_active from BaseModel)
    entity_type = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    properties = Column(JSONType, nullable=False, default={})
    status = Column(String(50), default="active")
    organization_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Note: In pure entity approach, User and Entity are the same table
    # No separate relationships needed since User inherits from Entity
    
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
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        # Use BaseModel's to_dict and add entity-specific fields
        result = super().to_dict()
        result.update({
            'entity_type': self.entity_type,
            'name': self.name,
            'description': self.description,
            'properties': self.properties,
            'status': self.status,
            'organization_id': str(self.organization_id) if self.organization_id else None
        })
        return result
    
    def __repr__(self):
        """String representation of the model."""
        return f"<Entity(id={self.id}, type={self.entity_type}, name={self.name})>" 