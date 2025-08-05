"""
Organization Member Service for LMS Core API.

This module contains the OrganizationMemberService for managing
organization membership and member operations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.organization_member import OrganizationMember
from ..models.user import User
from ..models.organization import Organization
from ..exceptions import (
    ServiceException,
    UserNotFoundException,
    OrganizationNotFoundException,
    PermissionDeniedException,
    MemberNotFoundException,
    DuplicateMemberException
)
from .base import BaseService

logger = logging.getLogger(__name__)


class OrganizationMemberService(BaseService[OrganizationMember]):
    """
    Service for managing organization members.
    
    Handles adding members, updating roles, and managing membership.
    """
    
    @property
    def model_class(self) -> type[OrganizationMember]:
        return OrganizationMember
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def add_member(
        self, 
        organization_id: UUID, 
        user_id: UUID, 
        role: str = "member",
        invited_by: Optional[UUID] = None
    ) -> OrganizationMember:
        """
        Add a user to an organization as a member.
        
        Args:
            organization_id: Organization ID
            user_id: User ID to add
            role: Member role (admin, member, viewer)
            invited_by: ID of user who sent the invitation (optional)
            
        Returns:
            OrganizationMember instance
            
        Raises:
            UserNotFoundException: If user not found
            OrganizationNotFoundException: If organization not found
            DuplicateMemberException: If user is already a member
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
            
            # Check if user is already a member
            existing_member = OrganizationMember.get_by_organization_and_user(
                self.db, organization_id, user_id
            )
            if existing_member:
                raise DuplicateMemberException(f"User {user_id} is already a member of organization {organization_id}")
            
            # Create new member
            member = OrganizationMember(
                organization_id=organization_id,
                user_id=user_id,
                role=role,
                invited_by=invited_by,
                invited_at=datetime.utcnow(),
                accepted_at=datetime.utcnow()  # Direct addition is considered accepted
            )
            
            self.db.add(member)
            self.db.commit()
            
            # Audit log
            self.audit_log("member_added", organization_id, {
                "user_id": str(user_id),
                "role": role,
                "invited_by": str(invited_by) if invited_by else None,
                "organization_name": organization.name
            })
            
            logger.info(f"User {user_id} added to organization {organization_id} with role {role}")
            return member
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (UserNotFoundException, OrganizationNotFoundException, DuplicateMemberException)):
                raise
            logger.error(f"Failed to add member: {str(e)}")
            raise ServiceException(f"Failed to add member: {str(e)}")
    
    def get_organization_members(
        self, 
        organization_id: UUID, 
        active_only: bool = True
    ) -> List[OrganizationMember]:
        """
        Get all members of an organization.
        
        Args:
            organization_id: Organization ID
            active_only: Whether to return only active members
            
        Returns:
            List of OrganizationMember instances
        """
        return OrganizationMember.get_organization_members(self.db, organization_id, active_only)
    
    def get_user_organizations(
        self, 
        user_id: UUID, 
        active_only: bool = True
    ) -> List[OrganizationMember]:
        """
        Get all organizations a user belongs to.
        
        Args:
            user_id: User ID
            active_only: Whether to return only active memberships
            
        Returns:
            List of OrganizationMember instances
        """
        return OrganizationMember.get_user_organizations(self.db, user_id, active_only)
    
    def get_member(
        self, 
        organization_id: UUID, 
        user_id: UUID
    ) -> Optional[OrganizationMember]:
        """
        Get a specific member of an organization.
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            
        Returns:
            OrganizationMember instance or None
        """
        return OrganizationMember.get_by_organization_and_user(self.db, organization_id, user_id)
    
    def update_member_role(
        self, 
        organization_id: UUID, 
        user_id: UUID, 
        new_role: str,
        updated_by: UUID
    ) -> OrganizationMember:
        """
        Update a member's role in an organization.
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            new_role: New role (admin, member, viewer)
            updated_by: ID of user making the change
            
        Returns:
            Updated OrganizationMember instance
            
        Raises:
            MemberNotFoundException: If member not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Verify member exists
            member = self.get_member(organization_id, user_id)
            if not member:
                raise MemberNotFoundException(f"User {user_id} is not a member of organization {organization_id}")
            
            # Verify updater has permission
            updater_member = self.get_member(organization_id, updated_by)
            if not updater_member or not updater_member.can_manage_roles():
                raise PermissionDeniedException("Only organization admins can update member roles")
            
            # Update role
            old_role = member.role
            member.role = new_role
            
            self.db.commit()
            
            # Audit log
            self.audit_log("member_role_updated", organization_id, {
                "user_id": str(user_id),
                "old_role": old_role,
                "new_role": new_role,
                "updated_by": str(updated_by)
            })
            
            logger.info(f"User {user_id} role updated from {old_role} to {new_role} in organization {organization_id}")
            return member
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (MemberNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to update member role: {str(e)}")
            raise ServiceException(f"Failed to update member role: {str(e)}")
    
    def remove_member(
        self, 
        organization_id: UUID, 
        user_id: UUID,
        removed_by: UUID
    ) -> bool:
        """
        Remove a member from an organization.
        
        Args:
            organization_id: Organization ID
            user_id: User ID to remove
            removed_by: ID of user performing the removal
            
        Returns:
            True if member removed successfully
            
        Raises:
            MemberNotFoundException: If member not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Verify member exists
            member = self.get_member(organization_id, user_id)
            if not member:
                raise MemberNotFoundException(f"User {user_id} is not a member of organization {organization_id}")
            
            # Verify remover has permission
            remover_member = self.get_member(organization_id, removed_by)
            if not remover_member or not remover_member.can_manage_roles():
                raise PermissionDeniedException("Only organization admins can remove members")
            
            # Check if trying to remove the last admin
            if member.role == "admin":
                admin_count = len(OrganizationMember.get_organization_admins(self.db, organization_id))
                if admin_count <= 1:
                    raise ServiceException("Cannot remove the last admin from an organization")
            
            # Remove member
            self.db.delete(member)
            self.db.commit()
            
            # Audit log
            self.audit_log("member_removed", organization_id, {
                "user_id": str(user_id),
                "role": member.role,
                "removed_by": str(removed_by)
            })
            
            logger.info(f"User {user_id} removed from organization {organization_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (MemberNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to remove member: {str(e)}")
            raise ServiceException(f"Failed to remove member: {str(e)}")
    
    def deactivate_member(
        self, 
        organization_id: UUID, 
        user_id: UUID,
        deactivated_by: UUID
    ) -> OrganizationMember:
        """
        Deactivate a member (soft delete).
        
        Args:
            organization_id: Organization ID
            user_id: User ID to deactivate
            deactivated_by: ID of user performing the deactivation
            
        Returns:
            Updated OrganizationMember instance
            
        Raises:
            MemberNotFoundException: If member not found
            PermissionDeniedException: If user lacks permission
            ServiceException: If operation fails
        """
        try:
            # Verify member exists
            member = self.get_member(organization_id, user_id)
            if not member:
                raise MemberNotFoundException(f"User {user_id} is not a member of organization {organization_id}")
            
            # Verify deactivator has permission
            deactivator_member = self.get_member(organization_id, deactivated_by)
            if not deactivator_member or not deactivator_member.can_manage_roles():
                raise PermissionDeniedException("Only organization admins can deactivate members")
            
            # Deactivate member
            member.is_active = False
            
            self.db.commit()
            
            # Audit log
            self.audit_log("member_deactivated", organization_id, {
                "user_id": str(user_id),
                "role": member.role,
                "deactivated_by": str(deactivated_by)
            })
            
            logger.info(f"User {user_id} deactivated in organization {organization_id}")
            return member
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (MemberNotFoundException, PermissionDeniedException)):
                raise
            logger.error(f"Failed to deactivate member: {str(e)}")
            raise ServiceException(f"Failed to deactivate member: {str(e)}")
    
    def get_member_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get member statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dictionary with member statistics
        """
        members = self.get_organization_members(organization_id, active_only=True)
        
        stats = {
            "total_members": len(members),
            "admins": len([m for m in members if m.role == "admin"]),
            "members": len([m for m in members if m.role == "member"]),
            "viewers": len([m for m in members if m.role == "viewer"]),
            "recent_joins": len([m for m in members if m.joined_at and (datetime.utcnow() - m.joined_at).days <= 30])
        }
        
        return stats 