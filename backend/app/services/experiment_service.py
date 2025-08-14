"""
Experiment service for the LMS Core API.

This module provides business logic for experiment management,
including CRUD operations, validation, and integration with
processes and bioreactors.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from fastapi import HTTPException

from ..models.experiment import Experiment, ExperimentTrial
from ..models.entity import Entity
from ..models.project import Project
from ..models.process import Process
from ..models.bioreactor import Bioreactor
from ..schemas.experiment import (
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    ExperimentTrialCreate, ExperimentTrialUpdate, ExperimentTrialResponse,
    ExperimentListResponse, ExperimentStatsResponse, ExperimentControlRequest,
    ExperimentControlResponse, ExperimentFilterRequest
)
from .base import BaseService
from .project_service import ProjectService
from .process_service import ProcessService
from .bioreactor_service import BioreactorService

logger = logging.getLogger(__name__)


class ExperimentService(BaseService[Experiment]):
    """
    Service for experiment management operations.
    
    Provides CRUD operations, validation, and business logic
    for experiments and their trials.
    """
    
    @property
    def model_class(self) -> type[Experiment]:
        """Return the Experiment model class."""
        return Experiment
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.project_service = ProjectService(db)
        self.process_service = ProcessService(db)
        self.bioreactor_service = BioreactorService(db)
    
    def create_experiment(self, experiment_data: ExperimentCreate, user_id: UUID) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            experiment_data: Experiment creation data
            user_id: ID of the user creating the experiment
            
        Returns:
            Created experiment
            
        Raises:
            HTTPException: If validation fails or resources not found
        """
        try:
            # Validate that project exists and user has access
            project = self.project_service.get_project_by_id(experiment_data.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Validate that process exists and is accessible
            process = self.process_service.get_process_by_id(experiment_data.process_id)
            if not process:
                raise HTTPException(status_code=404, detail="Process not found")
            
            # Validate that bioreactor exists and is available
            bioreactor = self.bioreactor_service.get_bioreactor_by_id(experiment_data.bioreactor_id)
            if not bioreactor:
                raise HTTPException(status_code=404, detail="Bioreactor not found")
            
            # Check if bioreactor is available for experiments
            if bioreactor.is_running_experiment():
                raise HTTPException(status_code=409, detail="Bioreactor is already running an experiment")
            
            # Create experiment
            experiment = Experiment(
                name=experiment_data.name,
                description=experiment_data.description,
                organization_id=project.organization_id,
                project_id=experiment_data.project_id,
                process_id=experiment_data.process_id,
                bioreactor_id=experiment_data.bioreactor_id,
                parameters=experiment_data.parameters,
                metadata=experiment_data.metadata,
                total_trials=experiment_data.total_trials,
                status='draft'
            )
            
            self.db.add(experiment)
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Created experiment {experiment.id} by user {user_id}")
            return experiment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create experiment")
    
    def get_experiment_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        """
        Get experiment by ID.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Experiment or None if not found
        """
        try:
            return self.db.query(Experiment).filter(
                Experiment.id == experiment_id,
                Experiment.entity_type == 'experiment'
            ).first()
        except Exception as e:
            logger.error(f"Error getting experiment {experiment_id}: {e}")
            return None
    
    def get_experiments_by_organization(
        self, 
        organization_id: UUID, 
        filters: ExperimentFilterRequest
    ) -> Tuple[List[Experiment], int]:
        """
        Get experiments for an organization with filtering.
        
        Args:
            organization_id: Organization ID
            filters: Filter criteria
            
        Returns:
            Tuple of (experiments, total_count)
        """
        try:
            query = self.db.query(Experiment).filter(
                Experiment.organization_id == organization_id,
                Experiment.entity_type == 'experiment'
            )
            
            # Apply filters
            if filters.status:
                query = query.filter(Experiment.status == filters.status)
            
            if filters.project_id:
                query = query.filter(Experiment.project_id == filters.project_id)
            
            if filters.process_id:
                query = query.filter(Experiment.process_id == filters.process_id)
            
            if filters.bioreactor_id:
                query = query.filter(Experiment.bioreactor_id == filters.bioreactor_id)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Experiment.name.ilike(search_term),
                        Experiment.description.ilike(search_term)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            experiments = query.offset(offset).limit(filters.page_size).all()
            
            return experiments, total_count
            
        except Exception as e:
            logger.error(f"Error getting experiments for organization {organization_id}: {e}")
            return [], 0
    
    def get_user_accessible_experiments(
        self, 
        user_id: UUID, 
        filters: ExperimentFilterRequest
    ) -> Tuple[List[Experiment], int]:
        """
        Get experiments that a user has access to through organization membership.
        
        Args:
            user_id: User ID
            filters: Filter criteria
            
        Returns:
            Tuple of (experiments, total_count)
        """
        try:
            from ..models.organization_member import OrganizationMember
            from ..models.user import User
            
            # Get user's organizations from membership table
            user_orgs = self.db.query(OrganizationMember.organization_id).filter(
                and_(
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.is_active == True
                )
            ).all()
            
            # Get user's legacy organization_id
            user = self.db.query(User).filter(User.id == user_id).first()
            legacy_org_id = user.organization_id if user else None
            
            # Build list of accessible organization IDs
            org_ids = [org[0] for org in user_orgs]  # Extract UUID from tuple
            if legacy_org_id and legacy_org_id not in org_ids:
                org_ids.append(legacy_org_id)
            
            if not org_ids:
                return [], 0
            
            # Query experiments from accessible organizations
            query = self.db.query(Experiment).filter(
                and_(
                    Experiment.organization_id.in_(org_ids),
                    Experiment.entity_type == 'experiment'
                )
            )
            
            # Apply filters
            if filters.status:
                query = query.filter(Experiment.status == filters.status)
            
            if filters.project_id:
                query = query.filter(Experiment.project_id == filters.project_id)
            
            if filters.process_id:
                query = query.filter(Experiment.process_id == filters.process_id)
            
            if filters.bioreactor_id:
                query = query.filter(Experiment.bioreactor_id == filters.bioreactor_id)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Experiment.name.ilike(search_term),
                        Experiment.description.ilike(search_term)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            experiments = query.offset(offset).limit(filters.page_size).all()
            
            return experiments, total_count
            
        except Exception as e:
            logger.error(f"Error getting user accessible experiments: {e}")
            return [], 0
    
    def update_experiment(
        self, 
        experiment_id: UUID, 
        experiment_data: ExperimentUpdate,
        user_id: UUID
    ) -> Optional[Experiment]:
        """
        Update an experiment.
        
        Args:
            experiment_id: Experiment ID
            experiment_data: Update data
            user_id: ID of the user updating the experiment
            
        Returns:
            Updated experiment or None if not found
            
        Raises:
            HTTPException: If validation fails or experiment is running
        """
        try:
            experiment = self.get_experiment_by_id(experiment_id)
            if not experiment:
                raise HTTPException(status_code=404, detail="Experiment not found")
            
            # Prevent updates to running experiments
            if experiment.is_running:
                raise HTTPException(
                    status_code=409, 
                    detail="Cannot update experiment while it is running"
                )
            
            # Update fields
            if experiment_data.name is not None:
                experiment.name = experiment_data.name
            
            if experiment_data.description is not None:
                experiment.description = experiment_data.description
            
            if experiment_data.parameters is not None:
                experiment.parameters = experiment_data.parameters
            
            if experiment_data.metadata is not None:
                experiment.metadata = experiment_data.metadata
            
            if experiment_data.total_trials is not None:
                experiment.total_trials = experiment_data.total_trials
            
            experiment.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Updated experiment {experiment_id} by user {user_id}")
            return experiment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating experiment {experiment_id}: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update experiment")
    
    def archive_experiment(self, experiment_id: UUID, user_id: UUID) -> Optional[Experiment]:
        """
        Archive an experiment.
        
        Args:
            experiment_id: Experiment ID
            user_id: ID of the user archiving the experiment
            
        Returns:
            Archived experiment or None if not found
            
        Raises:
            HTTPException: If experiment is running
        """
        try:
            experiment = self.get_experiment_by_id(experiment_id)
            if not experiment:
                raise HTTPException(status_code=404, detail="Experiment not found")
            
            # Prevent archiving running experiments
            if experiment.is_running:
                raise HTTPException(
                    status_code=409, 
                    detail="Cannot archive experiment while it is running"
                )
            
            experiment.archive_experiment()
            experiment.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Archived experiment {experiment_id} by user {user_id}")
            return experiment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error archiving experiment {experiment_id}: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to archive experiment")
    
    def control_experiment(
        self, 
        experiment_id: UUID, 
        control_data: ExperimentControlRequest,
        user_id: UUID
    ) -> ExperimentControlResponse:
        """
        Control an experiment (start, pause, resume, stop, complete, fail).
        
        Args:
            experiment_id: Experiment ID
            control_data: Control action data
            user_id: ID of the user controlling the experiment
            
        Returns:
            Control response
            
        Raises:
            HTTPException: If action is invalid or experiment not found
        """
        try:
            experiment = self.get_experiment_by_id(experiment_id)
            if not experiment:
                raise HTTPException(status_code=404, detail="Experiment not found")
            
            action = control_data.action
            bioreactor = None
            
            # Get bioreactor for status updates
            if experiment.bioreactor_id:
                bioreactor = self.bioreactor_service.get_bioreactor_by_id(experiment.bioreactor_id)
            
            if action == 'start':
                if not experiment.can_start():
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment cannot be started. Check that project, process, and bioreactor are set."
                    )
                
                # Check bioreactor availability
                if bioreactor and bioreactor.is_running_experiment():
                    raise HTTPException(
                        status_code=409, 
                        detail="Bioreactor is already running an experiment"
                    )
                
                experiment.start_experiment()
                
                # Update bioreactor status
                if bioreactor:
                    bioreactor.set_experiment_id(str(experiment.id))
                    bioreactor.set_control_mode('experiment')
                
                message = "Experiment started successfully"
                
            elif action == 'pause':
                if not experiment.can_pause():
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment cannot be paused"
                    )
                
                experiment.pause_experiment()
                message = "Experiment paused successfully"
                
            elif action == 'resume':
                if not experiment.can_resume():
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment cannot be resumed"
                    )
                
                experiment.resume_experiment()
                message = "Experiment resumed successfully"
                
            elif action == 'stop':
                if not experiment.can_stop():
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment cannot be stopped"
                    )
                
                # Stop experiment and clear bioreactor association
                experiment.fail_experiment("Experiment stopped by user")
                if bioreactor:
                    bioreactor.set_experiment_id(None)
                    bioreactor.set_control_mode('manual')
                
                message = "Experiment stopped successfully"
                
            elif action == 'complete':
                if not experiment.is_running:
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment is not running"
                    )
                
                experiment.complete_experiment(control_data.results)
                
                # Clear bioreactor association
                if bioreactor:
                    bioreactor.set_experiment_id(None)
                    bioreactor.set_control_mode('manual')
                
                message = "Experiment completed successfully"
                
            elif action == 'fail':
                if not experiment.is_running:
                    raise HTTPException(
                        status_code=409, 
                        detail="Experiment is not running"
                    )
                
                experiment.fail_experiment(control_data.error_message or "Experiment failed")
                
                # Clear bioreactor association
                if bioreactor:
                    bioreactor.set_experiment_id(None)
                    bioreactor.set_control_mode('manual')
                
                message = "Experiment marked as failed"
            
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
            
            experiment.last_updated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Experiment {experiment_id} {action} by user {user_id}")
            
            return ExperimentControlResponse(
                success=True,
                message=message,
                experiment=ExperimentResponse.from_orm(experiment)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error controlling experiment {experiment_id}: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to control experiment")
    
    def create_trial(
        self, 
        experiment_id: UUID, 
        trial_data: ExperimentTrialCreate,
        user_id: UUID
    ) -> Optional[ExperimentTrial]:
        """
        Create a new trial for an experiment.
        
        Args:
            experiment_id: Experiment ID
            trial_data: Trial creation data
            user_id: ID of the user creating the trial
            
        Returns:
            Created trial or None if experiment not found
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            experiment = self.get_experiment_by_id(experiment_id)
            if not experiment:
                raise HTTPException(status_code=404, detail="Experiment not found")
            
            # Check if trial number already exists
            existing_trial = self.db.query(ExperimentTrial).filter(
                ExperimentTrial.experiment_id == experiment_id,
                ExperimentTrial.trial_number == trial_data.trial_number
            ).first()
            
            if existing_trial:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Trial number {trial_data.trial_number} already exists for this experiment"
                )
            
            # Create trial
            trial = ExperimentTrial(
                experiment_id=experiment_id,
                trial_number=trial_data.trial_number,
                parameters=trial_data.parameters,
                created_by=user_id
            )
            
            self.db.add(trial)
            self.db.commit()
            self.db.refresh(trial)
            
            logger.info(f"Created trial {trial.id} for experiment {experiment_id} by user {user_id}")
            return trial
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating trial for experiment {experiment_id}: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create trial")
    
    def get_trials_by_experiment(self, experiment_id: UUID) -> List[ExperimentTrial]:
        """
        Get all trials for an experiment.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            List of trials
        """
        try:
            return self.db.query(ExperimentTrial).filter(
                ExperimentTrial.experiment_id == experiment_id
            ).order_by(ExperimentTrial.trial_number).all()
        except Exception as e:
            logger.error(f"Error getting trials for experiment {experiment_id}: {e}")
            return []
    
    def get_experiment_stats(self, organization_id: UUID) -> ExperimentStatsResponse:
        """
        Get experiment statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Experiment statistics
        """
        try:
            # Get experiment counts by status
            experiments = self.db.query(Experiment).filter(
                Experiment.organization_id == organization_id,
                Experiment.entity_type == 'experiment'
            ).all()
            
            stats = {
                'total_experiments': len(experiments),
                'active_experiments': len([e for e in experiments if e.is_active]),
                'completed_experiments': len([e for e in experiments if e.is_completed]),
                'failed_experiments': len([e for e in experiments if e.is_failed]),
                'draft_experiments': len([e for e in experiments if e.is_draft]),
                'archived_experiments': len([e for e in experiments if e.is_archived]),
                'total_trials': 0,
                'running_trials': 0
            }
            
            # Get trial statistics
            for experiment in experiments:
                trials = self.get_trials_by_experiment(experiment.id)
                stats['total_trials'] += len(trials)
                stats['running_trials'] += len([t for t in trials if t.status == 'running'])
            
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
    
    def validate_experiment_data(self, experiment_data: ExperimentCreate) -> List[str]:
        """
        Validate experiment creation data.
        
        Args:
            experiment_data: Experiment creation data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate project exists
        project = self.project_service.get_project_by_id(experiment_data.project_id)
        if not project:
            errors.append("Project not found")
        
        # Validate process exists
        process = self.process_service.get_process_by_id(experiment_data.process_id)
        if not process:
            errors.append("Process not found")
        
        # Validate bioreactor exists and is available
        bioreactor = self.bioreactor_service.get_bioreactor_by_id(experiment_data.bioreactor_id)
        if not bioreactor:
            errors.append("Bioreactor not found")
        elif bioreactor.is_running_experiment():
            errors.append("Bioreactor is already running an experiment")
        
        # Validate parameters against process requirements
        if process and experiment_data.parameters:
            process_params = process.get_parameters()
            for param_name, param_value in experiment_data.parameters.items():
                if param_name in process_params:
                    # Basic range validation (could be enhanced)
                    expected_type = type(process_params[param_name])
                    if not isinstance(param_value, expected_type):
                        errors.append(f"Parameter {param_name} has wrong type")
        
        return errors 