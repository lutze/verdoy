"""
Organization Member model for VerdoyLab API.

This module contains the OrganizationMember model for managing
organization membership and roles.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from uuid import UUID

from .base import BaseModel


class OrganizationMember(BaseModel):
    """
    Organization Member model for managing organization membership.
    
    Represents a user's membership in an organization with a specific role.
    """
    
    __tablename__ = "organization_members"
    
    # Foreign keys
    organization_id = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    invited_by = Column(PostgresUUID, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    
    # Member properties
    role = Column(String(50), nullable=False, default="member")
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Entity", foreign_keys=[organization_id], backref="members_list")
    user = relationship("Entity", foreign_keys=[user_id], backref="memberships")
    inviter = relationship("Entity", foreign_keys=[invited_by], backref="members_invited")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.joined_at:
            self.joined_at = datetime.utcnow()
        if not self.invited_at:
            self.invited_at = datetime.utcnow()
    
    @classmethod
    def get_by_organization_and_user(cls, db, organization_id: UUID, user_id: UUID):
        """
        Get organization membership by organization and user IDs.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            OrganizationMember instance or None
        """
        return db.query(cls).filter(
            cls.organization_id == organization_id,
            cls.user_id == user_id
        ).first()
    
    @classmethod
    def get_organization_members(cls, db, organization_id: UUID, active_only: bool = True):
        """
        Get all members of an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            active_only: Whether to return only active members
            
        Returns:
            List of OrganizationMember instances
        """
        query = db.query(cls).filter(cls.organization_id == organization_id)
        if active_only:
            query = query.filter(cls.is_active == True)
        return query.all()
    
    @classmethod
    def get_user_organizations(cls, db, user_id: UUID, active_only: bool = True):
        """
        Get all organizations a user belongs to.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Whether to return only active memberships
            
        Returns:
            List of OrganizationMember instances
        """
        query = db.query(cls).filter(cls.user_id == user_id)
        if active_only:
            query = query.filter(cls.is_active == True)
        return query.all()
    
    @classmethod
    def get_organization_admins(cls, db, organization_id: UUID):
        """
        Get all admin members of an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of admin OrganizationMember instances
        """
        return db.query(cls).filter(
            cls.organization_id == organization_id,
            cls.role == "admin",
            cls.is_active == True
        ).all()
    
    def is_admin(self) -> bool:
        """
        Check if member has admin role.
        
        Returns:
            True if member is admin, False otherwise
        """
        return self.role == "admin"
    
    def is_viewer(self) -> bool:
        """
        Check if member has viewer role.
        
        Returns:
            True if member is viewer, False otherwise
        """
        return self.role == "viewer"
    
    def can_invite_members(self) -> bool:
        """
        Check if member can invite other members.
        
        Returns:
            True if member can invite, False otherwise
        """
        return self.role in ["admin"]
    
    def can_manage_roles(self) -> bool:
        """
        Check if member can manage other members' roles.
        
        Returns:
            True if member can manage roles, False otherwise
        """
        return self.role in ["admin"]
    
    def can_approve_removals(self) -> bool:
        """
        Check if member can approve removal requests.
        
        Returns:
            True if member can approve removals, False otherwise
        """
        return self.role in ["admin"]
    
    def __repr__(self):
        """String representation of the organization member."""
        return f"<OrganizationMember(org_id={self.organization_id}, user_id={self.user_id}, role={self.role})>" 