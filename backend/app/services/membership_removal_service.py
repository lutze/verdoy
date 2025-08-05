"""
Membership Removal Service for LMS Core API.

This module contains the MembershipRemovalService for managing
membership removal requests and approval workflows.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.membership_removal_request import MembershipRemovalRequest
from ..models.organization_member import OrganizationMember
from ..models.user import User
from ..models.organization import Organization
from ..exceptions import (
    ServiceException,
    UserNotFoundException,
    OrganizationNotFoundException,
    PermissionDeniedException,
    RemovalRequestNotFoundException,
    DuplicateRemovalRequestException,
    MemberNotFoundException
)
from .base import BaseService

logger = logging.getLogger(__name__)


class MembershipRemovalService(BaseService[MembershipRemovalRequest]):
    """
    Service for managing membership removal requests.
    
    Handles creating removal requests, approving/denying them, and managing
    the removal workflow.
    """
    
    @property
    def model_class(self) -> type[MembershipRemovalRequest]:
        return MembershipRemovalRequest
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create_removal_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        requested_by: UUID,
        reason: Optional[str] = None
    ) -> MembershipRemovalRequest:
        """
        Create a membership removal request.
        
        Args:
            organization_id: Organization ID
            user_id: User ID requesting removal
            requested_by: ID of user making the request
            reason: Optional reason for removal request
            
        Returns:
            MembershipRemovalRequest instance
            
        Raises:
            UserNotFoundException: If user not found
            OrganizationNotFoundException: If organization not found
            MemberNotFoundException: If user is not a member
            DuplicateRemovalRequestException: If request already exists
            ServiceException: If operation fails
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")
            
            # Verify organization exists
            organization = self.db.query(Organization).filter(Organization.id == organization_id).first()
            if not organization:
                raise OrganizationNotFoundException(f"Organization {organization_id} not found")
            
            # Verify user is a member
            member = OrganizationMember.get_by_organization_and_user(self.db, organization_id, user_id)
            if not member or not member.is_active:
                raise MemberNotFoundException(f"User {user_id} is not an active member of organization {organization_id}")
            
            # Check if removal request already exists
            existing_request = MembershipRemovalRequest.get_by_organization_and_user(
                self.db, organization_id, user_id
            )
            if existing_request and existing_request.is_pending():
                raise DuplicateRemovalRequestException(f"Removal request already exists for user {user_id}")
            
            # Create removal request
            removal_request = MembershipRemovalRequest(
                organization_id=organization_id,
                user_id=user_id,
                requested_by=requested_by,
                reason=reason
            )
            
            self.db.add(removal_request)
            self.db.commit()
            
            # Audit log
            self.audit_log("removal_request_created", organization_id, {
                "user_id": str(user_id),
                "requested_by": str(requested_by),
                "reason": reason,
                "organization_name": organization.name
            })
            
            logger.info(f"Removal request created for user {user_id} in organization {organization_id}")
            return removal_request
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (UserNotFoundException, OrganizationNotFoundException, 
                             MemberNotFoundException, DuplicateRemovalRequestException)):
                raise
            logger.error(f"Failed to create removal request: {str(e)}")
            raise ServiceException(f"Failed to create removal request: {str(e)}")
    
    def get_removal_request(self, request_id: UUID) -> Optional[MembershipRemovalRequest]:
        """
        Get a removal request by ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            MembershipRemovalRequest instance or None
        """
        return MembershipRemovalRequest.get_by_id(self.db, request_id)
    
    def get_organization_requests(
        self, 
        organization_id: UUID, 
        status: Optional[str] = None
    ) -> List[MembershipRemovalRequest]:
        """
        Get all removal requests for an organization.
        
        Args:
            organization_id: Organization ID
            status: Filter by status (optional)
            
        Returns:
            List of MembershipRemovalRequest instances
        """
        return MembershipRemovalRequest.get_organization_requests(self.db, organization_id, status)
    
    def get_user_requests(
        self, 
        user_id: UUID, 
        status: Optional[str] = None
    ) -> List[MembershipRemovalRequest]:
        """
        Get all removal requests by a user.
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            
        Returns:
            List of MembershipRemovalRequest instances
        """
        return MembershipRemovalRequest.get_user_requests(self.db, user_id, status)
    
    def get_pending_requests(self, organization_id: UUID) -> List[MembershipRemovalRequest]:
        """
        Get all pending removal requests for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of pending MembershipRemovalRequest instances
        """
        return MembershipRemovalRequest.get_pending_requests(self.db, organization_id)
    
    def approve_removal_request(
        self, 
        request_id: UUID, 
        approved_by: UUID,
        admin_notes: Optional[str] = None
    ) -> MembershipRemovalRequest:
        """
        Approve a membership removal request.
        
        Args:
            request_id: Request ID
            approved_by: ID of admin approving the request
            admin_notes: Optional notes from the admin
            
        Returns:
            MembershipRemovalRequest instance
            
        Raises:
            RemovalRequestNotFoundException: If request not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Get removal request
            removal_request = self.get_removal_request(request_id)
            if not removal_request:
                raise RemovalRequestNotFoundException(f"Removal request {request_id} not found")
            
            # Verify approver has permission
            approver_member = OrganizationMember.get_by_organization_and_user(
                self.db, removal_request.organization_id, approved_by
            )
            if not approver_member or not approver_member.can_approve_removals():
                raise PermissionDeniedException("Only organization admins can approve removal requests")
            
            # Check if request can be approved
            if not removal_request.can_be_approved():
                raise ServiceException("Removal request cannot be approved")
            
            # Approve request
            removal_request.approve(approved_by, admin_notes)
            
            # Remove user from organization
            from .organization_member_service import OrganizationMemberService
            member_service = OrganizationMemberService(self.db)
            member_service.remove_member(
                organization_id=removal_request.organization_id,
                user_id=removal_request.user_id,
                removed_by=approved_by
            )
            
            self.db.commit()
            
            # Audit log
            self.audit_log("removal_request_approved", removal_request.organization_id, {
                "request_id": str(request_id),
                "user_id": str(removal_request.user_id),
                "approved_by": str(approved_by),
                "admin_notes": admin_notes
            })
            
            logger.info(f"Removal request {request_id} approved by user {approved_by}")
            return removal_request
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (RemovalRequestNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to approve removal request: {str(e)}")
            raise ServiceException(f"Failed to approve removal request: {str(e)}")
    
    def deny_removal_request(
        self, 
        request_id: UUID, 
        denied_by: UUID,
        admin_notes: Optional[str] = None
    ) -> MembershipRemovalRequest:
        """
        Deny a membership removal request.
        
        Args:
            request_id: Request ID
            denied_by: ID of admin denying the request
            admin_notes: Optional notes from the admin
            
        Returns:
            MembershipRemovalRequest instance
            
        Raises:
            RemovalRequestNotFoundException: If request not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Get removal request
            removal_request = self.get_removal_request(request_id)
            if not removal_request:
                raise RemovalRequestNotFoundException(f"Removal request {request_id} not found")
            
            # Verify denier has permission
            denier_member = OrganizationMember.get_by_organization_and_user(
                self.db, removal_request.organization_id, denied_by
            )
            if not denier_member or not denier_member.can_approve_removals():
                raise PermissionDeniedException("Only organization admins can deny removal requests")
            
            # Check if request can be denied
            if not removal_request.can_be_denied():
                raise ServiceException("Removal request cannot be denied")
            
            # Deny request
            removal_request.deny(denied_by, admin_notes)
            
            self.db.commit()
            
            # Audit log
            self.audit_log("removal_request_denied", removal_request.organization_id, {
                "request_id": str(request_id),
                "user_id": str(removal_request.user_id),
                "denied_by": str(denied_by),
                "admin_notes": admin_notes
            })
            
            logger.info(f"Removal request {request_id} denied by user {denied_by}")
            return removal_request
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (RemovalRequestNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to deny removal request: {str(e)}")
            raise ServiceException(f"Failed to deny removal request: {str(e)}")
    
    def cancel_removal_request(
        self, 
        request_id: UUID, 
        cancelled_by: UUID
    ) -> MembershipRemovalRequest:
        """
        Cancel a membership removal request.
        
        Args:
            request_id: Request ID
            cancelled_by: ID of user cancelling the request
            
        Returns:
            MembershipRemovalRequest instance
            
        Raises:
            RemovalRequestNotFoundException: If request not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Get removal request
            removal_request = self.get_removal_request(request_id)
            if not removal_request:
                raise RemovalRequestNotFoundException(f"Removal request {request_id} not found")
            
            # Verify canceller has permission (request owner or admin)
            if removal_request.requested_by != cancelled_by:
                canceller_member = OrganizationMember.get_by_organization_and_user(
                    self.db, removal_request.organization_id, cancelled_by
                )
                if not canceller_member or not canceller_member.can_approve_removals():
                    raise PermissionDeniedException("Only request owner or organization admins can cancel requests")
            
            # Check if request can be cancelled
            if not removal_request.is_pending():
                raise ServiceException("Only pending requests can be cancelled")
            
            # Cancel request
            removal_request.status = "cancelled"
            
            self.db.commit()
            
            # Audit log
            self.audit_log("removal_request_cancelled", removal_request.organization_id, {
                "request_id": str(request_id),
                "user_id": str(removal_request.user_id),
                "cancelled_by": str(cancelled_by)
            })
            
            logger.info(f"Removal request {request_id} cancelled by user {cancelled_by}")
            return removal_request
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (RemovalRequestNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to cancel removal request: {str(e)}")
            raise ServiceException(f"Failed to cancel removal request: {str(e)}")
    
    def get_removal_request_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get removal request statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary with removal request statistics
        """
        requests = self.get_organization_requests(organization_id)
        
        stats = {
            "total_requests": len(requests),
            "pending": len([r for r in requests if r.status == "pending"]),
            "approved": len([r for r in requests if r.status == "approved"]),
            "denied": len([r for r in requests if r.status == "denied"]),
            "recent_requests": len([r for r in requests if r.requested_at and (datetime.utcnow() - r.requested_at).days <= 7])
        }
        
        return stats 