"""
Organization service for the VerdoyLab system - Entity-based implementation.

This module provides business logic for organization management using the pure entity architecture,
including organization creation, updates, membership management, and invitation handling.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, text
from sqlalchemy.exc import IntegrityError

from ..models.entity import Entity
from ..models.user import User
from ..models.event import Event
from ..models.relationship import Relationship
from ..schemas.organization import OrganizationCreate, OrganizationUpdate
from ..exceptions import (
    ValidationException, NotFoundException, PermissionException,
    ConflictException, BusinessLogicException
)
from .base import BaseService
import logging

logger = logging.getLogger(__name__)


class OrganizationServiceEntity(BaseService):
    """
    Entity-based service for managing organizations and organization memberships.
    
    This service works with the pure entity architecture, storing all organization
    data in the entities table with entity_type = 'organization' and
    entity_type = 'organization.member'.
    """
    
    @property
    def model_class(self):
        """Return the Entity model class."""
        return Entity
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create_organization(
        self, 
        org_data: OrganizationCreate, 
        current_user: User
    ) -> Entity:
        """
        Create a new organization using entity architecture.
        
        Args:
            org_data: Organization creation data
            current_user: Current authenticated user
            
        Returns:
            Created organization entity
            
        Raises:
            ValidationException: If organization data is invalid
            ConflictException: If organization name already exists
        """
        try:
            # Validate organization data
            self._validate_organization_data(org_data)
            
            # Check for duplicate organization name
            if self._organization_name_exists(org_data.name):
                raise ConflictException(f"Organization with name '{org_data.name}' already exists")
            
            # Validate against schema if available
            self._validate_organization_schema(org_data)
            
            # Create organization entity
            organization_entity = Entity(
                entity_type='organization',
                name=org_data.name,
                description=org_data.description,
                status='active',
                organization_id=None,  # Organizations don't belong to other organizations
                properties={
                    'organization_type': org_data.organization_type.value if hasattr(org_data.organization_type, 'value') else str(org_data.organization_type),
                    'contact_email': getattr(org_data, 'contact_email', None),
                    'contact_phone': getattr(org_data, 'contact_phone', None),
                    'website': getattr(org_data, 'website', None),
                    'address': getattr(org_data, 'address', None),
                    'city': getattr(org_data, 'city', None),
                    'state': getattr(org_data, 'state', None),
                    'country': getattr(org_data, 'country', None),
                    'postal_code': getattr(org_data, 'postal_code', None),
                    'timezone': getattr(org_data, 'timezone', 'UTC'),
                    'member_count': 0,
                    'device_count': 0,
                    'subscription_plan': 'free',
                    'settings': org_data.settings or {},
                    'created_by': str(current_user.id)
                }
            )
            
            self.db.add(organization_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Add creator as organization admin
            self._add_user_to_organization(current_user.id, organization_entity.id, 'admin', current_user.id)
            
            # Log creation event
            self._log_event(
                "entity.created",
                organization_entity.id,
                "organization",
                {
                    "organization_name": organization_entity.name,
                    "organization_type": org_data.organization_type.value if hasattr(org_data.organization_type, 'value') else str(org_data.organization_type),
                    "created_by": str(current_user.id)
                },
                current_user.id
            )
            
            # Commit both organization and event together
            self.db.commit()
            self.db.refresh(organization_entity)
            
            return organization_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Organization creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Organization creation failed: {str(e)}")
    
    def get_organization(self, organization_id: UUID, current_user: User) -> Entity:
        """
        Get an organization by ID using entity architecture.
        
        Args:
            organization_id: Organization ID
            current_user: Current authenticated user
            
        Returns:
            Organization entity object
            
        Raises:
            NotFoundException: If organization not found
            PermissionException: If user lacks access
        """
        organization = self.db.query(Entity).filter(
            and_(
                Entity.id == organization_id,
                Entity.entity_type == 'organization'
            )
        ).first()
        
        if not organization:
            raise NotFoundException("Organization not found")
        
        # Check organization access
        if not self._user_has_org_access(current_user, organization_id):
            raise PermissionException("Access denied to organization")
        
        return organization
    
    def list_organizations(
        self,
        current_user: User,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None
    ) -> List[Entity]:
        """
        List organizations with filtering and pagination using entity architecture.
        
        Args:
            current_user: Current authenticated user
            status: Filter by status
            page: Page number
            per_page: Items per page
            search: Search term for name/description
            
        Returns:
            List of organization entities
        """
        # Build query for organization entities
        query = self.db.query(Entity).filter(Entity.entity_type == 'organization')
        
        # Apply status filter
        if status:
            query = query.filter(Entity.status == status)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Entity.name.ilike(search_term),
                    Entity.description.ilike(search_term)
                )
            )
        
        # Apply pagination and ordering
        organizations = query.order_by(desc(Entity.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        return organizations
    
    def update_organization(
        self,
        organization_id: UUID,
        org_data: OrganizationUpdate,
        current_user: User
    ) -> Entity:
        """
        Update an organization using entity architecture.
        
        Args:
            organization_id: Organization ID
            org_data: Organization update data
            current_user: Current authenticated user
            
        Returns:
            Updated organization entity
            
        Raises:
            NotFoundException: If organization not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        organization = self.get_organization(organization_id, current_user)
        
        # Check if name is being changed and if it conflicts
        if org_data.name and org_data.name != organization.name:
            if self._organization_name_exists(org_data.name, exclude_id=organization_id):
                raise ConflictException(f"Organization with name '{org_data.name}' already exists")
        
        # Update entity fields
        update_data = org_data.dict(exclude_unset=True)
        
        # Update basic entity fields
        if 'name' in update_data:
            organization.name = update_data['name']
        if 'description' in update_data:
            organization.description = update_data['description']
        
        # Update properties
        properties = organization.properties.copy()
        for field in ['organization_type', 'contact_email', 'contact_phone', 'website', 
                     'address', 'city', 'state', 'country', 'postal_code', 'timezone', 'settings']:
            if field in update_data:
                if field == 'organization_type' and hasattr(update_data[field], 'value'):
                    properties[field] = update_data[field].value
                else:
                    properties[field] = update_data[field]
        
        organization.properties = properties
        organization.updated_at = datetime.utcnow()
        
        try:
            # Log update event
            self._log_event(
                "entity.updated",
                organization.id,
                "organization",
                {
                    "organization_name": organization.name,
                    "updated_fields": list(update_data.keys())
                },
                current_user.id
            )
            
            # Commit both organization update and event together
            self.db.commit()
            self.db.refresh(organization)
            
            return organization
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Organization update failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Organization update failed: {str(e)}")
    
    def deactivate_organization(self, organization_id: UUID, current_user: User) -> Entity:
        """
        Deactivate an organization (soft delete) using entity architecture.
        
        Args:
            organization_id: Organization ID
            current_user: Current authenticated user
            
        Returns:
            Deactivated organization entity
            
        Raises:
            NotFoundException: If organization not found
            PermissionException: If user lacks access
        """
        organization = self.get_organization(organization_id, current_user)
        
        organization.status = 'inactive'
        organization.updated_at = datetime.utcnow()
        
        # Update properties
        properties = organization.properties.copy()
        properties['deactivated_at'] = datetime.utcnow().isoformat()
        organization.properties = properties
        
        try:
            # Log deactivation event
            self._log_event(
                "entity.updated",
                organization.id,
                "organization",
                {
                    "organization_name": organization.name,
                    "status": "inactive"
                },
                current_user.id
            )
            
            # Commit both organization deactivation and event together
            self.db.commit()
            self.db.refresh(organization)
            
            return organization
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Organization deactivation failed: {str(e)}")
    
    def add_user_to_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str,
        current_user: User
    ) -> Entity:
        """
        Add a user to an organization using entity architecture.
        
        Args:
            user_id: User ID to add
            organization_id: Organization ID
            role: User role in the organization
            current_user: Current authenticated user
            
        Returns:
            Created membership entity
            
        Raises:
            NotFoundException: If user or organization not found
            PermissionException: If user lacks access
            ConflictException: If user is already a member
        """
        # Verify organization exists and user has access
        organization = self.get_organization(organization_id, current_user)
        
        # Verify user exists
        user = self.db.query(Entity).filter(
            and_(
                Entity.id == user_id,
                Entity.entity_type == 'user'
            )
        ).first()
        
        if not user:
            raise NotFoundException("User not found")
        
        # Check if user is already a member
        existing_membership = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'organization.member',
                Entity.properties.op('->>')('user_id') == str(user_id),
                Entity.properties.op('->>')('organization_id') == str(organization_id),
                Entity.status == 'active'
            )
        ).first()
        
        if existing_membership:
            raise ConflictException("User is already a member of this organization")
        
        # Create membership entity
        membership_entity = Entity(
            entity_type='organization.member',
            name=f"{user.name} - {organization.name}",
            description=f"Membership of {user.name} in {organization.name}",
            status='active',
            organization_id=organization_id,
            properties={
                'user_id': str(user_id),
                'organization_id': str(organization_id),
                'role': role,
                'invited_by': str(current_user.id),
                'joined_at': datetime.utcnow().isoformat(),
                'invited_at': datetime.utcnow().isoformat(),
                'accepted_at': datetime.utcnow().isoformat()
            }
        )
        
        try:
            self.db.add(membership_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Create relationship between user and organization
            relationship = Relationship(
                from_entity=user_id,
                to_entity=organization_id,
                relationship_type='member_of',
                properties={
                    'role': role,
                    'joined_at': datetime.utcnow().isoformat(),
                    'invited_by': str(current_user.id)
                }
            )
            self.db.add(relationship)
            
            # Update organization member count
            self._update_organization_member_count(organization_id, 1)
            
            # Log membership creation event
            self._log_event(
                "entity.created",
                membership_entity.id,
                "organization.member",
                {
                    "user_id": str(user_id),
                    "organization_id": str(organization_id),
                    "role": role,
                    "invited_by": str(current_user.id)
                },
                current_user.id
            )
            
            # Commit membership, relationship, and event together
            self.db.commit()
            self.db.refresh(membership_entity)
            
            return membership_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Membership creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Membership creation failed: {str(e)}")
    
    def remove_user_from_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        current_user: User
    ) -> bool:
        """
        Remove a user from an organization using entity architecture.
        
        Args:
            user_id: User ID to remove
            organization_id: Organization ID
            current_user: Current authenticated user
            
        Returns:
            True if user removed successfully
            
        Raises:
            NotFoundException: If user or organization not found
            PermissionException: If user lacks access
        """
        # Verify organization exists and user has access
        organization = self.get_organization(organization_id, current_user)
        
        # Find membership entity
        membership = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'organization.member',
                Entity.properties.op('->>')('user_id') == str(user_id),
                Entity.properties.op('->>')('organization_id') == str(organization_id),
                Entity.status == 'active'
            )
        ).first()
        
        if not membership:
            raise NotFoundException("User is not a member of this organization")
        
        try:
            # Deactivate membership
            membership.status = 'inactive'
            membership.updated_at = datetime.utcnow()
            
            # Update properties
            properties = membership.properties.copy()
            properties['removed_at'] = datetime.utcnow().isoformat()
            properties['removed_by'] = str(current_user.id)
            membership.properties = properties
            
            # Update organization member count
            self._update_organization_member_count(organization_id, -1)
            
            # Log membership removal event
            self._log_event(
                "entity.updated",
                membership.id,
                "organization.member",
                {
                    "user_id": str(user_id),
                    "organization_id": str(organization_id),
                    "status": "inactive",
                    "removed_by": str(current_user.id)
                },
                current_user.id
            )
            
            # Commit membership update and event together
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Membership removal failed: {str(e)}")
    
    def get_organization_members(
        self,
        organization_id: UUID,
        current_user: User,
        role: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> List[Entity]:
        """
        Get all members of an organization using entity architecture.
        
        Args:
            organization_id: Organization ID
            current_user: Current authenticated user
            role: Optional role filter
            page: Page number
            per_page: Items per page
            
        Returns:
            List of membership entities
        """
        # Verify organization exists and user has access
        organization = self.get_organization(organization_id, current_user)
        
        # Build query for membership entities
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'organization.member',
                Entity.properties.op('->>')('organization_id') == str(organization_id),
                Entity.status == 'active'
            )
        )
        
        # Apply role filter
        if role:
            query = query.filter(Entity.properties.op('->>')('role') == role)
        
        # Apply pagination and ordering
        memberships = query.order_by(Entity.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return memberships
    
    def get_user_organizations(
        self,
        user_id: UUID,
        current_user: User,
        page: int = 1,
        per_page: int = 10
    ) -> List[Entity]:
        """
        Get all organizations a user belongs to using entity architecture.
        
        Args:
            user_id: User ID
            current_user: Current authenticated user
            page: Page number
            per_page: Items per page
            
        Returns:
            List of organization entities
        """
        # Build query for membership entities
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'organization.member',
                Entity.properties.op('->>')('user_id') == str(user_id),
                Entity.status == 'active'
            )
        )
        
        # Apply pagination and ordering
        memberships = query.order_by(Entity.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        # Get organization entities
        organization_ids = [UUID(membership.properties.get('organization_id')) for membership in memberships]
        organizations = []
        
        if organization_ids:
            organizations = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'organization',
                    Entity.id.in_(organization_ids),
                    Entity.status == 'active'
                )
            ).all()
        
        return organizations
    
    def get_organization_stats(self, organization_id: UUID, current_user: User) -> Dict[str, Any]:
        """
        Get statistics for a specific organization using entity architecture.
        
        Args:
            organization_id: Organization ID
            current_user: Current authenticated user
            
        Returns:
            Dictionary containing organization statistics
        """
        # Verify organization exists and user has access
        organization = self.get_organization(organization_id, current_user)
        
        try:
            # Get member count
            member_count = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'organization.member',
                    Entity.properties.op('->>')('organization_id') == str(organization_id),
                    Entity.status == 'active'
                )
            ).count()
            
            # Get active members
            active_members = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'organization.member',
                    Entity.properties.op('->>')('organization_id') == str(organization_id),
                    Entity.status == 'active'
                )
            ).count()
            
            # Placeholder statistics (would need other entity types for full stats)
            stats = {
                "member_count": member_count,
                "device_count": 0,  # Would need device entities
                "project_count": 0,  # Would need project entities
                "active_members": active_members,
                "online_devices": 0,  # Would need device status tracking
                "total_readings": 0,  # Would need reading entities
                "total_alerts": 0,    # Would need alert entities
                "active_alerts": 0,   # Would need alert entities
                "data_usage_gb": 0.0, # Would need data tracking
                "storage_usage_gb": 0.0, # Would need storage tracking
                "last_activity": organization.updated_at.isoformat() if organization.updated_at else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting organization stats: {e}")
            return {
                "member_count": 0,
                "device_count": 0,
                "project_count": 0,
                "active_members": 0,
                "online_devices": 0,
                "total_readings": 0,
                "total_alerts": 0,
                "active_alerts": 0,
                "data_usage_gb": 0.0,
                "storage_usage_gb": 0.0,
                "last_activity": None
            }
    
    # Helper methods for entity-based operations
    
    def _organization_name_exists(
        self, 
        name: str, 
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if an organization name already exists."""
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'organization',
                Entity.name == name,
                Entity.status != 'inactive'
            )
        )
        
        if exclude_id:
            query = query.filter(Entity.id != exclude_id)
        
        return query.first() is not None
    
    def _user_has_org_access(self, user: User, organization_id: UUID) -> bool:
        """Check if user has access to the organization."""
        if user.is_superuser:
            return True
        
        # Check organization_members table first (current system)
        from ..models.organization_member import OrganizationMember
        membership = self.db.query(OrganizationMember).filter(
            and_(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == True
            )
        ).first()
        
        if membership:
            return True
        
        # Fall back to legacy organization_id field for backward compatibility
        return user.organization_id == organization_id
    
    def _validate_organization_data(self, org_data: OrganizationCreate) -> None:
        """Validate organization creation data."""
        if not org_data.name:
            raise ValidationException("Organization name is required")
        
        if len(org_data.name) < 2:
            raise ValidationException("Organization name must be at least 2 characters long")
        
        if len(org_data.name) > 100:
            raise ValidationException("Organization name must be less than 100 characters")
        
        if org_data.description and len(org_data.description) > 500:
            raise ValidationException("Organization description must be less than 500 characters")
    
    def _validate_organization_schema(self, org_data: OrganizationCreate) -> None:
        """Validate organization data against schema if available."""
        try:
            # Check if schema validation function exists
            result = self.db.execute(
                text("SELECT validate_against_schema(:data, :schema_id)"),
                {
                    'data': str(org_data.dict()),
                    'schema_id': 'organization'
                }
            ).scalar()
            
            if not result:
                raise ValidationException("Organization data does not match required schema")
                
        except Exception as e:
            # If schema validation fails, log but don't block creation
            logger.warning(f"Schema validation failed: {e}")
    
    def _add_user_to_organization(self, user_id: UUID, organization_id: UUID, role: str, invited_by: UUID) -> Entity:
        """Internal method to add user to organization without permission checks."""
        # Create membership entity
        membership_entity = Entity(
            entity_type='organization.member',
            name=f"Membership {user_id} - {organization_id}",
            description=f"Membership in organization",
            status='active',
            organization_id=organization_id,
            properties={
                'user_id': str(user_id),
                'organization_id': str(organization_id),
                'role': role,
                'invited_by': str(invited_by),
                'joined_at': datetime.utcnow().isoformat(),
                'invited_at': datetime.utcnow().isoformat(),
                'accepted_at': datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(membership_entity)
        return membership_entity
    
    def _update_organization_member_count(self, organization_id: UUID, delta: int) -> None:
        """Update organization member count."""
        organization = self.db.query(Entity).filter(
            and_(
                Entity.id == organization_id,
                Entity.entity_type == 'organization'
            )
        ).first()
        
        if organization:
            properties = organization.properties.copy()
            current_count = properties.get('member_count', 0)
            properties['member_count'] = max(0, current_count + delta)
            organization.properties = properties
    
    def _log_event(self, event_type: str, entity_id: UUID, entity_type: str, data: Dict[str, Any], user_id: Optional[UUID] = None):
        """
        Log organization event.
        
        Args:
            event_type: Event type
            entity_id: Entity ID
            entity_type: Entity type
            data: Event data
            user_id: Optional user ID who triggered the event
        """
        try:
            # Include user_id in the data if provided
            event_data = data.copy()
            if user_id:
                event_data['user_id'] = str(user_id)
                
            event = Event(
                event_type=event_type,
                entity_id=entity_id,
                entity_type=entity_type,
                data=event_data,
                timestamp=datetime.utcnow()
            )
            self.db.add(event)
            # Note: No commit here - let the calling method handle the transaction
        except Exception as e:
            logger.error(f"Failed to log organization event: {str(e)}")

