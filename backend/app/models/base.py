"""
Base model for all database models in the VerdoyLab API.

This module provides the base model class with common fields and
functionality that all models inherit from.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from sqlalchemy import String, Text
import uuid
from ..database import JSONType

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and functionality.
    
    All models should inherit from this class to get:
    - UUID primary key
    - Created/updated timestamps
    - Soft delete functionality
    - Common utility methods
    """
    
    __abstract__ = True
    
    # Use UUID as primary key with auto-generation
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        return cls.__name__.lower() + 's'
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """Update model instance with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self):
        """Soft delete the model instance."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted model instance."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_by_id(cls, db, id):
        """
        Get model instance by ID.
        
        Args:
            db: Database session
            id: Model ID
            
        Returns:
            Model instance or None
        """
        return db.query(cls).filter(cls.id == id).first()
    
    @classmethod
    def get_all(cls, db, skip: int = 0, limit: int = 100):
        """
        Get all model instances with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        return db.query(cls).offset(skip).limit(limit).all()
    
    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>" 