"""
User model for LMS Core API.

This module contains the User model and related functionality
for user authentication and management.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from passlib.context import CryptContext
import uuid

from .base import BaseModel

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    # Bi-directional one-to-one relationship to Entity (user profile)
    entity = relationship("Entity", back_populates="user", uselist=False)
    devices = relationship("Device", back_populates="user")
    
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