"""
Organization Invitation Service for VerdoyLab API.

This module contains the OrganizationInvitationService for managing
organization invitations and acceptance workflows.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.organization_invitation import OrganizationInvitation
from ..models.organization_member import OrganizationMember
from ..models.user import User
from ..models.organization import Organization
from ..exceptions import (
    ServiceException,
    UserNotFoundException,
    OrganizationNotFoundException,
    PermissionDeniedException,
    InvitationNotFoundException,
    InvitationExpiredException,
    DuplicateInvitationException,
    DuplicateMemberException
)
from .base import BaseService

logger = logging.getLogger(__name__)


class OrganizationInvitationService(BaseService[OrganizationInvitation]):
    """
    Service for managing organization invitations.
    
    Handles sending invitations, accepting/declining them, and managing
    invitation workflows.
    """
    
    @property
    def model_class(self) -> type[OrganizationInvitation]:
        return OrganizationInvitation
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def send_invitation(
        self,
        organization_id: UUID,
        email: str,
        invited_by: UUID,
        role: str = "member",
        message: Optional[str] = None,
        expires_in_days: int = 7
    ) -> OrganizationInvitation:
        """
        Send an invitation to join an organization.
        
        Args:
            organization_id: Organization ID
            email: Email address to invite
            role: Role to assign when accepted
            invited_by: ID of user sending the invitation
            message: Optional message to include
            expires_in_days: Days until invitation expires
            
        Returns:
            OrganizationInvitation instance
            
        Raises:
            OrganizationNotFoundException: If organization not found
            PermissionDeniedException: If user lacks permission
            DuplicateInvitationException: If invitation already exists
            ServiceException: If operation fails
        """
        try:
            # Verify organization exists
            organization = self.db.query(Organization).filter(Organization.id == organization_id).first()
            if not organization:
                raise OrganizationNotFoundException(f"Organization {organization_id} not found")
            
            # Verify inviter has permission
            inviter_member = OrganizationMember.get_by_organization_and_user(
                self.db, organization_id, invited_by
            )
            if not inviter_member or not inviter_member.can_invite_members():
                raise PermissionDeniedException("Only organization admins can send invitations")
            
            # Check if invitation already exists
            existing_invitation = OrganizationInvitation.get_by_organization_and_email(
                self.db, organization_id, email
            )
            if existing_invitation and existing_invitation.status == "pending":
                raise DuplicateInvitationException(f"Invitation already exists for {email}")
            
            # Check if user is already a member
            user = User.get_by_email(self.db, email)
            if user:
                existing_member = OrganizationMember.get_by_organization_and_user(
                    self.db, organization_id, user.id
                )
                if existing_member and existing_member.is_active:
                    raise DuplicateMemberException(f"User {email} is already a member of this organization")
            
            # Create invitation
            invitation = OrganizationInvitation(
                organization_id=organization_id,
                email=email,
                role=role,
                invited_by=invited_by,
                message=message,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
            )
            
            self.db.add(invitation)
            self.db.commit()
            
            # Audit log
            self.audit_log("invitation_sent", organization_id, {
                "email": email,
                "role": role,
                "invited_by": str(invited_by),
                "expires_at": invitation.expires_at.isoformat(),
                "organization_name": organization.name
            })
            
            logger.info(f"Invitation sent to {email} for organization {organization_id}")
            return invitation
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (OrganizationNotFoundException, PermissionDeniedException, 
                             DuplicateInvitationException, DuplicateMemberException)):
                raise
            logger.error(f"Failed to send invitation: {str(e)}")
            raise ServiceException(f"Failed to send invitation: {str(e)}")
    
    def get_invitation(self, invitation_id: UUID) -> Optional[OrganizationInvitation]:
        """
        Get an invitation by ID.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            OrganizationInvitation instance or None
        """
        return OrganizationInvitation.get_by_id(self.db, invitation_id)
    
    def get_organization_invitations(
        self, 
        organization_id: UUID, 
        status: Optional[str] = None
    ) -> List[OrganizationInvitation]:
        """
        Get all invitations for an organization.
        
        Args:
            organization_id: Organization ID
            status: Filter by status (optional)
            
        Returns:
            List of OrganizationInvitation instances
        """
        return OrganizationInvitation.get_organization_invitations(self.db, organization_id, status)
    
    def get_user_invitations(
        self, 
        email: str, 
        status: Optional[str] = None
    ) -> List[OrganizationInvitation]:
        """
        Get all invitations for a user by email.
        
        Args:
            email: User email
            status: Filter by status (optional)
            
        Returns:
            List of OrganizationInvitation instances
        """
        return OrganizationInvitation.get_user_invitations(self.db, email, status)
    
    def accept_invitation(
        self, 
        invitation_id: UUID, 
        user_id: UUID
    ) -> OrganizationMember:
        """
        Accept an organization invitation.
        
        Args:
            invitation_id: Invitation ID
            user_id: ID of user accepting the invitation
            
        Returns:
            OrganizationMember instance
            
        Raises:
            InvitationNotFoundException: If invitation not found
            InvitationExpiredException: If invitation has expired
            ServiceException: If operation fails
        """
        try:
            # Get invitation
            invitation = self.get_invitation(invitation_id)
            if not invitation:
                raise InvitationNotFoundException(f"Invitation {invitation_id} not found")
            
            # Check if invitation can be accepted
            if not invitation.can_be_accepted():
                if invitation.is_expired():
                    raise InvitationExpiredException("Invitation has expired")
                else:
                    raise ServiceException("Invitation cannot be accepted")
            
            # Verify user email matches invitation
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.email != invitation.email:
                raise ServiceException("User email does not match invitation")
            
            # Accept invitation
            invitation.accept()
            
            # Add user to organization
            from .organization_member_service import OrganizationMemberService
            member_service = OrganizationMemberService(self.db)
            member = member_service.add_member(
                organization_id=invitation.organization_id,
                user_id=user_id,
                role=invitation.role,
                invited_by=invitation.invited_by
            )
            
            self.db.commit()
            
            # Audit log
            self.audit_log("invitation_accepted", invitation.organization_id, {
                "invitation_id": str(invitation_id),
                "user_id": str(user_id),
                "email": invitation.email,
                "role": invitation.role
            })
            
            logger.info(f"Invitation {invitation_id} accepted by user {user_id}")
            return member
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (InvitationNotFoundException, InvitationExpiredException)):
                raise
            logger.error(f"Failed to accept invitation: {str(e)}")
            raise ServiceException(f"Failed to accept invitation: {str(e)}")
    
    def decline_invitation(self, invitation_id: UUID, user_id: UUID) -> OrganizationInvitation:
        """
        Decline an organization invitation.
        
        Args:
            invitation_id: Invitation ID
            user_id: ID of user declining the invitation
            
        Returns:
            OrganizationInvitation instance
            
        Raises:
            InvitationNotFoundException: If invitation not found
            InvitationExpiredException: If invitation has expired
            ServiceException: If operation fails
        """
        try:
            # Get invitation
            invitation = self.get_invitation(invitation_id)
            if not invitation:
                raise InvitationNotFoundException(f"Invitation {invitation_id} not found")
            
            # Check if invitation can be declined
            if not invitation.can_be_declined():
                if invitation.is_expired():
                    raise InvitationExpiredException("Invitation has expired")
                else:
                    raise ServiceException("Invitation cannot be declined")
            
            # Verify user email matches invitation
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.email != invitation.email:
                raise ServiceException("User email does not match invitation")
            
            # Decline invitation
            invitation.decline()
            
            self.db.commit()
            
            # Audit log
            self.audit_log("invitation_declined", invitation.organization_id, {
                "invitation_id": str(invitation_id),
                "user_id": str(user_id),
                "email": invitation.email
            })
            
            logger.info(f"Invitation {invitation_id} declined by user {user_id}")
            return invitation
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (InvitationNotFoundException, InvitationExpiredException)):
                raise
            logger.error(f"Failed to decline invitation: {str(e)}")
            raise ServiceException(f"Failed to decline invitation: {str(e)}")
    
    def cancel_invitation(
        self, 
        invitation_id: UUID, 
        cancelled_by: UUID
    ) -> OrganizationInvitation:
        """
        Cancel an organization invitation.
        
        Args:
            invitation_id: Invitation ID
            cancelled_by: ID of user cancelling the invitation
            
        Returns:
            OrganizationInvitation instance
            
        Raises:
            InvitationNotFoundException: If invitation not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Get invitation
            invitation = self.get_invitation(invitation_id)
            if not invitation:
                raise InvitationNotFoundException(f"Invitation {invitation_id} not found")
            
            # Verify canceller has permission
            canceller_member = OrganizationMember.get_by_organization_and_user(
                self.db, invitation.organization_id, cancelled_by
            )
            if not canceller_member or not canceller_member.can_invite_members():
                raise PermissionDeniedException("Only organization admins can cancel invitations")
            
            # Cancel invitation
            invitation.status = "cancelled"
            
            self.db.commit()
            
            # Audit log
            self.audit_log("invitation_cancelled", invitation.organization_id, {
                "invitation_id": str(invitation_id),
                "cancelled_by": str(cancelled_by),
                "email": invitation.email
            })
            
            logger.info(f"Invitation {invitation_id} cancelled by user {cancelled_by}")
            return invitation
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (InvitationNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to cancel invitation: {str(e)}")
            raise ServiceException(f"Failed to cancel invitation: {str(e)}")
    
    def expire_invitations(self) -> int:
        """
        Expire all pending invitations that have passed their expiry date.
        
        Returns:
            Number of invitations expired
        """
        try:
            expired_invitations = OrganizationInvitation.get_expired_invitations(self.db)
            
            for invitation in expired_invitations:
                invitation.expire()
            
            self.db.commit()
            
            logger.info(f"Expired {len(expired_invitations)} invitations")
            return len(expired_invitations)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to expire invitations: {str(e)}")
            raise ServiceException(f"Failed to expire invitations: {str(e)}")
    
    def get_invitation_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get invitation statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary with invitation statistics
        """
        invitations = self.get_organization_invitations(organization_id)
        
        stats = {
            "total_invitations": len(invitations),
            "pending": len([i for i in invitations if i.status == "pending"]),
            "accepted": len([i for i in invitations if i.status == "accepted"]),
            "declined": len([i for i in invitations if i.status == "declined"]),
            "expired": len([i for i in invitations if i.status == "expired"]),
            "recent_invitations": len([i for i in invitations if i.invited_at and (datetime.utcnow() - i.invited_at).days <= 7])
        }
        
        return stats 