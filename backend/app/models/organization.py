"""
Organization model for LMS Core API.

This module contains the Organization model and related functionality
for multi-tenant organization management.
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
from typing import Dict, Any, Optional

from .base import BaseModel
from .entity import Entity
from ..database import JSONType


class Organization(Entity):
    """
    Organization model for multi-tenant support.
    
    Maps to the existing entities table with entity_type = 'organization'
    and stores organization configuration in the properties JSON column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'organization',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for organizations
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'organization'
        super().__init__(*args, **kwargs)
    
    # Relationships - these are handled through the Entity base class
    # Users, devices, etc. are accessed through the entities relationship
    
    # Add reverse relationship to Project
    projects = relationship(
        "Project",
        primaryjoin="Organization.id==Project.organization_id",
        foreign_keys="Project.organization_id",
        back_populates=None  # No back_populates since Project.organization does not use it
    )
    
    @classmethod
    def get_by_name(cls, db, name: str):
        """
        Get organization by name.
        
        Args:
            db: Database session
            name: Organization name
            
        Returns:
            Organization instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "organization",
            cls.name == name
        ).first()
    
    @classmethod
    def get_all_organizations(cls, db, skip: int = 0, limit: int = 100):
        """
        Get all organizations.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of organization instances
        """
        return db.query(cls).filter(
            cls.entity_type == "organization"
        ).offset(skip).limit(limit).all()
    
    def get_contact_email(self) -> str:
        """
        Get contact email from properties.
        
        Returns:
            Contact email string
        """
        return self.get_property('contactEmail', '')
    
    def get_contact_phone(self) -> str:
        """
        Get contact phone from properties.
        
        Returns:
            Contact phone string
        """
        return self.get_property('contactPhone', '')
    
    def get_address(self) -> str:
        """
        Get address from properties.
        
        Returns:
            Address string
        """
        return self.get_property('address', '')
    
    def get_website(self) -> str:
        """
        Get website from properties.
        
        Returns:
            Website string
        """
        return self.get_property('website', '')
    
    def get_member_count(self) -> int:
        """
        Get member count from properties.
        
        Returns:
            Member count as integer
        """
        return self.get_property('memberCount', 0)
    
    def get_subscription_plan(self) -> str:
        """
        Get subscription plan from properties.
        
        Returns:
            Subscription plan string
        """
        return self.get_property('subscriptionPlan', 'free')
    
    def __repr__(self):
        """String representation of the organization."""
        return f"<Organization(id={self.id}, name={self.name})>" 