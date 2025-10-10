"""
Experiment service for the VerdoyLab system - Entity-based implementation.

This module provides business logic for experiment management using the pure entity architecture,
including experiment creation, updates, execution, and trial management.
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
from ..schemas.experiment import (
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    ExperimentTrialCreate, ExperimentTrialUpdate, ExperimentTrialResponse,
    ExperimentListResponse, ExperimentStatsResponse, ExperimentControlRequest,
    ExperimentControlResponse, ExperimentFilterRequest
)
from ..exceptions import (
    ValidationException, NotFoundException, PermissionException,
    ConflictException, BusinessLogicException
)
from .base import BaseService
import logging

logger = logging.getLogger(__name__)


class ExperimentServiceEntity(BaseService):
    """
    Entity-based service for managing experiments and experiment trials.
    
    This service works with the pure entity architecture, storing all experiment
    data in the entities table with entity_type = 'experiment' and
    entity_type = 'experiment.trial'.
    """
    
    @property
    def model_class(self):
        """Return the Entity model class."""
        return Entity
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create_experiment(
        self, 
        experiment_data: ExperimentCreate, 
        current_user: User
    ) -> Entity:
        """
        Create a new experiment using entity architecture.
        
        Args:
            experiment_data: Experiment creation data
            current_user: Current authenticated user
            
        Returns:
            Created experiment entity
            
        Raises:
            ValidationException: If experiment data is invalid
            PermissionException: If user lacks permission
            ConflictException: If experiment name already exists
        """
        try:
            # Validate organization access if specified
            if experiment_data.organization_id:
                if not self._user_has_org_access(current_user, experiment_data.organization_id):
                    raise PermissionException("Access denied to organization")
            
            # Check for duplicate experiment name in organization
            if self._experiment_name_exists(experiment_data.name, experiment_data.organization_id):
                raise ConflictException(f"Experiment with name '{experiment_data.name}' already exists")
            
            # Validate against schema if available
            self._validate_experiment_schema(experiment_data)
            
            # Create experiment entity
            experiment_entity = Entity(
                entity_type='experiment',
                name=experiment_data.name,
                description=experiment_data.description,
                status='draft',
                organization_id=experiment_data.organization_id,
                properties={
                    'project_id': str(experiment_data.project_id),
                    'process_id': str(experiment_data.process_id),
                    'bioreactor_id': str(experiment_data.bioreactor_id),
                    'parameters': experiment_data.parameters or {},
                    'metadata': experiment_data.metadata or {},
                    'total_trials': experiment_data.total_trials,
                    'current_trial': 1,
                    'started_at': None,
                    'completed_at': None,
                    'results': {},
                    'error_message': None,
                    'created_by': str(current_user.id)
                }
            )
            
            self.db.add(experiment_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Log creation event
            self._log_event(
                "entity.created",
                experiment_entity.id,
                "experiment",
                {
                    "experiment_name": experiment_entity.name,
                    "project_id": str(experiment_data.project_id),
                    "process_id": str(experiment_data.process_id),
                    "bioreactor_id": str(experiment_data.bioreactor_id)
                },
                current_user.id
            )
            
            # Commit both experiment and event together
            self.db.commit()
            self.db.refresh(experiment_entity)
            
            return experiment_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Experiment creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Experiment creation failed: {str(e)}")
    
    def get_experiment(self, experiment_id: UUID, current_user: User) -> Entity:
        """
        Get an experiment by ID using entity architecture.
        
        Args:
            experiment_id: Experiment ID
            current_user: Current authenticated user
            
        Returns:
            Experiment entity object
            
        Raises:
            NotFoundException: If experiment not found
            PermissionException: If user lacks access
        """
        experiment = self.db.query(Entity).filter(
            and_(
                Entity.id == experiment_id,
                Entity.entity_type == 'experiment'
            )
        ).first()
        
        if not experiment:
            raise NotFoundException("Experiment not found")
        
        # Check organization access
        if experiment.organization_id and not self._user_has_org_access(current_user, experiment.organization_id):
            raise PermissionException("Access denied to experiment")
        
        return experiment
    
    def list_experiments(
        self,
        current_user: User,
        organization_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        process_id: Optional[UUID] = None,
        bioreactor_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None
    ) -> ExperimentListResponse:
        """
        List experiments with filtering and pagination using entity architecture.
        
        Args:
            current_user: Current authenticated user
            organization_id: Filter by organization
            project_id: Filter by project
            process_id: Filter by process
            bioreactor_id: Filter by bioreactor
            status: Filter by status
            page: Page number
            per_page: Items per page
            search: Search term for name/description
            
        Returns:
            Paginated list of experiments
        """
        # Build query for experiment entities
        query = self.db.query(Entity).filter(Entity.entity_type == 'experiment')
        
        # Apply organization filter
        if organization_id:
            if not self._user_has_org_access(current_user, organization_id):
                raise PermissionException("Access denied to organization")
            query = query.filter(Entity.organization_id == organization_id)
        else:
            # Show experiments from user's organization
            user_org_id = current_user.organization_id if current_user else None
            if user_org_id:
                query = query.filter(Entity.organization_id == user_org_id)
            else:
                # Standalone user - no experiments to show
                return ExperimentListResponse(experiments=[], total=0, page=page, per_page=per_page)
        
        # Apply filters using JSONB properties
        if project_id:
            query = query.filter(Entity.properties.op('->>')('project_id') == str(project_id))
        
        if process_id:
            query = query.filter(Entity.properties.op('->>')('process_id') == str(process_id))
        
        if bioreactor_id:
            query = query.filter(Entity.properties.op('->>')('bioreactor_id') == str(bioreactor_id))
        
        if status:
            query = query.filter(Entity.properties.op('->>')('status') == status)
        
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
        experiments = query.order_by(desc(Entity.updated_at)).offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to response format
        experiment_responses = []
        for experiment in experiments:
            response_data = self._entity_to_experiment_dict(experiment)
            experiment_responses.append(ExperimentResponse(**response_data))
        
        return ExperimentListResponse(
            experiments=experiment_responses,
            total=total,
            page=page,
            per_page=per_page
        )
    
    def update_experiment(
        self,
        experiment_id: UUID,
        experiment_data: ExperimentUpdate,
        current_user: User
    ) -> Entity:
        """
        Update an experiment using entity architecture.
        
        Args:
            experiment_id: Experiment ID
            experiment_data: Experiment update data
            current_user: Current authenticated user
            
        Returns:
            Updated experiment entity
            
        Raises:
            NotFoundException: If experiment not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        experiment = self.get_experiment(experiment_id, current_user)
        
        # Check if experiment is running
        if self._is_experiment_running(experiment):
            raise ValidationException("Cannot update experiment while it is running")
        
        # Check if name is being changed and if it conflicts
        if experiment_data.name and experiment_data.name != experiment.name:
            if self._experiment_name_exists(experiment_data.name, experiment.organization_id, exclude_id=experiment_id):
                raise ConflictException(f"Experiment with name '{experiment_data.name}' already exists")
        
        # Update entity fields
        update_data = experiment_data.dict(exclude_unset=True)
        
        # Update basic entity fields
        if 'name' in update_data:
            experiment.name = update_data['name']
        if 'description' in update_data:
            experiment.description = update_data['description']
        
        # Update properties
        properties = experiment.properties.copy()
        if 'parameters' in update_data:
            properties['parameters'] = update_data['parameters']
        if 'metadata' in update_data:
            properties['metadata'] = update_data['metadata']
        if 'total_trials' in update_data:
            properties['total_trials'] = update_data['total_trials']
        
        experiment.properties = properties
        experiment.updated_at = datetime.utcnow()
        
        try:
            # Log update event
            self._log_event(
                "entity.updated",
                experiment.id,
                "experiment",
                {
                    "experiment_name": experiment.name,
                    "updated_fields": list(update_data.keys())
                },
                current_user.id
            )
            
            # Commit both experiment update and event together
            self.db.commit()
            self.db.refresh(experiment)
            
            return experiment
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Experiment update failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Experiment update failed: {str(e)}")
    
    def control_experiment(
        self,
        experiment_id: UUID,
        control_data: ExperimentControlRequest,
        current_user: User
    ) -> ExperimentControlResponse:
        """
        Control an experiment (start, pause, resume, stop, complete, fail) using entity architecture.
        
        Args:
            experiment_id: Experiment ID
            control_data: Control action data
            current_user: Current authenticated user
            
        Returns:
            Control response
            
        Raises:
            NotFoundException: If experiment not found
            PermissionException: If user lacks access
            ValidationException: If action is invalid
        """
        experiment = self.get_experiment(experiment_id, current_user)
        
        action = control_data.action
        message = ""
        
        # Update properties
        properties = experiment.properties.copy()
        
        if action == 'start':
            if not self._can_start_experiment(experiment):
                raise ValidationException("Experiment cannot be started. Check that project, process, and bioreactor are set.")
            
            properties['status'] = 'active'
            properties['started_at'] = datetime.utcnow().isoformat()
            properties['error_message'] = None
            message = "Experiment started successfully"
            
        elif action == 'pause':
            if not self._can_pause_experiment(experiment):
                raise ValidationException("Experiment cannot be paused")
            
            properties['status'] = 'paused'
            message = "Experiment paused successfully"
            
        elif action == 'resume':
            if not self._can_resume_experiment(experiment):
                raise ValidationException("Experiment cannot be resumed")
            
            properties['status'] = 'active'
            message = "Experiment resumed successfully"
            
        elif action == 'stop':
            if not self._can_stop_experiment(experiment):
                raise ValidationException("Experiment cannot be stopped")
            
            properties['status'] = 'failed'
            properties['completed_at'] = datetime.utcnow().isoformat()
            properties['error_message'] = "Experiment stopped by user"
            message = "Experiment stopped successfully"
            
        elif action == 'complete':
            if not self._is_experiment_running(experiment):
                raise ValidationException("Experiment is not running")
            
            properties['status'] = 'completed'
            properties['completed_at'] = datetime.utcnow().isoformat()
            if control_data.results:
                properties['results'] = control_data.results
            message = "Experiment completed successfully"
            
        elif action == 'fail':
            if not self._is_experiment_running(experiment):
                raise ValidationException("Experiment is not running")
            
            properties['status'] = 'failed'
            properties['completed_at'] = datetime.utcnow().isoformat()
            properties['error_message'] = control_data.error_message or "Experiment failed"
            message = "Experiment marked as failed"
        
        else:
            raise ValidationException(f"Invalid action: {action}")
        
        experiment.properties = properties
        experiment.updated_at = datetime.utcnow()
        
        try:
            # Log control event
            self._log_event(
                "entity.updated",
                experiment.id,
                "experiment",
                {
                    "experiment_name": experiment.name,
                    "action": action,
                    "status": properties['status']
                },
                current_user.id
            )
            
            # Commit both experiment update and event together
            self.db.commit()
            self.db.refresh(experiment)
            
            # Convert to response format
            response_data = self._entity_to_experiment_dict(experiment)
            experiment_response = ExperimentResponse(**response_data)
            
            return ExperimentControlResponse(
                success=True,
                message=message,
                experiment=experiment_response
            )
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Experiment control failed: {str(e)}")
    
    def create_trial(
        self,
        experiment_id: UUID,
        trial_data: ExperimentTrialCreate,
        current_user: User
    ) -> Entity:
        """
        Create a new trial for an experiment using entity architecture.
        
        Args:
            experiment_id: Experiment ID
            trial_data: Trial creation data
            current_user: Current authenticated user
            
        Returns:
            Created trial entity
            
        Raises:
            NotFoundException: If experiment not found
            PermissionException: If user lacks access
            ConflictException: If trial number already exists
        """
        # Get the experiment
        experiment = self.get_experiment(experiment_id, current_user)
        
        # Check if trial number already exists
        existing_trial = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'experiment.trial',
                Entity.properties.op('->>')('experiment_id') == str(experiment_id),
                Entity.properties.op('->>')('trial_number') == str(trial_data.trial_number)
            )
        ).first()
        
        if existing_trial:
            raise ConflictException(f"Trial number {trial_data.trial_number} already exists for this experiment")
        
        # Create trial entity
        trial_entity = Entity(
            entity_type='experiment.trial',
            name=f"Trial {trial_data.trial_number}",
            description=f"Trial {trial_data.trial_number} for {experiment.name}",
            status='pending',
            organization_id=experiment.organization_id,
            properties={
                'experiment_id': str(experiment_id),
                'trial_number': trial_data.trial_number,
                'status': 'pending',
                'started_at': None,
                'completed_at': None,
                'parameters': trial_data.parameters or {},
                'results': {},
                'error_message': None,
                'created_by': str(current_user.id)
            }
        )
        
        try:
            self.db.add(trial_entity)
            self.db.flush()  # Flush to get the ID without committing
            
            # Create relationship between trial and experiment
            relationship = Relationship(
                from_entity=trial_entity.id,
                to_entity=experiment_id,
                relationship_type='trial_of',
                properties={
                    'trial_number': trial_data.trial_number,
                    'created_by': str(current_user.id)
                }
            )
            self.db.add(relationship)
            
            # Log trial creation event
            self._log_event(
                "entity.created",
                trial_entity.id,
                "experiment.trial",
                {
                    "experiment_id": str(experiment_id),
                    "trial_number": trial_data.trial_number,
                    "status": "pending"
                },
                current_user.id
            )
            
            # Commit trial, relationship, and event together
            self.db.commit()
            self.db.refresh(trial_entity)
            
            return trial_entity
            
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictException("Trial creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Trial creation failed: {str(e)}")
    
    def get_trial(self, trial_id: UUID, current_user: User) -> Entity:
        """
        Get a trial by ID using entity architecture.
        
        Args:
            trial_id: Trial ID
            current_user: Current authenticated user
            
        Returns:
            Trial entity object
            
        Raises:
            NotFoundException: If trial not found
            PermissionException: If user lacks access
        """
        trial = self.db.query(Entity).filter(
            and_(
                Entity.id == trial_id,
                Entity.entity_type == 'experiment.trial'
            )
        ).first()
        
        if not trial:
            raise NotFoundException("Trial not found")
        
        # Check access through the associated experiment
        experiment_id = UUID(trial.properties.get('experiment_id'))
        experiment = self.get_experiment(experiment_id, current_user)
        
        return trial
    
    def list_trials(
        self,
        experiment_id: UUID,
        current_user: User,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> List[Entity]:
        """
        List trials for an experiment using entity architecture.
        
        Args:
            experiment_id: Experiment ID
            current_user: Current authenticated user
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            List of trial entities
        """
        # Verify access to experiment
        experiment = self.get_experiment(experiment_id, current_user)
        
        # Build query for trial entities
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'experiment.trial',
                Entity.properties.op('->>')('experiment_id') == str(experiment_id)
            )
        )
        
        # Apply status filter
        if status:
            query = query.filter(Entity.properties.op('->>')('status') == status)
        
        # Apply pagination and ordering
        trials = query.order_by(Entity.properties.op('->>')('trial_number')).offset((page - 1) * per_page).limit(per_page).all()
        
        return trials
    
    def update_trial(
        self,
        trial_id: UUID,
        trial_data: ExperimentTrialUpdate,
        current_user: User
    ) -> Entity:
        """
        Update a trial using entity architecture.
        
        Args:
            trial_id: Trial ID
            trial_data: Trial update data
            current_user: Current authenticated user
            
        Returns:
            Updated trial entity
            
        Raises:
            NotFoundException: If trial not found
            PermissionException: If user lacks access
            ValidationException: If update data is invalid
        """
        trial = self.get_trial(trial_id, current_user)
        
        # Update properties
        properties = trial.properties.copy()
        
        if 'status' in trial_data.dict(exclude_unset=True):
            new_status = trial_data.status
            if new_status == 'running':
                properties['status'] = 'running'
                properties['started_at'] = datetime.utcnow().isoformat()
            elif new_status == 'completed':
                properties['status'] = 'completed'
                properties['completed_at'] = datetime.utcnow().isoformat()
                if trial_data.results:
                    properties['results'] = trial_data.results
            elif new_status == 'failed':
                properties['status'] = 'failed'
                properties['completed_at'] = datetime.utcnow().isoformat()
                if trial_data.error_message:
                    properties['error_message'] = trial_data.error_message
        
        if 'parameters' in trial_data.dict(exclude_unset=True):
            properties['parameters'] = trial_data.parameters
        if 'results' in trial_data.dict(exclude_unset=True):
            properties['results'] = trial_data.results
        if 'error_message' in trial_data.dict(exclude_unset=True):
            properties['error_message'] = trial_data.error_message
        
        trial.properties = properties
        trial.updated_at = datetime.utcnow()
        
        try:
            # Log update event
            self._log_event(
                "entity.updated",
                trial.id,
                "experiment.trial",
                {
                    "experiment_id": trial.properties.get('experiment_id'),
                    "trial_number": trial.properties.get('trial_number'),
                    "status": properties.get('status'),
                    "updated_fields": list(trial_data.dict(exclude_unset=True).keys())
                },
                current_user.id
            )
            
            # Commit both trial update and event together
            self.db.commit()
            self.db.refresh(trial)
            
            return trial
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicException(f"Trial update failed: {str(e)}")
    
    def get_experiment_stats(self, organization_id: UUID, current_user: User) -> ExperimentStatsResponse:
        """
        Get experiment statistics for an organization using entity architecture.
        
        Args:
            organization_id: Organization ID
            current_user: Current authenticated user
            
        Returns:
            Experiment statistics
        """
        # Check organization access
        if not self._user_has_org_access(current_user, organization_id):
            raise PermissionException("Access denied to organization")
        
        try:
            # Get experiment counts by status
            experiments = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'experiment',
                    Entity.organization_id == organization_id
                )
            ).all()
            
            stats = {
                'total_experiments': len(experiments),
                'active_experiments': len([e for e in experiments if e.properties.get('status') == 'active']),
                'completed_experiments': len([e for e in experiments if e.properties.get('status') == 'completed']),
                'failed_experiments': len([e for e in experiments if e.properties.get('status') == 'failed']),
                'draft_experiments': len([e for e in experiments if e.properties.get('status') == 'draft']),
                'archived_experiments': len([e for e in experiments if e.properties.get('status') == 'archived']),
                'total_trials': 0,
                'running_trials': 0
            }
            
            # Get trial statistics
            for experiment in experiments:
                trials = self.list_trials(experiment.id, current_user)
                stats['total_trials'] += len(trials)
                stats['running_trials'] += len([t for t in trials if t.properties.get('status') == 'running'])
            
            return ExperimentStatsResponse(**stats)
            
        except Exception as e:
            logger.error(f"Error getting experiment stats for organization {organization_id}: {e}")
            return ExperimentStatsResponse(
                total_experiments=0,
                active_experiments=0,
                completed_experiments=0,
                failed_experiments=0,
                draft_experiments=0,
                archived_experiments=0,
                total_trials=0,
                running_trials=0
            )
    
    # Helper methods for entity-based operations
    
    def _experiment_name_exists(
        self, 
        name: str, 
        organization_id: Optional[UUID], 
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if an experiment name already exists in the organization."""
        query = self.db.query(Entity).filter(
            and_(
                Entity.entity_type == 'experiment',
                Entity.name == name,
                Entity.organization_id == organization_id,
                Entity.status != 'archived'
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
    
    def _validate_experiment_schema(self, experiment_data: ExperimentCreate) -> None:
        """Validate experiment data against schema if available."""
        try:
            # Check if schema validation function exists
            result = self.db.execute(
                text("SELECT validate_against_schema(:data, :schema_id)"),
                {
                    'data': str(experiment_data.dict()),
                    'schema_id': 'experiment'
                }
            ).scalar()
            
            if not result:
                raise ValidationException("Experiment data does not match required schema")
                
        except Exception as e:
            # If schema validation fails, log but don't block creation
            logger.warning(f"Schema validation failed: {e}")
    
    def _entity_to_experiment_dict(self, entity: Entity) -> Dict[str, Any]:
        """Convert experiment entity to dictionary representation."""
        return {
            "id": str(entity.id),
            "name": entity.name,
            "description": entity.description,
            "organization_id": str(entity.organization_id) if entity.organization_id else None,
            "project_id": entity.properties.get('project_id'),
            "process_id": entity.properties.get('process_id'),
            "bioreactor_id": entity.properties.get('bioreactor_id'),
            "status": entity.properties.get('status', 'draft'),
            "parameters": entity.properties.get('parameters', {}),
            "metadata": entity.properties.get('metadata', {}),
            "total_trials": entity.properties.get('total_trials', 1),
            "current_trial": entity.properties.get('current_trial', 1),
            "started_at": entity.properties.get('started_at'),
            "completed_at": entity.properties.get('completed_at'),
            "results": entity.properties.get('results', {}),
            "error_message": entity.properties.get('error_message'),
            "created_by": entity.properties.get('created_by'),
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }
    
    def _is_experiment_running(self, experiment: Entity) -> bool:
        """Check if experiment is running."""
        status = experiment.properties.get('status', 'draft')
        return status in ['active', 'paused']
    
    def _can_start_experiment(self, experiment: Entity) -> bool:
        """Check if experiment can be started."""
        status = experiment.properties.get('status', 'draft')
        return (status == 'draft' and 
                experiment.properties.get('project_id') and 
                experiment.properties.get('process_id') and 
                experiment.properties.get('bioreactor_id'))
    
    def _can_pause_experiment(self, experiment: Entity) -> bool:
        """Check if experiment can be paused."""
        status = experiment.properties.get('status', 'draft')
        return status == 'active'
    
    def _can_resume_experiment(self, experiment: Entity) -> bool:
        """Check if experiment can be resumed."""
        status = experiment.properties.get('status', 'draft')
        return status == 'paused'
    
    def _can_stop_experiment(self, experiment: Entity) -> bool:
        """Check if experiment can be stopped."""
        return self._is_experiment_running(experiment)
    
    def get_experiment_by_id(self, experiment_id: UUID) -> Optional[Entity]:
        """
        Get experiment by ID (legacy compatibility method).
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment entity or None if not found
        """
        try:
            return self.db.query(Entity).filter(
                and_(
                    Entity.id == experiment_id,
                    Entity.entity_type == 'experiment'
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting experiment {experiment_id}: {e}")
            return None
    
    def get_user_accessible_experiments(
        self, 
        user_id: UUID, 
        filters: ExperimentFilterRequest
    ) -> Tuple[List[Entity], int]:
        """
        Get experiments that a user has access to through organization membership.
        
        Args:
            user_id: User ID
            filters: Filter criteria
            
        Returns:
            Tuple of (experiments, total_count)
        """
        try:
            # Get user's organizations from user entity
            user = self.db.query(Entity).filter(
                and_(
                    Entity.id == user_id,
                    Entity.entity_type == 'user'
                )
            ).first()
            
            if not user:
                return [], 0
            
            # Get user's organization_id
            organization_id = user.organization_id
            if not organization_id:
                return [], 0
            
            # Build query for experiments in user's organization
            query = self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'experiment',
                    Entity.organization_id == organization_id
                )
            )
            
            # Apply filters
            if filters.status:
                query = query.filter(Entity.status == filters.status)
            
            if filters.project_id:
                query = query.filter(Entity.properties['project_id'].astext == str(filters.project_id))
            
            if filters.process_id:
                query = query.filter(Entity.properties['process_id'].astext == str(filters.process_id))
            
            if filters.bioreactor_id:
                query = query.filter(Entity.properties['bioreactor_id'].astext == str(filters.bioreactor_id))
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Entity.name.ilike(search_term),
                        Entity.description.ilike(search_term)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            if filters.page and filters.page_size:
                offset = (filters.page - 1) * filters.page_size
                query = query.offset(offset).limit(filters.page_size)
            
            experiments = query.order_by(Entity.created_at.desc()).all()
            return experiments, total_count
            
        except Exception as e:
            logger.error(f"Error getting user accessible experiments: {e}")
            return [], 0
    
    def archive_experiment(self, experiment_id: UUID, user_id: UUID) -> Optional[Entity]:
        """
        Archive an experiment.
        
        Args:
            experiment_id: Experiment ID
            user_id: ID of the user archiving the experiment
            
        Returns:
            Archived experiment entity or None if not found
        """
        try:
            experiment = self.get_experiment_by_id(experiment_id)
            if not experiment:
                return None
            
            # Prevent archiving running experiments
            status = experiment.properties.get('status', 'draft')
            if status in ['active', 'paused']:
                raise BusinessLogicException("Cannot archive experiment while it is running")
            
            # Update status to archived
            experiment.properties = experiment.properties or {}
            experiment.properties['status'] = 'archived'
            experiment.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(experiment)
            
            # Log event
            self._log_event(
                'experiment.archived',
                experiment.id,
                'experiment',
                {'previous_status': status},
                user_id
            )
            
            return experiment
            
        except Exception as e:
            logger.error(f"Error archiving experiment {experiment_id}: {e}")
            self.db.rollback()
            return None
    
    def get_trials_by_experiment(self, experiment_id: UUID) -> List[Entity]:
        """
        Get all trials for an experiment.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            List of trial entities
        """
        try:
            from sqlalchemy import Integer
            return self.db.query(Entity).filter(
                and_(
                    Entity.entity_type == 'experiment.trial',
                    Entity.properties['experiment_id'].astext == str(experiment_id)
                )
            ).order_by(Entity.properties['trial_number'].astext.cast(Integer)).all()
        except Exception as e:
            logger.error(f"Error getting trials for experiment {experiment_id}: {e}")
            return []

    def _log_event(self, event_type: str, entity_id: UUID, entity_type: str, data: Dict[str, Any], user_id: Optional[UUID] = None):
        """
        Log experiment event.
        
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
            logger.error(f"Failed to log experiment event: {str(e)}")

