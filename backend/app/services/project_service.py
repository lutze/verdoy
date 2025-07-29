"""
Project service for laboratory project management and operations.

This service handles:
- Project creation and management  
- Project lifecycle management (status, progress)
- Project team and permissions
- Project statistics and reporting
- Project-organization relationships
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from .base import BaseService
from ..models.project import Project
from ..models.organization import Organization
from ..models.user import User
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectStatistics
from ..exceptions import (
    ServiceException,
    ValidationException,
    NotFoundException,
    ProjectNotFoundException,
    OrganizationNotFoundException,
    UserNotFoundException
)

logger = logging.getLogger(__name__)


class ProjectService(BaseService[Project]):
    """
    Project service for laboratory project management.
    
    This service provides business logic for:
    - Project creation and management
    - Project lifecycle and status management
    - Project team management and permissions
    - Progress tracking and reporting
    - Organization-project relationships
    """
    
    @property
    def model_class(self) -> type[Project]:
        """Return the Project model class."""
        return Project
    
    def create_project(self, project_data: ProjectCreate, created_by: Optional[UUID] = None) -> Project:
        """
        Create a new project.
        
        Args:
            project_data: Project creation data
            created_by: User ID who created the project
            
        Returns:
            The created project
            
        Raises:
            OrganizationNotFoundException: If organization not found
            UserNotFoundException: If project lead not found
            ValidationException: If data validation fails
            ServiceException: If creation fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate project data
            self.validate_project_data(project_data)
            
            # Verify organization exists
            organization = self.db.query(Organization).filter(
                Organization.id == project_data.organization_id
            ).first()
            if not organization:
                raise OrganizationNotFoundException(f"Organization {project_data.organization_id} not found")
            
            # Verify project lead exists if provided
            if project_data.project_lead_id:
                project_lead = self.db.query(User).filter(
                    User.id == project_data.project_lead_id
                ).first()
                if not project_lead:
                    raise UserNotFoundException(f"User {project_data.project_lead_id} not found")
            
            # Create project
            project = Project(
                name=project_data.name,
                description=project_data.description,
                organization_id=project_data.organization_id,
                status=project_data.status.value,
                priority=project_data.priority.value,
                start_date=project_data.start_date,
                end_date=project_data.end_date,
                expected_completion=project_data.expected_completion,
                project_lead_id=project_data.project_lead_id,
                budget=project_data.budget,
                progress_percentage=project_data.progress_percentage,
                tags=project_data.tags,
                project_metadata=project_data.project_metadata,
                settings=project_data.settings
            )
            
            # Save to database
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            # Audit log
            self.audit_log("project_created", project.id, {
                "name": project.name,
                "organization_id": str(project.organization_id),
                "created_by": str(created_by) if created_by else "system"
            })
            
            # Performance monitoring
            self.performance_monitor("project_creation", start_time)
            
            logger.info(f"Project created successfully: {project.name}")
            return project
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during project creation: {e}")
            raise ServiceException("Failed to create project due to data conflict")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during project creation: {e}")
            raise ServiceException("Failed to create project")
    
    def get_projects_by_organization(self, organization_id: UUID, status: Optional[str] = None) -> List[Project]:
        """
        Get projects for a specific organization.
        
        Args:
            organization_id: Organization ID
            status: Optional status filter
            
        Returns:
            List of projects
        """
        try:
            query = self.db.query(Project).filter(Project.organization_id == organization_id)
            
            if status:
                query = query.filter(Project.status == status)
            
            projects = query.order_by(Project.created_at.desc()).all()
            logger.debug(f"Retrieved {len(projects)} projects for organization {organization_id}")
            return projects
            
        except Exception as e:
            logger.error(f"Error getting projects by organization: {e}")
            return []
    
    def get_projects_by_user(self, user_id: UUID, role: str = "lead") -> List[Project]:
        """
        Get projects where user has a specific role.
        
        Args:
            user_id: User ID
            role: Role type (currently only "lead" supported)
            
        Returns:
            List of projects
        """
        try:
            if role == "lead":
                projects = self.db.query(Project).filter(
                    Project.project_lead_id == user_id
                ).order_by(Project.created_at.desc()).all()
            else:
                # TODO: Implement team member role filtering when ProjectMember model exists
                projects = []
            
            logger.debug(f"Retrieved {len(projects)} projects for user {user_id} with role {role}")
            return projects
            
        except Exception as e:
            logger.error(f"Error getting projects by user: {e}")
            return []
    
    def update_project(self, project_id: UUID, project_data: ProjectUpdate, updated_by: Optional[UUID] = None) -> Project:
        """
        Update an existing project.
        
        Args:
            project_id: Project ID
            project_data: Project update data
            updated_by: User ID who updated the project
            
        Returns:
            Updated project
            
        Raises:
            NotFoundException: If project not found
            ValidationException: If data validation fails
            ServiceException: If update fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Get existing project
            project = self.get_by_id_or_raise(project_id)
            
            # Validate update data
            self.validate_project_update_data(project_data)
            
            # Update project fields
            update_fields = {}
            for field, value in project_data.dict(exclude_unset=True).items():
                if hasattr(project, field):
                    setattr(project, field, value)
                    update_fields[field] = value
            
            # Update timestamps
            project.updated_at = datetime.utcnow()
            
            # Save to database
            self.db.commit()
            self.db.refresh(project)
            
            # Audit log
            self.audit_log("project_updated", project_id, {
                "updated_fields": list(update_fields.keys()),
                "updated_by": str(updated_by) if updated_by else "system"
            })
            
            # Performance monitoring
            self.performance_monitor("project_update", start_time)
            
            logger.info(f"Project updated successfully: {project.name}")
            return project
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during project update: {e}")
            raise ServiceException("Failed to update project due to data conflict")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during project update: {e}")
            raise ServiceException("Failed to update project")

    def update_project_progress(self, project_id: UUID, progress_percentage: int) -> Project:
        """
        Update project progress percentage.
        
        Args:
            project_id: Project ID
            progress_percentage: New progress percentage (0-100)
            
        Returns:
            Updated project
            
        Raises:
            NotFoundException: If project not found
            ValidationException: If progress percentage invalid
            ServiceException: If update fails
        """
        try:
            if not (0 <= progress_percentage <= 100):
                raise ValidationException("Progress percentage must be between 0 and 100")
            
            project = self.get_by_id_or_raise(project_id)
            old_progress = project.progress_percentage
            
            project.update_progress(progress_percentage)
            self.db.commit()
            self.db.refresh(project)
            
            # Audit log
            self.audit_log("project_progress_updated", project_id, {
                "old_progress": old_progress,
                "new_progress": progress_percentage,
                "status": project.status
            })
            
            logger.info(f"Project progress updated: {project.name} -> {progress_percentage}%")
            return project
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating project progress: {e}")
            raise ServiceException("Failed to update project progress")
    
    def get_overdue_projects(self, organization_id: Optional[UUID] = None) -> List[Project]:
        """
        Get projects that are overdue (past expected completion and not completed).
        
        Args:
            organization_id: Optional organization filter
            
        Returns:
            List of overdue projects
        """
        try:
            query = self.db.query(Project).filter(
                Project.expected_completion < datetime.utcnow().date(),
                Project.status.in_(["active", "on_hold"])
            )
            
            if organization_id:
                query = query.filter(Project.organization_id == organization_id)
            
            overdue_projects = query.order_by(Project.expected_completion.asc()).all()
            logger.debug(f"Found {len(overdue_projects)} overdue projects")
            return overdue_projects
            
        except Exception as e:
            logger.error(f"Error getting overdue projects: {e}")
            return []
    
    def get_project_statistics(self, organization_id: Optional[UUID] = None) -> ProjectStatistics:
        """
        Get project statistics for analytics.
        
        Args:
            organization_id: Optional organization filter
            
        Returns:
            ProjectStatistics object
        """
        try:
            query = self.db.query(Project)
            
            if organization_id:
                query = query.filter(Project.organization_id == organization_id)
            
            all_projects = query.all()
            
            total_projects = len(all_projects)
            active_projects = len([p for p in all_projects if p.status == "active"])
            completed_projects = len([p for p in all_projects if p.status == "completed"])
            on_hold_projects = len([p for p in all_projects if p.status == "on_hold"])
            overdue_projects = len([p for p in all_projects if p.is_overdue])
            
            # Calculate average progress
            if total_projects > 0:
                total_progress = sum(p.progress_percentage for p in all_projects)
                average_progress = total_progress / total_projects
            else:
                average_progress = 0.0
            
            return ProjectStatistics(
                total_projects=total_projects,
                active_projects=active_projects,
                completed_projects=completed_projects,
                overdue_projects=overdue_projects,
                on_hold_projects=on_hold_projects,
                average_progress=round(average_progress, 1)
            )
            
        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return ProjectStatistics(
                total_projects=0,
                active_projects=0,
                completed_projects=0,
                overdue_projects=0,
                on_hold_projects=0,
                average_progress=0.0
            )
    
    def archive_project(self, project_id: UUID) -> bool:
        """
        Archive a project (soft delete equivalent for projects).
        
        Args:
            project_id: Project ID
            
        Returns:
            True if project archived successfully
            
        Raises:
            NotFoundException: If project not found
            ServiceException: If archival fails
        """
        try:
            project = self.get_by_id_or_raise(project_id)
            
            # Archive project
            old_status = project.status
            project.status = "archived"
            project.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Audit log
            self.audit_log("project_archived", project_id, {
                "name": project.name,
                "old_status": old_status,
                "archived_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Project archived: {project.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving project: {e}")
            raise ServiceException("Failed to archive project")
    
    def validate_project_data(self, project_data: ProjectCreate) -> bool:
        """
        Validate project creation data.
        
        Args:
            project_data: Project creation data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if not project_data.name:
            raise ValidationException("Project name is required")
        
        if len(project_data.name) < 2:
            raise ValidationException("Project name must be at least 2 characters long")
        
        if len(project_data.name) > 255:
            raise ValidationException("Project name must be less than 255 characters")
        
        if project_data.description and len(project_data.description) > 2000:
            raise ValidationException("Project description must be less than 2000 characters")
        
        if project_data.start_date and project_data.end_date:
            if project_data.end_date < project_data.start_date:
                raise ValidationException("End date must be after start date")
        
        if project_data.start_date and project_data.expected_completion:
            if project_data.expected_completion < project_data.start_date:
                raise ValidationException("Expected completion must be after start date")
        
        if not (0 <= project_data.progress_percentage <= 100):
            raise ValidationException("Progress percentage must be between 0 and 100")
        
        return True

    def validate_project_update_data(self, project_data: ProjectUpdate) -> bool:
        """
        Validate project update data.
        
        Args:
            project_data: Project update data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if project_data.name is not None:
            if not project_data.name:
                raise ValidationException("Project name cannot be empty")
            
            if len(project_data.name) < 2:
                raise ValidationException("Project name must be at least 2 characters long")
            
            if len(project_data.name) > 255:
                raise ValidationException("Project name must be less than 255 characters")
        
        if project_data.description is not None and len(project_data.description) > 2000:
            raise ValidationException("Project description must be less than 2000 characters")
        
        if project_data.start_date and project_data.end_date:
            if project_data.end_date < project_data.start_date:
                raise ValidationException("End date must be after start date")
        
        if project_data.start_date and project_data.expected_completion:
            if project_data.expected_completion < project_data.start_date:
                raise ValidationException("Expected completion must be after start date")
        
        if project_data.progress_percentage is not None:
            if not (0 <= project_data.progress_percentage <= 100):
                raise ValidationException("Progress percentage must be between 0 and 100")
        
        return True 