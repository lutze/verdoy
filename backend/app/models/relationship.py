"""
Relationship model for VerdoyLab API.

This module defines the Relationship model which represents connections
between entities in the system.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB

from .base import Base


class Relationship(Base):
    """
    Relationship model representing connections between entities.
    
    This model stores graph relationships between entities with properties,
    strength values, and temporal validity.
    """
    __tablename__ = "relationships"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=lambda: str(UUID()))
    from_entity = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    to_entity = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    properties = Column(JSONB, default={})
    strength = Column(Numeric(3, 2), default=1.0)  # Relationship strength (0.0-1.0)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    from_entity_obj = relationship("Entity", foreign_keys=[from_entity])
    to_entity_obj = relationship("Entity", foreign_keys=[to_entity])
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, from={self.from_entity}, to={self.to_entity}, type='{self.relationship_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            "id": str(self.id),
            "from_entity": str(self.from_entity),
            "to_entity": str(self.to_entity),
            "relationship_type": self.relationship_type,
            "properties": self.properties,
            "strength": float(self.strength) if self.strength else 1.0,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "created_by": self.created_by
        }
    
    def is_valid(self, at_time: Optional[datetime] = None) -> bool:
        """Check if relationship is valid at given time."""
        if at_time is None:
            at_time = datetime.utcnow()
        
        if self.valid_from and at_time < self.valid_from:
            return False
        
        if self.valid_to and at_time > self.valid_to:
            return False
        
        return True
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value from the relationship."""
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a property value in the relationship."""
        if not self.properties:
            self.properties = {}
        self.properties[key] = value

