"""
Experiment model for laboratory experiment management.

Experiments represent specific research activities that use processes
and bioreactors to achieve scientific objectives. They track execution,
results, and multiple trials for reproducibility.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from .base import Base, BaseModel
from .entity import Entity
from ..database import JSONType


class Experiment(Entity):
    """
    Experiment model for managing laboratory experiments.
    
    Maps to the entities table with entity_type = 'experiment'
    and stores experiment-specific fields in the properties JSONB column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'experiment',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for experiments
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'experiment'
        super().__init__(*args, **kwargs)
    
    # Experiment-specific property accessors
    @property
    def project_id(self) -> Optional[UUID]:
        """Get project ID from properties."""
        project_id_str = self.get_property('project_id')
        if project_id_str:
            return UUID(project_id_str)
        return None
    
    @project_id.setter
    def project_id(self, value: Optional[UUID]):
        """Set project ID in properties."""
        if value:
            self.set_property('project_id', str(value))
        else:
            self.set_property('project_id', None)
    
    @property
    def process_id(self) -> Optional[UUID]:
        """Get process ID from properties."""
        process_id_str = self.get_property('process_id')
        if process_id_str:
            return UUID(process_id_str)
        return None
    
    @process_id.setter
    def process_id(self, value: Optional[UUID]):
        """Set process ID in properties."""
        if value:
            self.set_property('process_id', str(value))
        else:
            self.set_property('process_id', None)
    
    @property
    def bioreactor_id(self) -> Optional[UUID]:
        """Get bioreactor ID from properties."""
        bioreactor_id_str = self.get_property('bioreactor_id')
        if bioreactor_id_str:
            return UUID(bioreactor_id_str)
        return None
    
    @bioreactor_id.setter
    def bioreactor_id(self, value: Optional[UUID]):
        """Set bioreactor ID in properties."""
        if value:
            self.set_property('bioreactor_id', str(value))
        else:
            self.set_property('bioreactor_id', None)
    
    @property
    def status(self) -> str:
        """Get experiment status from properties."""
        return self.get_property('status', 'draft')
    
    @status.setter
    def status(self, value: str):
        """Set experiment status in properties."""
        valid_statuses = ['draft', 'active', 'paused', 'completed', 'failed', 'archived']
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self.set_property('status', value)
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get experiment parameters from properties."""
        return self.get_property('parameters', {})
    
    @parameters.setter
    def parameters(self, value: Dict[str, Any]):
        """Set experiment parameters in properties."""
        self.set_property('parameters', value)
    
    @property
    def experiment_metadata(self) -> Dict[str, Any]:
        """Get experiment metadata from properties."""
        return self.get_property('metadata', {})
    
    @experiment_metadata.setter
    def experiment_metadata(self, value: Dict[str, Any]):
        """Set experiment metadata in properties."""
        self.set_property('metadata', value)
    
    @property
    def current_trial(self) -> int:
        """Get current trial number from properties."""
        return self.get_property('current_trial', 1)
    
    @current_trial.setter
    def current_trial(self, value: int):
        """Set current trial number in properties."""
        if value < 1:
            raise ValueError("Trial number must be at least 1")
        self.set_property('current_trial', value)
    
    @property
    def total_trials(self) -> int:
        """Get total number of trials from properties."""
        return self.get_property('total_trials', 1)
    
    @total_trials.setter
    def total_trials(self, value: int):
        """Set total number of trials in properties."""
        if value < 1:
            raise ValueError("Total trials must be at least 1")
        self.set_property('total_trials', value)
    
    @property
    def started_at(self) -> Optional[datetime]:
        """Get experiment start time from properties."""
        started_str = self.get_property('started_at')
        if started_str:
            return datetime.fromisoformat(started_str)
        return None
    
    @started_at.setter
    def started_at(self, value: Optional[datetime]):
        """Set experiment start time in properties."""
        if value:
            self.set_property('started_at', value.isoformat())
        else:
            self.set_property('started_at', None)
    
    @property
    def completed_at(self) -> Optional[datetime]:
        """Get experiment completion time from properties."""
        completed_str = self.get_property('completed_at')
        if completed_str:
            return datetime.fromisoformat(completed_str)
        return None
    
    @completed_at.setter
    def completed_at(self, value: Optional[datetime]):
        """Set experiment completion time in properties."""
        if value:
            self.set_property('completed_at', value.isoformat())
        else:
            self.set_property('completed_at', None)
    
    @property
    def results(self) -> Dict[str, Any]:
        """Get experiment results from properties."""
        return self.get_property('results', {})
    
    @results.setter
    def results(self, value: Dict[str, Any]):
        """Set experiment results in properties."""
        self.set_property('results', value)
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message from properties."""
        return self.get_property('error_message')
    
    @error_message.setter
    def error_message(self, value: Optional[str]):
        """Set error message in properties."""
        self.set_property('error_message', value)
    
    # Status check methods
    @property
    def is_draft(self) -> bool:
        """Check if experiment is in draft status."""
        return self.status == 'draft'
    
    @property
    def is_active(self) -> bool:
        """Check if experiment is active."""
        return self.status == 'active'
    
    @property
    def is_paused(self) -> bool:
        """Check if experiment is paused."""
        return self.status == 'paused'
    
    @property
    def is_completed(self) -> bool:
        """Check if experiment is completed."""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """Check if experiment failed."""
        return self.status == 'failed'
    
    @property
    def is_archived(self) -> bool:
        """Check if experiment is archived."""
        return self.status == 'archived'
    
    @property
    def is_running(self) -> bool:
        """Check if experiment is running (active or paused)."""
        return self.status in ['active', 'paused']
    
    @property
    def is_finished(self) -> bool:
        """Check if experiment is finished (completed or failed)."""
        return self.status in ['completed', 'failed']
    
    # Experiment lifecycle methods
    def start_experiment(self) -> None:
        """Start the experiment."""
        if not self.is_draft:
            raise ValueError(f"Cannot start experiment in {self.status} status")
        
        self.status = 'active'
        self.started_at = datetime.utcnow()
        self.error_message = None
    
    def pause_experiment(self) -> None:
        """Pause the experiment."""
        if not self.is_active:
            raise ValueError(f"Cannot pause experiment in {self.status} status")
        
        self.status = 'paused'
    
    def resume_experiment(self) -> None:
        """Resume the experiment."""
        if not self.is_paused:
            raise ValueError(f"Cannot resume experiment in {self.status} status")
        
        self.status = 'active'
    
    def complete_experiment(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Complete the experiment."""
        if not self.is_running:
            raise ValueError(f"Cannot complete experiment in {self.status} status")
        
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if results:
            self.results = results
    
    def fail_experiment(self, error_message: str) -> None:
        """Mark experiment as failed."""
        if not self.is_running:
            raise ValueError(f"Cannot fail experiment in {self.status} status")
        
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def archive_experiment(self) -> None:
        """Archive the experiment."""
        self.status = 'archived'
    
    def get_duration_minutes(self) -> Optional[int]:
        """Get experiment duration in minutes."""
        if not self.started_at:
            return None
        
        if self.completed_at:
            end_time = self.completed_at
        else:
            # Use timezone-aware datetime to match started_at
            from datetime import datetime, timezone
            end_time = datetime.now(timezone.utc)
        
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60)
    
    def get_progress_percentage(self) -> int:
        """Get experiment progress percentage."""
        if not self.is_running:
            return 100 if self.is_finished else 0
        
        # For now, return 50% for running experiments
        # This could be enhanced with actual progress tracking
        return 50
    
    def can_start(self) -> bool:
        """Check if experiment can be started."""
        return self.is_draft and self.project_id and self.process_id and self.bioreactor_id
    
    def can_pause(self) -> bool:
        """Check if experiment can be paused."""
        return self.is_active
    
    def can_resume(self) -> bool:
        """Check if experiment can be resumed."""
        return self.is_paused
    
    def can_stop(self) -> bool:
        """Check if experiment can be stopped."""
        return self.is_running
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert experiment to dictionary representation."""
        result = super().to_dict()
        result.update({
            'project_id': str(self.project_id) if self.project_id else None,
            'process_id': str(self.process_id) if self.process_id else None,
            'bioreactor_id': str(self.bioreactor_id) if self.bioreactor_id else None,
            'status': self.status,
            'parameters': self.parameters,
            'metadata': self.experiment_metadata,
            'current_trial': self.current_trial,
            'total_trials': self.total_trials,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': self.results,
            'error_message': self.error_message,
            'duration_minutes': self.get_duration_minutes(),
            'progress_percentage': self.get_progress_percentage(),
            'is_running': self.is_running,
            'is_finished': self.is_finished,
            'can_start': self.can_start(),
            'can_pause': self.can_pause(),
            'can_resume': self.can_resume(),
            'can_stop': self.can_stop()
        })
        return result


class ExperimentTrial(Base):
    """
    ExperimentTrial model representing specific executions of experiments.
    
    Experiment trials track individual executions of experiments,
    including parameters, results, and execution details.
    """
    
    __tablename__ = "experiment_trials"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    trial_number = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    parameters = Column(JSONType, default={})  # Trial-specific parameters
    results = Column(JSONType, default={})  # Trial results and data
    error_message = Column(Text)
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ExperimentTrial(id={self.id}, experiment_id={self.experiment_id}, trial_number={self.trial_number})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trial to dictionary representation."""
        return {
            "id": str(self.id),
            "experiment_id": str(self.experiment_id),
            "trial_number": self.trial_number,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parameters": self.parameters,
            "results": self.results,
            "error_message": self.error_message,
            "created_by": str(self.created_by) if self.created_by else None
        }
    
    def start_trial(self) -> None:
        """Start the trial."""
        if self.status != "pending":
            raise ValueError(f"Cannot start trial in {self.status} status")
        
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def complete_trial(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Complete the trial."""
        if self.status != "running":
            raise ValueError(f"Cannot complete trial in {self.status} status")
        
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if results:
            self.results = results
    
    def fail_trial(self, error_message: str) -> None:
        """Mark trial as failed."""
        if self.status != "running":
            raise ValueError(f"Cannot fail trial in {self.status} status")
        
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def get_duration_minutes(self) -> Optional[int]:
        """Get trial duration in minutes."""
        if not self.started_at:
            return None
        
        if self.completed_at:
            end_time = self.completed_at
        else:
            # Use timezone-aware datetime to match started_at
            from datetime import datetime, timezone
            end_time = datetime.now(timezone.utc)
        
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60) 