"""
Membership Removal Request model for LMS Core API.

This module contains the MembershipRemovalRequest model for managing
membership removal requests and approval workflows.
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from uuid import UUID

from .base import BaseModel


class MembershipRemovalRequest(BaseModel):
    """
    Membership Removal Request model for managing removal requests.
    
    Represents a user's request to be removed from an organization.
    """
    
    __tablename__ = "membership_removal_requests"
    
    # Foreign keys
    organization_id = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    requested_by = Column(PostgresUUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    approved_by = Column(PostgresUUID, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    
    # Request properties
    status = Column(String(50), nullable=False, default="pending")
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Entity", foreign_keys=[organization_id], backref="removal_requests_received")
    user = relationship("Entity", foreign_keys=[user_id], backref="removal_requests_made")
    requester = relationship("Entity", foreign_keys=[requested_by], backref="removal_requests_requested")
    approver = relationship("Entity", foreign_keys=[approved_by], backref="removal_requests_approved")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.requested_at:
            self.requested_at = datetime.utcnow()
    
    @classmethod
    def get_by_id(cls, db, request_id: UUID):
        """
        Get removal request by ID.
        
        Args:
            db: Database session
            request_id: Request ID
            
        Returns:
            MembershipRemovalRequest instance or None
        """
        return db.query(cls).filter(cls.id == request_id).first()
    
    @classmethod
    def get_by_organization_and_user(cls, db, organization_id: UUID, user_id: UUID):
        """
        Get removal request by organization and user IDs.
        
        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            MembershipRemovalRequest instance or None
        """
        return db.query(cls).filter(
            cls.organization_id == organization_id,
            cls.user_id == user_id
        ).first()
    
    @classmethod
    def get_organization_requests(cls, db, organization_id: UUID, status: Optional[str] = None):
        """
        Get all removal requests for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            status: Filter by status (optional)
            
        Returns:
            List of MembershipRemovalRequest instances
        """
        query = db.query(cls).filter(cls.organization_id == organization_id)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.requested_at.desc()).all()
    
    @classmethod
    def get_user_requests(cls, db, user_id: UUID, status: Optional[str] = None):
        """
        Get all removal requests by a user.
        
        Args:
            db: Database session
            user_id: User ID
            status: Filter by status (optional)
            
        Returns:
            List of MembershipRemovalRequest instances
        """
        query = db.query(cls).filter(cls.user_id == user_id)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.requested_at.desc()).all()
    
    @classmethod
    def get_pending_requests(cls, db, organization_id: UUID):
        """
        Get all pending removal requests for an organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            
        Returns:
            List of pending MembershipRemovalRequest instances
        """
        return cls.get_organization_requests(db, organization_id, status="pending")
    
    def is_pending(self) -> bool:
        """
        Check if request is pending.
        
        Returns:
            True if pending, False otherwise
        """
        return self.status == "pending"
    
    def is_approved(self) -> bool:
        """
        Check if request is approved.
        
        Returns:
            True if approved, False otherwise
        """
        return self.status == "approved"
    
    def is_denied(self) -> bool:
        """
        Check if request is denied.
        
        Returns:
            True if denied, False otherwise
        """
        return self.status == "denied"
    
    def can_be_approved(self) -> bool:
        """
        Check if request can be approved.
        
        Returns:
            True if can be approved, False otherwise
        """
        return self.status == "pending"
    
    def can_be_denied(self) -> bool:
        """
        Check if request can be denied.
        
        Returns:
            True if can be denied, False otherwise
        """
        return self.status == "pending"
    
    def approve(self, approved_by: UUID, admin_notes: Optional[str] = None):
        """
        Approve the removal request.
        
        Args:
            approved_by: ID of the admin who approved the request
            admin_notes: Optional notes from the admin
        """
        if self.can_be_approved():
            self.status = "approved"
            self.approved_by = approved_by
            self.approved_at = datetime.utcnow()
            if admin_notes:
                self.admin_notes = admin_notes
    
    def deny(self, approved_by: UUID, admin_notes: Optional[str] = None):
        """
        Deny the removal request.
        
        Args:
            approved_by: ID of the admin who denied the request
            admin_notes: Optional notes from the admin
        """
        if self.can_be_denied():
            self.status = "denied"
            self.approved_by = approved_by
            self.approved_at = datetime.utcnow()
            if admin_notes:
                self.admin_notes = admin_notes
    
    def get_days_since_request(self) -> int:
        """
        Get number of days since the request was made.
        
        Returns:
            Number of days since request
        """
        delta = datetime.utcnow() - self.requested_at
        return delta.days
    
    def __repr__(self):
        """String representation of the membership removal request."""
        return f"<MembershipRemovalRequest(id={self.id}, org_id={self.organization_id}, user_id={self.user_id}, status={self.status})>" 