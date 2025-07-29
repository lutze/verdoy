"""
Project model for laboratory project management.

Projects organize experiments, processes, and research activities
within an organization. They serve as containers for related work
and help with organization, permissions, and data management.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from .base import BaseModel
from ..database import JSONType


class Project(BaseModel):
    """
    Project model for organizing laboratory work and experiments.
    
    Projects provide:
    - Organization and structure for related experiments
    - Collaboration boundaries and permissions
    - Resource allocation and tracking
    - Progress monitoring and reporting
    - Data organization and archival
    """
    
    __tablename__ = "projects"
    
    # Project inherits from entities table - name and description are in entities
    # id is the foreign key to entities table
    
    # Organization relationship
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    
    # Project status and lifecycle
    status = Column(String(50), default="active", nullable=False, index=True)  # active, on_hold, completed, archived
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    
    # Project timeline
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    expected_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    
    # Project management
    project_lead_id = Column(PostgresUUID(as_uuid=True), ForeignKey("entities.id"), nullable=True, index=True)
    budget = Column(String(100), nullable=True)  # Stored as string for flexibility with currencies
    progress_percentage = Column(Integer, default=0, nullable=False)
    
    # Project metadata and configuration
    tags = Column(JSONType, default=list, nullable=False)  # List of tags for categorization
    project_metadata = Column(JSONType, default=dict, nullable=False)  # Additional metadata
    settings = Column(JSONType, default=dict, nullable=False)  # Project-specific settings
    
    # Relationships
    organization = relationship("Entity", foreign_keys=[organization_id])
    project_lead = relationship("Entity", foreign_keys=[project_lead_id])
    entity = relationship("Entity", foreign_keys=[BaseModel.id])  # Link to entity for name/description
    # experiments = relationship("Experiment", back_populates="project")  # Will be added when Experiment model exists
    # members = relationship("ProjectMember", back_populates="project")  # For project team management
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.entity.name if self.entity else 'Unknown'}', status='{self.status}')>"
    
    @property
    def name(self) -> str:
        """Get project name from associated entity."""
        return self.entity.name if self.entity else "Unknown"
    
    @property
    def description(self) -> str:
        """Get project description from associated entity."""
        return self.entity.description if self.entity else ""
    
    @property
    def is_active(self) -> bool:
        """Check if project is currently active."""
        return self.status == "active"
    
    @property
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == "completed"
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is past its expected completion date."""
        if not self.expected_completion:
            return False
        return datetime.utcnow() > self.expected_completion and not self.is_completed
    
    def get_duration_days(self) -> int:
        """Get project duration in days."""
        if not self.start_date:
            return 0
        
        end = self.actual_completion or self.end_date or datetime.utcnow()
        return (end - self.start_date).days
    
    def update_progress(self, percentage: int):
        """Update project progress percentage."""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            if percentage == 100 and self.status == "active":
                self.status = "completed"
                self.actual_completion = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a tag to the project."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags = self.tags + [tag]
    
    def remove_tag(self, tag: str):
        """Remove a tag from the project."""
        if self.tags and tag in self.tags:
            self.tags = [t for t in self.tags if t != tag]
    
    def to_dict(self):
        """Convert project to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "organization_id": str(self.organization_id),
            "status": self.status,
            "priority": self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "expected_completion": self.expected_completion.isoformat() if self.expected_completion else None,
            "actual_completion": self.actual_completion.isoformat() if self.actual_completion else None,
            "project_lead_id": str(self.project_lead_id) if self.project_lead_id else None,
            "budget": self.budget,
            "progress_percentage": self.progress_percentage,
            "tags": self.tags or [],
            "project_metadata": self.project_metadata or {},
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "is_overdue": self.is_overdue
        } 