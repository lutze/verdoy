"""
Project model for laboratory project management.

Projects organize experiments, processes, and research activities
within an organization. They serve as containers for related work
and help with organization, permissions, and data management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import relationship
from uuid import UUID

from .entity import Entity


class Project(Entity):
    """
    Project model for organizing laboratory work and experiments.
    
    Maps to the entities table with entity_type = 'project'
    and stores project-specific fields in the properties JSONB column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'project',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for projects
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'project'
        super().__init__(*args, **kwargs)
    
    # Project-specific property accessors
    @property
    def start_date(self) -> Optional[datetime]:
        """Get project start date from properties."""
        start_date_str = self.get_property('start_date')
        if start_date_str:
            return datetime.fromisoformat(start_date_str)
        return None
    
    @start_date.setter
    def start_date(self, value: Optional[datetime]):
        """Set project start date in properties."""
        if value:
            self.set_property('start_date', value.isoformat())
        else:
            self.set_property('start_date', None)
    
    @property
    def end_date(self) -> Optional[datetime]:
        """Get project end date from properties."""
        end_date_str = self.get_property('end_date')
        if end_date_str:
            return datetime.fromisoformat(end_date_str)
        return None
    
    @end_date.setter
    def end_date(self, value: Optional[datetime]):
        """Set project end date in properties."""
        if value:
            self.set_property('end_date', value.isoformat())
        else:
            self.set_property('end_date', None)
    
    @property
    def expected_completion(self) -> Optional[datetime]:
        """Get expected completion date from properties."""
        completion_str = self.get_property('expected_completion')
        if completion_str:
            return datetime.fromisoformat(completion_str)
        return None
    
    @expected_completion.setter
    def expected_completion(self, value: Optional[datetime]):
        """Set expected completion date in properties."""
        if value:
            self.set_property('expected_completion', value.isoformat())
        else:
            self.set_property('expected_completion', None)
    
    @property
    def actual_completion(self) -> Optional[datetime]:
        """Get actual completion date from properties."""
        completion_str = self.get_property('actual_completion')
        if completion_str:
            return datetime.fromisoformat(completion_str)
        return None
    
    @actual_completion.setter
    def actual_completion(self, value: Optional[datetime]):
        """Set actual completion date in properties."""
        if value:
            self.set_property('actual_completion', value.isoformat())
        else:
            self.set_property('actual_completion', None)
    
    @property
    def budget(self) -> Optional[str]:
        """Get project budget from properties."""
        return self.get_property('budget')
    
    @budget.setter
    def budget(self, value: Optional[str]):
        """Set project budget in properties."""
        self.set_property('budget', value)
    
    @property
    def progress_percentage(self) -> int:
        """Get project progress percentage from properties."""
        return self.get_property('progress_percentage', 0)
    
    @progress_percentage.setter
    def progress_percentage(self, value: int):
        """Set project progress percentage in properties."""
        self.set_property('progress_percentage', value)
    
    @property
    def tags(self) -> List[str]:
        """Get project tags from properties."""
        return self.get_property('tags', [])
    
    @tags.setter
    def tags(self, value: List[str]):
        """Set project tags in properties."""
        self.set_property('tags', value)
    
    @property
    def project_metadata(self) -> Dict[str, Any]:
        """Get project metadata from properties."""
        return self.get_property('project_metadata', {})
    
    @project_metadata.setter
    def project_metadata(self, value: Dict[str, Any]):
        """Set project metadata in properties."""
        self.set_property('project_metadata', value)
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Get project settings from properties."""
        return self.get_property('settings', {})
    
    @settings.setter
    def settings(self, value: Dict[str, Any]):
        """Set project settings in properties."""
        self.set_property('settings', value)
    
    # Note: organization_id is inherited from Entity base class
    # and stored in the actual database column, not in properties
    
    @property
    def project_lead_id(self) -> Optional[UUID]:
        """Get project lead ID from properties."""
        lead_id_str = self.get_property('project_lead_id')
        if lead_id_str:
            return UUID(lead_id_str)
        return None
    
    @project_lead_id.setter
    def project_lead_id(self, value: Optional[UUID]):
        """Set project lead ID in properties."""
        if value:
            self.set_property('project_lead_id', str(value))
        else:
            self.set_property('project_lead_id', None)
    
    @property
    def priority(self) -> str:
        """Get project priority from properties."""
        return self.get_property('priority', 'medium')
    
    @priority.setter
    def priority(self, value: str):
        """Set project priority in properties."""
        self.set_property('priority', value)
    
    @property
    def members(self) -> List[Any]:
        """
        Get project team members.
        
        TODO: Implement proper project-member relationship.
        For now, returns empty list as placeholder.
        """
        # TODO: Implement proper relationship with User model
        # This should query a project_members junction table
        return []
    
    @property
    def member_count(self) -> int:
        """
        Get count of project team members.
        
        TODO: Implement proper project-member relationship.
        For now, returns 0 as placeholder.
        """
        # TODO: Implement proper count from project_members table
        return 0
    
    # Business logic methods
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
        current_tags = self.tags
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = current_tags
    
    def remove_tag(self, tag: str):
        """Remove a tag from the project."""
        current_tags = self.tags
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = current_tags
    
    def to_dict(self):
        """Convert project to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "status": self.status,
            "priority": self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "expected_completion": self.expected_completion.isoformat() if self.expected_completion else None,
            "actual_completion": self.actual_completion.isoformat() if self.actual_completion else None,
            "project_lead_id": str(self.project_lead_id) if self.project_lead_id else None,
            "budget": self.budget,
            "progress_percentage": self.progress_percentage,
            "tags": self.tags,
            "project_metadata": self.project_metadata,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "is_overdue": self.is_overdue
        } 