"""
User model for LMS Core API.

This module contains the User model and related functionality
for user authentication and management.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid

from .base import BaseModel


class User(BaseModel):
    """
    User model for authentication and user management.
    
    Maps to the existing users table for authentication capabilities
    and relationship to entities.
    """
    
    __tablename__ = "users"
    
    entity_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, unique=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    entity = relationship("Entity", back_populates="user")
    devices = relationship("Device", back_populates="user")
    
    @classmethod
    def get_by_email(cls, db, email: str):
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_active_users(cls, db, skip: int = 0, limit: int = 100):
        """
        Get all active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active user instances
        """
        return db.query(cls).filter(cls.is_active == True).offset(skip).limit(limit).all()
    
    @classmethod
    def get_by_entity_id(cls, db, entity_id):
        """
        Get user by entity ID.
        
        Args:
            db: Database session
            entity_id: Entity ID
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(cls.entity_id == entity_id).first()
    
    def is_admin(self) -> bool:
        """
        Check if user is an admin.
        
        Returns:
            True if user is admin, False otherwise
        """
        return self.is_superuser
    
    def __repr__(self):
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email})>" 