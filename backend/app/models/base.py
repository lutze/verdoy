"""
Base model class for LMS Core API.

This module provides a base model class with common functionality
used by all database models in the application.
"""

from sqlalchemy import Column, DateTime, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common functionality.
    
    Provides:
    - UUID primary key
    - Created and updated timestamps
    - Common utility methods
    """
    
    __abstract__ = True
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs):
        """
        Update model instance with provided values.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
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