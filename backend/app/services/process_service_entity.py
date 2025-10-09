"""
Process service for the VerdoyLab system - Entity-based implementation.

This module provides business logic for process management using the pure entity architecture,
including process creation, updates, execution, and monitoring.
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
from ..schemas.process import (
    ProcessCreate, ProcessUpdate, ProcessResponse, ProcessListResponse,
    ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceResponse, ProcessInstanceListResponse,
    ProcessStatus, ProcessInstanceStatus
)
from ..exceptions import (
    ValidationException, NotFoundException, PermissionException,
    ConflictException, BusinessLogicException
)
from .base import BaseService
import logging

logger = logging.getLogger(__name__)


class ProcessServiceEntity(BaseService):
    """
    Entity-based service for managing processes and process instances.
    
    This service works with the pure entity architecture, storing all process
    data in the entities table with entity_type = 'process.definition' and
    entity_type = 'process.instance'.
    """
    
    @property
    def model_class(self):
        """Return the Entity model class."""
        return Entity
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_processes_by_organization(self, organization_id: UUID, status: Optional[str] = None) -> List[Entity]:
        """
        Get processes for a specific organization.
        
        Args:
            organization_id: Organization ID
            status: Optional status filter
            
        Returns:
            List of process entities
        """
        try:
            query = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'process.definition',
                    Entity.organization_id == organization_id
                )
            )
            
            if status:
                query = query.filter(Entity.status == status)
            
            processes = query.order_by(Entity.created_at.desc()).all()
            return processes
            
        except Exception as e:
            logger.error(f"Error getting processes by organization: {e}")
            return []
    
    def create_process(
        self, 
        process_data: ProcessCreate, 
        current_user: User
    ) -> Entity:
        """
        Create a new process using entity architecture.
        
        Args:
            process_data: Process creation data
            current_user: Current authenticated user
            
        Returns:
            Created process entity
            
        Raises:
            ValidationException: If process data is invalid
            PermissionException: If user lacks permission
            ConflictException: If process name already exists
        """
        try:
            # Validate organization access if specified
            if process_data.organization_id:
                if not self._user_has_org_access(current_user, process_data.organization_id):
                    raise PermissionException("Access denied to organization")
            
            # Check for duplicate process name in organization
            if self._process_name_exists(process_data.name, process_data.organization_id):
                raise ConflictException(f"Process with name '{process_data.name}' already exists")
            
            # Validate against schema if available
            self._validate_process_schema(process_data)
            
            # Create process entity
            process_entity = Entity(
                entity_type='process.definition',
                name=process_data.name,
                description=process_data.description,
                status=ProcessStatus.ACTIVE.value,
                organization_id=process_data.organization_id,
                properties={
                    'version': process_data.version,
                    'process_type': process_data.process_type.value,
                    'definition': process_data.definition.dict(),
                    'is_template': process_data.is_template,
                    'created_by': str(current_user.id)
                }
            )
            
            self.db.add(process_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Log creation event
            self._log_event(
                "entity.created",
                process_entity.id,
                "process.definition",
                {
                    "process_name": process_entity.name,
                    "process_type": process_data.process_type.value,
                    "version": process_data.version
                },
                current_user.id
            )
            
            # Commit both process and event together
            self.db.commit()
            self.db.refresh(process_entity)
            
            return process_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Process creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process creation failed: {str(e)}")
    
    def get_process(self, process_id: UUID, current_user: User) -> Entity:
        """
        Get a process by ID using entity architecture.
        
        Args:
            process_id: Process ID
            current_user: Current authenticated user
            
        Returns:
            Process entity object
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
        """
        process = self.db.query(Entity).filter(
            and_(
                Entity.id == process_id,
                Entity.entity_type == 'process.definition'
            )
        ).first()
        
        if not process:
            raise NotFoundException("Process not found")
        
        # Check organization access
        if process.organization_id and not self._user_has_org_access(current_user, process.organization_id):
            raise PermissionException("Access denied to process")
        
        return process
    
    def list_processes(
        self,
        current_user: User,
        organization_id: Optional[UUID] = None,
        process_type: Optional[str] = None,
        status: Optional[ProcessStatus] = None,
        is_template: Optional[bool] = None,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None
    ) -> ProcessListResponse:
        """
        List processes with filtering and pagination using entity architecture.
        
        Args:
            current_user: Current authenticated user
            organization_id: Filter by organization
            process_type: Filter by process type
            status: Filter by status
            is_template: Filter by template status
            page: Page number
            per_page: Items per page
            search: Search term for name/description
            
        Returns:
            Paginated list of processes
        """
        # Build query for process entities
        query = self.db.query(Entity).filter(Entity.entity_type == 'process.definition')
        
        # Apply organization filter
        if organization_id:
            if not self._user_has_org_access(current_user, organization_id):
                raise PermissionException("Access denied to organization")
            query = query.filter(Entity.organization_id == organization_id)
        else:
            # Show processes from user's organization or public templates
            user_org_id = current_user.organization_id if current_user else None
            if user_org_id:
                query = query.filter(
                    or_(
                        Entity.organization_id == user_org_id,
                        and_(
                            Entity.properties.op('->>')('is_template') == 'true',
                            Entity.status == ProcessStatus.ACTIVE.value
                        )
                    )
                )
            else:
                # Standalone user - only show public templates
                query = query.filter(
                    and_(
                        Entity.properties.op('->>')('is_template') == 'true',
                        Entity.status == ProcessStatus.ACTIVE.value
                    )
                )
        
        # Apply filters using JSONB properties
        if process_type:
            query = query.filter(Entity.properties.op('->>')('process_type') == process_type)
        
        if status:
            query = query.filter(Entity.status == status.value)
        
        if is_template is not None:
            query = query.filter(Entity.properties.op('->>')('is_template') == str(is_template).lower())
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Entity.name.ilike(search_term),
                    Entity.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        processes = query.order_by(desc(Entity.updated_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to response format
        process_responses = []
        for process in processes:
            response_data = self._entity_to_process_dict(process)
            response_data["step_count"] = self._get_step_count(process)
            response_data["estimated_duration"] = self._get_estimated_duration(process)
            process_responses.append(ProcessResponse(**response_data))
        
        return ProcessListResponse(
            processes=process_responses,
            total=total,
            page=page,
            per_page=per_page
        )
    
    def update_process(
        self,
        process_id: UUID,
        process_data: ProcessUpdate,
        current_user: User
    ) -> Entity:
        """
        Update a process using entity architecture.
        
        Args:
            process_id: Process ID
            process_data: Process update data
            current_user: Current authenticated user
            
        Returns:
            Updated process entity
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        process = self.get_process(process_id, current_user)
        
        # Check if name is being changed and if it conflicts
        if process_data.name and process_data.name != process.name:
            if self._process_name_exists(process_data.name, process.organization_id, exclude_id=process_id):
                raise ConflictException(f"Process with name '{process_data.name}' already exists")
        
        # Update entity fields
        update_data = process_data.dict(exclude_unset=True)
        
        # Update basic entity fields
        if 'name' in update_data:
            process.name = update_data['name']
        if 'description' in update_data:
            process.description = update_data['description']
        if 'status' in update_data:
            process.status = update_data['status'].value
        
        # Update properties
        properties = process.properties.copy()
        if 'version' in update_data:
            properties['version'] = update_data['version']
        if 'process_type' in update_data:
            properties['process_type'] = update_data['process_type'].value
        if 'definition' in update_data:
            properties['definition'] = update_data['definition'].dict()
        if 'is_template' in update_data:
            properties['is_template'] = update_data['is_template']
        
        process.properties = properties
        process.updated_at = datetime.utcnow()
        
        try:
            # Log update event
            self._log_event(
                "entity.updated",
                process.id,
                "process.definition",
                {
                    "process_name": process.name,
                    "updated_fields": list(update_data.keys())
                },
                current_user.id
            )
            
            # Commit both process update and event together
            self.db.commit()
            self.db.refresh(process)
            
            return process
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Process update failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process update failed: {str(e)}")
    
    def archive_process(self, process_id: UUID, current_user: User) -> Entity:
        """
        Archive a process (soft delete) using entity architecture.
        
        Args:
            process_id: Process ID
            current_user: Current authenticated user
            
        Returns:
            Archived process entity
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
        """
        process = self.get_process(process_id, current_user)
        
        # Check if process has running instances
        running_instances = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'process.instance',
                Entity.properties.op('->>')('process_id') == str(process_id),
                Entity.status == ProcessInstanceStatus.RUNNING.value
            )
        ).count()
        
        if running_instances > 0:
            raise BusinessLogicException("Cannot archive process with running instances")
        
        process.status = ProcessStatus.ARCHIVED.value
        process.updated_at = datetime.utcnow()
        
        try:
            # Log archive event
            self._log_event(
                "entity.updated",
                process.id,
                "process.definition",
                {
                    "process_name": process.name,
                    "status": "archived"
                },
                current_user.id
            )
            
            # Commit both process archive and event together
            self.db.commit()
            self.db.refresh(process)
            
            return process
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process archive failed: {str(e)}")
    
    def create_process_instance(
        self,
        instance_data: ProcessInstanceCreate,
        current_user: User
    ) -> Entity:
        """
        Create a new process instance using entity architecture.
        
        Args:
            instance_data: Process instance creation data
            current_user: Current authenticated user
            
        Returns:
            Created process instance entity
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
            ValidationException: If instance data is invalid
        """
        # Get the process
        process = self.get_process(instance_data.process_id, current_user)
        
        # Validate process is active
        if process.status != ProcessStatus.ACTIVE.value:
            raise ValidationException("Cannot create instance from inactive process")
        
        # Create process instance entity
        instance_entity = Entity(
            entity_type='process.instance',
            name=instance_data.batch_id or f"Instance {uuid4()}",
            description=f"Process instance for {process.name}",
            status=ProcessInstanceStatus.RUNNING.value,
            organization_id=process.organization_id,
            properties={
                'process_id': str(instance_data.process_id),
                'batch_id': instance_data.batch_id,
                'started_at': datetime.utcnow().isoformat(),
                'parameters': instance_data.parameters or {},
                'results': {},
                'created_by': str(current_user.id)
            }
        )
        
        try:
            self.db.add(instance_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Create relationship between instance and process
            relationship = Relationship(
                from_entity=instance_entity.id,
                to_entity=instance_data.process_id,
                relationship_type='instance_of',
                properties={
                    'batch_id': instance_data.batch_id,
                    'created_by': str(current_user.id)
                }
            )
            self.db.add(relationship)
            
            # Log instance creation event
            self._log_event(
                "entity.created",
                instance_entity.id,
                "process.instance",
                {
                    "process_id": str(instance_data.process_id),
                    "batch_id": instance_data.batch_id,
                    "status": ProcessInstanceStatus.RUNNING.value
                },
                current_user.id
            )
            
            # Commit instance, relationship, and event together
            self.db.commit()
            self.db.refresh(instance_entity)
            
            return instance_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Process instance creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process instance creation failed: {str(e)}")
    
    def get_process_instance(self, instance_id: UUID, current_user: User) -> Entity:
        """
        Get a process instance by ID using entity architecture.
        
        Args:
            instance_id: Process instance ID
            current_user: Current authenticated user
            
        Returns:
            Process instance entity object
            
        Raises:
            NotFoundException: If instance not found
            PermissionException: If user lacks access
        """
        instance = self.db.query(Entity).filter(
            and_(
                Entity.id == instance_id,
                Entity.entity_type == 'process.instance'
            )
        ).first()
        
        if not instance:
            raise NotFoundException("Process instance not found")
        
        # Check access through the associated process
        process_id = UUID(instance.properties.get('process_id'))
        process = self.get_process(process_id, current_user)
        
        return instance
    
    def list_process_instances(
        self,
        current_user: User,
        process_id: Optional[UUID] = None,
        status: Optional[ProcessInstanceStatus] = None,
        page: int = 1,
        per_page: int = 10
    ) -> ProcessInstanceListResponse:
        """
        List process instances with filtering and pagination using entity architecture.
        
        Args:
            current_user: Current authenticated user
            process_id: Filter by process ID
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of process instances
        """
        # Build query for process instance entities
        query = self.db.query(Entity).filter(Entity.entity_type == 'process.instance')
        
        # Apply organization filter based on user's access
        user_org_id = current_user.organization_id if current_user else None
        if user_org_id:
            query = query.filter(Entity.organization_id == user_org_id)
        else:
            # Standalone user - no instances to show
            return ProcessInstanceListResponse(instances=[], total=0, page=page, per_page=per_page)
        
        # Apply filters
        if process_id:
            query = query.filter(Entity.properties.op('->>')('process_id') == str(process_id))
        
        if status:
            query = query.filter(Entity.status == status.value)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        instances = query.order_by(desc(Entity.created_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to response format
        instance_responses = []
        for instance in instances:
            response_data = self._entity_to_process_instance_dict(instance)
            response_data["duration"] = self._get_duration(instance)
            instance_responses.append(ProcessInstanceResponse(**response_data))
        
        return ProcessInstanceListResponse(
            instances=instance_responses,
            total=total,
            page=page,
            per_page=per_page
        )
    
    def update_process_instance(
        self,
        instance_id: UUID,
        instance_data: ProcessInstanceUpdate,
        current_user: User
    ) -> Entity:
        """
        Update a process instance using entity architecture.
        
        Args:
            instance_id: Process instance ID
            instance_data: Process instance update data
            current_user: Current authenticated user
            
        Returns:
            Updated process instance entity
            
        Raises:
            NotFoundException: If instance not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        instance = self.get_process_instance(instance_id, current_user)
        
        # Update fields
        update_data = instance_data.dict(exclude_unset=True)
        
        # Update basic entity fields
        if 'status' in update_data:
            instance.status = update_data['status'].value
        
        # Update properties
        properties = instance.properties.copy()
        if 'parameters' in update_data:
            properties['parameters'] = update_data['parameters']
        if 'results' in update_data:
            properties['results'] = update_data['results']
        if 'error_message' in update_data:
            properties['error_message'] = update_data['error_message']
        
        # Handle status transitions
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == ProcessInstanceStatus.COMPLETED:
                properties['completed_at'] = datetime.utcnow().isoformat()
                if 'results' in update_data:
                    properties['results'] = update_data['results']
            elif new_status == ProcessInstanceStatus.FAILED:
                properties['completed_at'] = datetime.utcnow().isoformat()
                if 'error_message' in update_data:
                    properties['error_message'] = update_data['error_message']
            elif new_status == ProcessInstanceStatus.PAUSED:
                # Pause the process instance
                properties['paused_at'] = datetime.utcnow().isoformat()
            elif new_status == ProcessInstanceStatus.RUNNING:
                # Resume the process instance
                if 'paused_at' in properties:
                    del properties['paused_at']
        
        instance.properties = properties
        instance.updated_at = datetime.utcnow()
        
        try:
            # Log update event
            self._log_event(
                "entity.updated",
                instance.id,
                "process.instance",
                {
                    "process_id": instance.properties.get('process_id'),
                    "status": instance.status,
                    "updated_fields": list(update_data.keys())
                },
                current_user.id
            )
            
            # Commit both instance update and event together
            self.db.commit()
            self.db.refresh(instance)
            
            return instance
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process instance update failed: {str(e)}")
    
    def batch_update_process_instances(
        self,
        instance_ids: List[UUID],
        update_data: ProcessInstanceUpdate,
        current_user: User
    ) -> List[Entity]:
        """
        Update multiple process instances in batch using entity architecture.
        
        Args:
            instance_ids: List of process instance IDs to update
            update_data: Process instance update data
            current_user: Current authenticated user
            
        Returns:
            List of updated process instance entities
            
        Raises:
            ValidationException: If update data is invalid
            PermissionException: If user lacks access to any instance
        """
        updated_instances = []
        
        try:
            for instance_id in instance_ids:
                instance = self.update_process_instance(instance_id, update_data, current_user)
                updated_instances.append(instance)
            
            return updated_instances
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Batch process instance update failed: {str(e)}")
    
    def batch_update_instance_status(
        self,
        instance_ids: List[UUID],
        new_status: ProcessInstanceStatus,
        current_user: User,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[Entity]:
        """
        Update status for multiple process instances in batch.
        
        Args:
            instance_ids: List of process instance IDs to update
            new_status: New status to set
            current_user: Current authenticated user
            additional_data: Optional additional data (results, error_message, etc.)
            
        Returns:
            List of updated process instance entities
        """
        update_data = ProcessInstanceUpdate(status=new_status)
        
        if additional_data:
            if 'results' in additional_data:
                update_data.results = additional_data['results']
            if 'error_message' in additional_data:
                update_data.error_message = additional_data['error_message']
            if 'parameters' in additional_data:
                update_data.parameters = additional_data['parameters']
        
        return self.batch_update_process_instances(instance_ids, update_data, current_user)
    
    # Helper methods for entity-based operations
    
    def _process_name_exists(
        self, 
        name: str, 
        organization_id: Optional[UUID], 
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if a process name already exists in the organization."""
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'process.definition',
                Entity.name == name,
                Entity.organization_id == organization_id,
                Entity.status != ProcessStatus.ARCHIVED.value
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
    
    def _validate_process_schema(self, process_data: ProcessCreate) -> None:
        """Validate process data against schema if available."""
        try:
            # Check if schema validation function exists
            result = self.db.execute(
                text("SELECT validate_against_schema(:data, :schema_id)"),
                {
                    'data': str(process_data.definition.dict()),
                    'schema_id': 'process.definition'
                }
            ).scalar()
            
            if not result:
                raise ValidationException("Process definition does not match required schema")
                
        except Exception as e:
            # If schema validation fails, log but don't block creation
            logger.warning(f"Schema validation failed: {e}")
    
    def _entity_to_process_dict(self, entity: Entity) -> Dict[str, Any]:
        """Convert process entity to dictionary representation."""
        return {
            "id": str(entity.id),
            "name": entity.name,
            "version": entity.properties.get('version'),
            "process_type": entity.properties.get('process_type'),
            "definition": entity.properties.get('definition'),
            "status": entity.status,
            "organization_id": str(entity.organization_id) if entity.organization_id else None,
            "created_by": entity.properties.get('created_by'),
            "description": entity.description,
            "is_template": entity.properties.get('is_template', False),
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }
    
    def _entity_to_process_instance_dict(self, entity: Entity) -> Dict[str, Any]:
        """Convert process instance entity to dictionary representation."""
        return {
            "id": str(entity.id),
            "process_id": entity.properties.get('process_id'),
            "batch_id": entity.properties.get('batch_id'),
            "status": entity.status,
            "started_at": entity.properties.get('started_at'),
            "completed_at": entity.properties.get('completed_at'),
            "parameters": entity.properties.get('parameters', {}),
            "results": entity.properties.get('results', {}),
            "error_message": entity.properties.get('error_message'),
            "created_by": entity.properties.get('created_by')
        }
    
    def _get_step_count(self, process_entity: Entity) -> int:
        """Get the number of steps in this process."""
        definition = process_entity.properties.get('definition', {})
        steps = definition.get("steps", [])
        return len(steps)
    
    def _get_estimated_duration(self, process_entity: Entity) -> Optional[int]:
        """Get estimated duration in minutes."""
        definition = process_entity.properties.get('definition', {})
        return definition.get("estimated_duration")
    
    def _get_duration(self, instance_entity: Entity) -> Optional[int]:
        """Get execution duration in minutes."""
        started_at = instance_entity.properties.get('started_at')
        completed_at = instance_entity.properties.get('completed_at')
        
        if started_at and completed_at:
            start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            duration = end - start
            return int(duration.total_seconds() / 60)
        return None
    
    def _log_event(self, event_type: str, entity_id: UUID, entity_type: str, data: Dict[str, Any], user_id: Optional[UUID] = None):
        """
        Log process event.
        
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
            logger.error(f"Failed to log process event: {str(e)}")
