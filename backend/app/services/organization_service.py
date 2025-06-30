"""
Organization service for multi-tenant organization management.

This service handles:
- Organization creation and management
- Multi-tenant data isolation
- User-organization relationships
- Organization settings and configuration
- Billing and subscription management
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from uuid import UUID
import logging

from .base import BaseService
from ..models.organization import Organization
from ..models.user import User
from ..schemas.organization import OrganizationCreate, OrganizationUpdate
from ..exceptions import (
    ServiceException,
    ValidationException,
    OrganizationAlreadyExistsException,
    OrganizationNotFoundException,
    UserNotFoundException
)

logger = logging.getLogger(__name__)


class OrganizationService(BaseService[Organization]):
    """
    Organization service for multi-tenant organization management.
    
    This service provides business logic for:
    - Organization creation and management
    - Multi-tenant data isolation and security
    - User-organization relationship management
    - Organization settings and configuration
    - Billing and subscription integration
    """
    
    @property
    def model_class(self) -> type[Organization]:
        """Return the Organization model class."""
        return Organization
    
    def create_organization(self, org_data: OrganizationCreate, created_by: Optional[UUID] = None) -> Organization:
        """
        Create a new organization.
        
        Args:
            org_data: Organization creation data
            created_by: User ID who created the organization
            
        Returns:
            The created organization
            
        Raises:
            OrganizationAlreadyExistsException: If organization already exists
            ValidationException: If data validation fails
            ServiceException: If creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate organization data
            self.validate_organization_data(org_data)
            
            # Check if organization already exists
            if self.organization_exists_by_name(org_data.name):
                raise OrganizationAlreadyExistsException(f"Organization with name '{org_data.name}' already exists")
            
            # Create organization
            organization = Organization(
                name=org_data.name,
                description=org_data.description,
                is_active=True,
                settings=org_data.settings or {},
                billing_info=org_data.billing_info or {}
            )
            
            # Save to database
            self.db.add(organization)
            self.db.commit()
            self.db.refresh(organization)
            
            # Add creator as organization admin if provided
            if created_by:
                self.add_user_to_organization(created_by, organization.id, role="admin")
            
            # Audit log
            self.audit_log("organization_created", organization.id, {
                "name": organization.name,
                "created_by": str(created_by) if created_by else "system"
            })
            
            # Performance monitoring
            self.performance_monitor("organization_creation", start_time)
            
            logger.info(f"Organization created successfully: {organization.name}")
            return organization
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during organization creation: {e}")
            raise OrganizationAlreadyExistsException("Organization with this name already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during organization creation: {e}")
            raise ServiceException("Failed to create organization")
    
    def add_user_to_organization(self, user_id: UUID, organization_id: UUID, role: str = "member") -> bool:
        """
        Add a user to an organization with a specific role.
        
        Args:
            user_id: User ID to add
            organization_id: Organization ID
            role: User role in the organization (admin, member, viewer)
            
        Returns:
            True if user added successfully
            
        Raises:
            UserNotFoundException: If user not found
            OrganizationNotFoundException: If organization not found
            ServiceException: If operation fails
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")
            
            # Verify organization exists
            organization = self.get_by_id_or_raise(organization_id)
            
            # Add user to organization
            if not hasattr(organization, 'users'):
                # Create user-organization relationship
                from ..models.user_organization import UserOrganization
                user_org = UserOrganization(
                    user_id=user_id,
                    organization_id=organization_id,
                    role=role,
                    joined_at=datetime.utcnow()
                )
                self.db.add(user_org)
            else:
                # Update existing relationship
                user_org = self.db.query(UserOrganization).filter(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == organization_id
                ).first()
                
                if user_org:
                    user_org.role = role
                    user_org.updated_at = datetime.utcnow()
                else:
                    user_org = UserOrganization(
                        user_id=user_id,
                        organization_id=organization_id,
                        role=role,
                        joined_at=datetime.utcnow()
                    )
                    self.db.add(user_org)
            
            self.db.commit()
            
            # Audit log
            self.audit_log("user_added_to_organization", organization_id, {
                "user_id": str(user_id),
                "role": role,
                "organization_name": organization.name
            })
            
            logger.info(f"User {user_id} added to organization {organization_id} with role {role}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding user to organization: {e}")
            raise ServiceException("Failed to add user to organization")
    
    def remove_user_from_organization(self, user_id: UUID, organization_id: UUID) -> bool:
        """
        Remove a user from an organization.
        
        Args:
            user_id: User ID to remove
            organization_id: Organization ID
            
        Returns:
            True if user removed successfully
            
        Raises:
            UserNotFoundException: If user not found
            OrganizationNotFoundException: If organization not found
            ServiceException: If operation fails
        """
        try:
            # Verify user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundException(f"User {user_id} not found")
            
            # Verify organization exists
            organization = self.get_by_id_or_raise(organization_id)
            
            # Remove user from organization
            from ..models.user_organization import UserOrganization
            user_org = self.db.query(UserOrganization).filter(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == organization_id
            ).first()
            
            if user_org:
                self.db.delete(user_org)
                self.db.commit()
                
                # Audit log
                self.audit_log("user_removed_from_organization", organization_id, {
                    "user_id": str(user_id),
                    "organization_name": organization.name
                })
                
                logger.info(f"User {user_id} removed from organization {organization_id}")
                return True
            else:
                logger.warning(f"User {user_id} not found in organization {organization_id}")
                return False
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing user from organization: {e}")
            raise ServiceException("Failed to remove user from organization")
    
    def get_organization_users(self, organization_id: UUID, role: Optional[str] = None) -> List[User]:
        """
        Get all users in an organization with optional role filtering.
        
        Args:
            organization_id: Organization ID
            role: Optional role filter
            
        Returns:
            List of users in the organization
        """
        try:
            from ..models.user_organization import UserOrganization
            
            query = self.db.query(User).join(UserOrganization).filter(
                UserOrganization.organization_id == organization_id
            )
            
            if role:
                query = query.filter(UserOrganization.role == role)
            
            users = query.all()
            logger.debug(f"Retrieved {len(users)} users for organization {organization_id}")
            return users
            
        except Exception as e:
            logger.error(f"Error getting organization users: {e}")
            return []
    
    def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        """
        Get all organizations a user belongs to.
        
        Args:
            user_id: User ID
            
        Returns:
            List of organizations the user belongs to
        """
        try:
            from ..models.user_organization import UserOrganization
            
            organizations = self.db.query(Organization).join(UserOrganization).filter(
                UserOrganization.user_id == user_id
            ).all()
            
            logger.debug(f"Retrieved {len(organizations)} organizations for user {user_id}")
            return organizations
            
        except Exception as e:
            logger.error(f"Error getting user organizations: {e}")
            return []
    
    def update_organization_settings(self, organization_id: UUID, settings: Dict[str, Any]) -> Organization:
        """
        Update organization settings.
        
        Args:
            organization_id: Organization ID
            settings: New settings dictionary
            
        Returns:
            The updated organization
            
        Raises:
            OrganizationNotFoundException: If organization not found
            ServiceException: If update fails
        """
        try:
            organization = self.get_by_id_or_raise(organization_id)
            
            # Update settings
            current_settings = organization.settings or {}
            current_settings.update(settings)
            organization.settings = current_settings
            organization.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(organization)
            
            # Audit log
            self.audit_log("organization_settings_updated", organization_id, {
                "updated_settings": list(settings.keys())
            })
            
            logger.info(f"Organization settings updated: {organization.name}")
            return organization
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating organization settings: {e}")
            raise ServiceException("Failed to update organization settings")
    
    def deactivate_organization(self, organization_id: UUID) -> bool:
        """
        Deactivate an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            True if organization deactivated successfully
            
        Raises:
            OrganizationNotFoundException: If organization not found
            ServiceException: If deactivation fails
        """
        try:
            organization = self.get_by_id_or_raise(organization_id)
            
            # Deactivate organization
            organization.is_active = False
            organization.deactivated_at = datetime.utcnow()
            self.db.commit()
            
            # Audit log
            self.audit_log("organization_deactivated", organization_id, {
                "name": organization.name,
                "deactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Organization deactivated: {organization.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating organization: {e}")
            raise ServiceException("Failed to deactivate organization")
    
    def reactivate_organization(self, organization_id: UUID) -> bool:
        """
        Reactivate an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            True if organization reactivated successfully
            
        Raises:
            OrganizationNotFoundException: If organization not found
            ServiceException: If reactivation fails
        """
        try:
            organization = self.get_by_id_or_raise(organization_id)
            
            # Reactivate organization
            organization.is_active = True
            organization.deactivated_at = None
            self.db.commit()
            
            # Audit log
            self.audit_log("organization_reactivated", organization_id, {
                "name": organization.name,
                "reactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Organization reactivated: {organization.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating organization: {e}")
            raise ServiceException("Failed to reactivate organization")
    
    def get_organization_by_name(self, name: str) -> Optional[Organization]:
        """
        Get organization by name.
        
        Args:
            name: Organization name
            
        Returns:
            Organization if found, None otherwise
        """
        try:
            return self.db.query(Organization).filter(Organization.name == name).first()
        except Exception as e:
            logger.error(f"Error getting organization by name: {e}")
            return None
    
    def organization_exists_by_name(self, name: str) -> bool:
        """
        Check if organization exists by name.
        
        Args:
            name: Organization name
            
        Returns:
            True if organization exists, False otherwise
        """
        try:
            return self.db.query(Organization).filter(Organization.name == name).first() is not None
        except Exception as e:
            logger.error(f"Error checking organization existence by name: {e}")
            return False
    
    def validate_organization_data(self, org_data: OrganizationCreate) -> bool:
        """
        Validate organization creation data.
        
        Args:
            org_data: Organization creation data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if not org_data.name:
            raise ValidationException("Organization name is required")
        
        if len(org_data.name) < 2:
            raise ValidationException("Organization name must be at least 2 characters long")
        
        if len(org_data.name) > 100:
            raise ValidationException("Organization name must be less than 100 characters")
        
        if org_data.description and len(org_data.description) > 500:
            raise ValidationException("Organization description must be less than 500 characters")
        
        return True
    
    def get_organization_statistics(self) -> Dict[str, Any]:
        """
        Get organization statistics for analytics.
        
        Returns:
            Dictionary containing organization statistics
        """
        try:
            total_organizations = self.db.query(Organization).count()
            active_organizations = self.db.query(Organization).filter(Organization.is_active == True).count()
            inactive_organizations = self.db.query(Organization).filter(Organization.is_active == False).count()
            
            # Get organizations created in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_organizations = self.db.query(Organization).filter(
                Organization.created_at >= thirty_days_ago
            ).count()
            
            return {
                "total_organizations": total_organizations,
                "active_organizations": active_organizations,
                "inactive_organizations": inactive_organizations,
                "new_organizations_30_days": new_organizations,
                "activation_rate": (active_organizations / total_organizations * 100) if total_organizations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting organization statistics: {e}")
            return {
                "total_organizations": 0,
                "active_organizations": 0,
                "inactive_organizations": 0,
                "new_organizations_30_days": 0,
                "activation_rate": 0
            } 