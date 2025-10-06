"""
Organization Invitation model for VerdoyLab API.

This module contains the OrganizationInvitation model for managing
organization invitations and acceptance workflows.
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from .base import BaseModel


class OrganizationInvitation(BaseModel):
    """
    Organization Invitation model for managing invitations.
    
    Represents an invitation sent to a user to join an organization.
    """
    
    __tablename__ = "organization_invitations"
    
    # Foreign keys
    organization_id = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    invited_by = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    
    # Invitation properties
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="member")
    status = Column(String(50), nullable=False, default="pending")
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Entity", foreign_keys=[organization_id], backref="invitations_received")
    inviter = relationship("Entity", foreign_keys=[invited_by], backref="invitations_sent")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.invited_at:
            self.invited_at = datetime.utcnow()
        if not self.expires_at:
            # Default to 7 days from now
            self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    @classmethod
    def get_by_id(cls, db, invitation_id: UUID):
        """
        Get invitation by ID.
        
        Args:
            db: Database session
            invitation_id: Invitation ID
            
        Returns:
            OrganizationInvitation instance or None
        """
        return db.query(cls).filter(cls.id == invitation_id).first()
    
    @classmethod
    def get_by_organization_and_email(cls, db, organization_id: UUID, email: str):
        """
        Get invitation by organization and email.
        
        Args:
            db: Database session
            organization_id: Organization ID
            email: Invitee email
            
        Returns:
            OrganizationInvitation instance or None
        """
        return db.query(cls).filter(
            cls.organization_id == organization_id,
            cls.email == email
        ).first()
    
    @classmethod
    def get_organization_invitations(cls, db, organization_id: UUID, status: Optional[str] = None):
        """
        Get all invitations for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            status: Filter by status (optional)
            
        Returns:
            List of OrganizationInvitation instances
        """
        query = db.query(cls).filter(cls.organization_id == organization_id)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.invited_at.desc()).all()
    
    @classmethod
    def get_user_invitations(cls, db, email: str, status: Optional[str] = None):
        """
        Get all invitations for a user by email.
        
        Args:
            db: Database session
            email: User email
            status: Filter by status (optional)
            
        Returns:
            List of OrganizationInvitation instances
        """
        query = db.query(cls).filter(cls.email == email)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.invited_at.desc()).all()
    
    @classmethod
    def get_expired_invitations(cls, db):
        """
        Get all expired invitations.
        
        Args:
            db: Database session
            
        Returns:
            List of expired OrganizationInvitation instances
        """
        return db.query(cls).filter(
            cls.status == "pending",
            cls.expires_at < datetime.utcnow()
        ).all()
    
    def is_expired(self) -> bool:
        """
        Check if invitation has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at
    
    def is_pending(self) -> bool:
        """
        Check if invitation is pending.
        
        Returns:
            True if pending, False otherwise
        """
        return self.status == "pending" and not self.is_expired()
    
    def can_be_accepted(self) -> bool:
        """
        Check if invitation can be accepted.
        
        Returns:
            True if can be accepted, False otherwise
        """
        return self.status == "pending" and not self.is_expired()
    
    def can_be_declined(self) -> bool:
        """
        Check if invitation can be declined.
        
        Returns:
            True if can be declined, False otherwise
        """
        return self.status == "pending" and not self.is_expired()
    
    def accept(self):
        """
        Accept the invitation.
        
        Sets status to 'accepted' and records acceptance time.
        """
        if self.can_be_accepted():
            self.status = "accepted"
            self.accepted_at = datetime.utcnow()
    
    def decline(self):
        """
        Decline the invitation.
        
        Sets status to 'declined' and records decline time.
        """
        if self.can_be_declined():
            self.status = "declined"
            self.declined_at = datetime.utcnow()
    
    def expire(self):
        """
        Mark invitation as expired.
        
        Sets status to 'expired'.
        """
        if self.status == "pending":
            self.status = "expired"
    
    def get_days_until_expiry(self) -> int:
        """
        Get number of days until invitation expires.
        
        Returns:
            Number of days until expiry (negative if already expired)
        """
        delta = self.expires_at - datetime.utcnow()
        return delta.days
    
    def __repr__(self):
        """String representation of the organization invitation."""
        return f"<OrganizationInvitation(id={self.id}, org_id={self.organization_id}, email={self.email}, status={self.status})>" 