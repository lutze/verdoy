"""
Process models for the VerdoyLab system.

This module defines the Process and ProcessInstance models that handle
process definitions, templates, and execution instances.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from .base import Base
from ..database import JSONType


class Process(Base):
    """
    Process model representing process definitions and templates.
    
    Processes define reusable workflows, recipes, or procedures that can be
    executed on bioreactors or other devices. They contain step definitions,
    parameters, and expected outcomes.
    """
    __tablename__ = "processes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)
    process_type = Column(String(100), nullable=False)
    definition = Column(JSONType, nullable=False)  # Steps, parameters, expected outcomes
    status = Column(String(50), default="active")
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"))
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"))
    description = Column(Text)
    is_template = Column(Boolean, default=False)  # Whether this is a reusable template
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Entity", foreign_keys=[organization_id])
    creator = relationship("Entity", foreign_keys=[created_by])
    instances = relationship("ProcessInstance", back_populates="process", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Process(id={self.id}, name='{self.name}', version='{self.version}', type='{self.process_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert process to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "process_type": self.process_type,
            "definition": self.definition,
            "status": self.status,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "description": self.description,
            "is_template": self.is_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_step_count(self) -> int:
        """Get the number of steps in this process."""
        steps = self.definition.get("steps", [])
        return len(steps)
    
    def get_estimated_duration(self) -> Optional[int]:
        """Get estimated duration in minutes."""
        return self.definition.get("estimated_duration")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get process parameters."""
        return self.definition.get("parameters", {})
    
    def get_steps(self) -> List[Dict[str, Any]]:
        """Get process steps."""
        return self.definition.get("steps", [])
    
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the process."""
        steps = self.get_steps()
        steps.append(step)
        self.definition["steps"] = steps
        self.updated_at = datetime.utcnow()
    
    def remove_step(self, step_index: int) -> bool:
        """Remove a step from the process by index."""
        steps = self.get_steps()
        if 0 <= step_index < len(steps):
            steps.pop(step_index)
            self.definition["steps"] = steps
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def update_step(self, step_index: int, step_data: Dict[str, Any]) -> bool:
        """Update a step in the process by index."""
        steps = self.get_steps()
        if 0 <= step_index < len(steps):
            steps[step_index] = step_data
            self.definition["steps"] = steps
            self.updated_at = datetime.utcnow()
            return True
        return False


class ProcessInstance(Base):
    """
    ProcessInstance model representing specific executions of processes.
    
    Process instances track the execution of a process definition,
    including current state, parameters, and results.
    """
    __tablename__ = "process_instances"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    process_id = Column(PostgresUUID(as_uuid=True), ForeignKey("processes.id"), nullable=False)
    batch_id = Column(String(100))  # Optional batch identifier
    status = Column(String(50), default="running")  # running, completed, failed, paused
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    parameters = Column(JSONType, default={})  # Instance-specific parameters
    results = Column(JSONType, default={})  # Execution results and data
    current_step = Column(String(100))  # Current step being executed
    step_results = Column(JSONType, default={})  # Results for each step
    error_message = Column(Text)  # Error message if failed
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"))
    
    # Relationships
    process = relationship("Process", back_populates="instances")
    creator = relationship("Entity", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ProcessInstance(id={self.id}, process_id={self.process_id}, status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert process instance to dictionary representation."""
        return {
            "id": str(self.id),
            "process_id": str(self.process_id),
            "batch_id": self.batch_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parameters": self.parameters,
            "results": self.results,
            "current_step": self.current_step,
            "step_results": self.step_results,
            "error_message": self.error_message,
            "created_by": str(self.created_by) if self.created_by else None
        }
    
    def get_duration(self) -> Optional[int]:
        """Get execution duration in minutes."""
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return int(duration.total_seconds() / 60)
        return None
    
    def is_completed(self) -> bool:
        """Check if the process instance is completed."""
        return self.status in ["completed", "failed"]
    
    def is_running(self) -> bool:
        """Check if the process instance is running."""
        return self.status == "running"
    
    def is_paused(self) -> bool:
        """Check if the process instance is paused."""
        return self.status == "paused"
    
    def is_failed(self) -> bool:
        """Check if the process instance failed."""
        return self.status == "failed"
    
    def complete(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Mark the process instance as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if results:
            self.results.update(results)
    
    def fail(self, error_message: str) -> None:
        """Mark the process instance as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def pause(self) -> None:
        """Pause the process instance."""
        self.status = "paused"
    
    def resume(self) -> None:
        """Resume the process instance."""
        self.status = "running"
    
    def update_current_step(self, step_name: str, step_result: Optional[Dict[str, Any]] = None) -> None:
        """Update the current step being executed."""
        self.current_step = step_name
        if step_result:
            if not self.step_results:
                self.step_results = {}
            self.step_results[step_name] = step_result 