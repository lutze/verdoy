"""
User model for LMS Core API.

This module contains the User model and related functionality
for user authentication and management.
"""

from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from typing import Optional
import uuid

from .entity import Entity

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Entity):
    """
    User model for authentication and user management.
    
    Maps to the entities table with entity_type = 'user'
    and stores user-specific fields in the properties JSONB column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for users
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'user'
        super().__init__(*args, **kwargs)
    
    # User-specific property accessors
    @property
    def email(self) -> str:
        """Get user email from properties."""
        return self.get_property('email', '')
    
    @email.setter
    def email(self, value: str):
        """Set user email in properties."""
        self.set_property('email', value)
    
    @property
    def hashed_password(self) -> str:
        """Get hashed password from properties."""
        return self.get_property('hashed_password', '')
    
    @hashed_password.setter
    def hashed_password(self, value: str):
        """Set hashed password in properties."""
        self.set_property('hashed_password', value)
    
    @property
    def is_superuser(self) -> bool:
        """Get superuser status from properties."""
        return self.get_property('is_superuser', False)
    
    @is_superuser.setter
    def is_superuser(self, value: bool):
        """Set superuser status in properties."""
        self.set_property('is_superuser', value)
    
    @property
    def entity_id(self) -> Optional[uuid.UUID]:
        """Get entity ID from properties (for backward compatibility)."""
        entity_id_str = self.get_property('entity_id')
        if entity_id_str:
            return uuid.UUID(entity_id_str)
        return self.id  # Use own ID as entity_id
    
    @entity_id.setter
    def entity_id(self, value: Optional[uuid.UUID]):
        """Set entity ID in properties (for backward compatibility)."""
        if value:
            self.set_property('entity_id', str(value))
        else:
            self.set_property('entity_id', str(self.id))
    
    # Password management methods
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def check_password(self, plain_password: str) -> bool:
        """
        Verify a password against this user's hashed password.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return self.verify_password(plain_password, self.hashed_password)
    
    # Query methods
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
        # Get all users and filter in Python to avoid JSONB operator issues
        users = db.query(cls).filter(cls.entity_type == "user").all()
        
        for user in users:
            if user.email == email:
                return user
        
        return None
    
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
        return db.query(cls).filter(
            cls.entity_type == "user",
            cls.is_active == True
        ).offset(skip).limit(limit).all()
    
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
        return db.query(cls).filter(
            cls.entity_type == "user",
            cls.id == entity_id
        ).first()
    
    def is_admin(self) -> bool:
        """
        Check if user is an admin.
        
        Returns:
            True if user is admin, False otherwise
        """
        return self.is_superuser or self.get_property('is_admin', False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>" 