"""
Process service for the LMS Core system.

This module provides business logic for process management, including
process creation, updates, execution, and monitoring.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError

from ..models.process import Process, ProcessInstance
from ..models.entity import Entity
from ..models.user import User
from ..models.event import Event
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


class ProcessService(BaseService):
    """
    Service for managing processes and process instances.
    
    Provides business logic for process creation, updates, execution,
    and monitoring with proper validation and error handling.
    """
    
    @property
    def model_class(self):
        """Return the Process model class."""
        return Process
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_processes_by_organization(self, organization_id: UUID, status: Optional[str] = None) -> List[Process]:
        """
        Get processes for a specific organization.
        
        Args:
            organization_id: Organization ID
            status: Optional status filter
            
        Returns:
            List of processes
        """
        try:
            query = self.db.query(Process).filter(
                Process.organization_id == organization_id
            )
            
            if status:
                query = query.filter(Process.status == status)
            
            processes = query.order_by(Process.created_at.desc()).all()
            return processes
            
        except Exception as e:
            logger.error(f"Error getting processes by organization: {e}")
            return []
    
    def create_process(
        self, 
        process_data: ProcessCreate, 
        current_user: User
    ) -> Process:
        """
        Create a new process.
        
        Args:
            process_data: Process creation data
            current_user: Current authenticated user
            
        Returns:
            Created process
            
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
            
            # Create process
            process = Process(
                name=process_data.name,
                version=process_data.version,
                process_type=process_data.process_type.value,
                definition=process_data.definition.dict(),
                description=process_data.description,
                organization_id=process_data.organization_id,
                created_by=current_user.id,
                is_template=process_data.is_template,
                status=ProcessStatus.ACTIVE.value
            )
            
            self.db.add(process)
            self.db.flush()  # Flush to get the ID without committing
            
            # Log creation event (added to same transaction)
            self._log_event(
                "process.created",
                process.id,
                "process",
                {"process_name": process.name, "process_type": process.process_type},
                current_user.id
            )
            
            # Commit both process and event together
            self.db.commit()
            self.db.refresh(process)
            
            return process
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Process creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process creation failed: {str(e)}")
    
    def get_process(self, process_id: UUID, current_user: User) -> Process:
        """
        Get a process by ID.
        
        Args:
            process_id: Process ID
            current_user: Current authenticated user
            
        Returns:
            Process object
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
        """
        process = self.db.query(Process).filter(Process.id == process_id).first()
        
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
        List processes with filtering and pagination.
        
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
        # Build query
        query = self.db.query(Process)
        
        # Apply organization filter
        if organization_id:
            if not self._user_has_org_access(current_user, organization_id):
                raise PermissionException("Access denied to organization")
            query = query.filter(Process.organization_id == organization_id)
        else:
            # Show processes from user's organization or public templates
            user_org_id = current_user.organization_id if current_user else None
            if user_org_id:
                query = query.filter(
                    or_(
                        Process.organization_id == user_org_id,
                        and_(Process.is_template == True, Process.status == ProcessStatus.ACTIVE.value)
                    )
                )
            else:
                # Standalone user - only show public templates
                query = query.filter(
                    and_(Process.is_template == True, Process.status == ProcessStatus.ACTIVE.value)
                )
        
        # Apply filters
        if process_type:
            query = query.filter(Process.process_type == process_type)
        
        if status:
            query = query.filter(Process.status == status.value)
        
        if is_template is not None:
            query = query.filter(Process.is_template == is_template)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Process.name.ilike(search_term),
                    Process.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        processes = query.order_by(desc(Process.updated_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to response format
        process_responses = []
        for process in processes:
            response_data = process.to_dict()
            response_data["step_count"] = process.get_step_count()
            response_data["estimated_duration"] = process.get_estimated_duration()
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
    ) -> Process:
        """
        Update a process.
        
        Args:
            process_id: Process ID
            process_data: Process update data
            current_user: Current authenticated user
            
        Returns:
            Updated process
            
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
        
        # Update fields
        update_data = process_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "definition" and value:
                setattr(process, field, value.dict())
            elif field == "process_type" and value:
                setattr(process, field, value.value)
            elif field == "status" and value:
                setattr(process, field, value.value)
            else:
                setattr(process, field, value)
        
        process.updated_at = datetime.utcnow()
        
        try:
            # Log update event (added to same transaction)
            self._log_event(
                "process.updated",
                process.id,
                "process",
                {"process_name": process.name, "updated_fields": list(update_data.keys())},
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
    
    def archive_process(self, process_id: UUID, current_user: User) -> Process:
        """
        Archive a process (soft delete).
        
        Args:
            process_id: Process ID
            current_user: Current authenticated user
            
        Returns:
            Archived process
            
        Raises:
            NotFoundException: If process not found
            PermissionException: If user lacks access
        """
        process = self.get_process(process_id, current_user)
        
        # Check if process has running instances
        running_instances = self.db.query(ProcessInstance).filter(
            and_(
                ProcessInstance.process_id == process_id,
                ProcessInstance.status == ProcessInstanceStatus.RUNNING.value
            )
        ).count()
        
        if running_instances > 0:
            raise BusinessLogicException("Cannot archive process with running instances")
        
        process.status = ProcessStatus.ARCHIVED.value
        process.updated_at = datetime.utcnow()
        
        try:
            # Log archive event (added to same transaction)
            self._log_event(
                "process.archived",
                process.id,
                "process",
                {"process_name": process.name},
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
    ) -> ProcessInstance:
        """
        Create a new process instance.
        
        Args:
            instance_data: Process instance creation data
            current_user: Current authenticated user
            
        Returns:
            Created process instance
            
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
        
        # Create process instance
        instance = ProcessInstance(
            process_id=instance_data.process_id,
            batch_id=instance_data.batch_id,
            parameters=instance_data.parameters,
            status=ProcessInstanceStatus.RUNNING.value,
            created_by=current_user.id
        )
        
        try:
            self.db.add(instance)
            self.db.flush()  # Flush to get the ID without committing
            
            # Log instance creation event (added to same transaction)
            self._log_event(
                "process_instance.created",
                instance.id,
                "process_instance",
                {
                    "process_id": str(instance.process_id),
                    "batch_id": instance.batch_id,
                    "status": instance.status
                },
                current_user.id
            )
            
            # Commit both instance and event together
            self.db.commit()
            self.db.refresh(instance)
            
            return instance
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Process instance creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Process instance creation failed: {str(e)}")
    
    def get_process_instance(self, instance_id: UUID, current_user: User) -> ProcessInstance:
        """
        Get a process instance by ID.
        
        Args:
            instance_id: Process instance ID
            current_user: Current authenticated user
            
        Returns:
            Process instance object
            
        Raises:
            NotFoundException: If instance not found
            PermissionException: If user lacks access
        """
        instance = self.db.query(ProcessInstance).filter(ProcessInstance.id == instance_id).first()
        
        if not instance:
            raise NotFoundException("Process instance not found")
        
        # Check access through the associated process
        process = self.get_process(instance.process_id, current_user)
        
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
        List process instances with filtering and pagination.
        
        Args:
            current_user: Current authenticated user
            process_id: Filter by process ID
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of process instances
        """
        # Build query
        query = self.db.query(ProcessInstance).join(Process)
        
        # Apply organization filter based on process
        user_org_id = current_user.organization_id if current_user else None
        if user_org_id:
            query = query.filter(Process.organization_id == user_org_id)
        else:
            # Standalone user - no instances to show
            return ProcessInstanceListResponse(instances=[], total=0, page=page, per_page=per_page)
        
        # Apply filters
        if process_id:
            query = query.filter(ProcessInstance.process_id == process_id)
        
        if status:
            query = query.filter(ProcessInstance.status == status.value)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        instances = query.order_by(desc(ProcessInstance.started_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to response format
        instance_responses = []
        for instance in instances:
            response_data = instance.to_dict()
            response_data["duration"] = instance.get_duration()
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
    ) -> ProcessInstance:
        """
        Update a process instance.
        
        Args:
            instance_id: Process instance ID
            instance_data: Process instance update data
            current_user: Current authenticated user
            
        Returns:
            Updated process instance
            
        Raises:
            NotFoundException: If instance not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        instance = self.get_process_instance(instance_id, current_user)
        
        # Update fields
        update_data = instance_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                setattr(instance, field, value.value)
            else:
                setattr(instance, field, value)
        
        # Handle status transitions
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == ProcessInstanceStatus.COMPLETED:
                instance.complete(update_data.get("results"))
            elif new_status == ProcessInstanceStatus.FAILED:
                instance.fail(update_data.get("error_message", "Unknown error"))
            elif new_status == ProcessInstanceStatus.PAUSED:
                instance.pause()
            elif new_status == ProcessInstanceStatus.RUNNING:
                instance.resume()
        
        try:
            # Log update event (added to same transaction)
            self._log_event(
                "process_instance.updated",
                instance.id,
                "process_instance",
                {
                    "process_id": str(instance.process_id),
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
    
    def _process_name_exists(
        self, 
        name: str, 
        organization_id: Optional[UUID], 
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if a process name already exists in the organization."""
        query = self.db.query(Process).filter(
            and_(
                Process.name == name,
                Process.organization_id == organization_id,
                Process.status != ProcessStatus.ARCHIVED.value
            )
        )
        
        if exclude_id:
            query = query.filter(Process.id != exclude_id)
        
        return query.first() is not None
    
    def _user_has_org_access(self, user: User, organization_id: UUID) -> bool:
        """Check if user has access to the organization."""
        if user.is_superuser:
            return True
        
        return user.organization_id == organization_id
    
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
            self.logger.error(f"Failed to log process event: {str(e)}") 