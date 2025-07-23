"""
Tests for ProjectService - Project management and operations.

This module tests the fully implemented ProjectService functionality:
- Project creation and management
- Project lifecycle and status management
- Progress tracking and reporting
- Project statistics and analytics
- Organization-project relationships
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from app.services.project_service import ProjectService
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStatistics
from app.exceptions import (
    ProjectNotFoundException,
    OrganizationNotFoundException,
    UserNotFoundException,
    ValidationException,
    ServiceException
)


class TestProjectService:
    """Test suite for ProjectService functionality."""

    @pytest.fixture
    def project_service(self, db_session):
        """Create ProjectService instance for testing."""
        return ProjectService(db_session)

    @pytest.fixture
    def sample_project_data(self, test_organization):
        """Sample project data for testing."""
        return {
            "name": f"Test Project {uuid4().hex[:8]}",
            "description": "Test project for service testing",
            "organization_id": test_organization.id,
            "status": "active",
            "priority": "medium",
            "start_date": date.today(),
            "expected_completion": date.today() + timedelta(days=30),
            "budget": "$10,000",
            "tags": ["testing", "automation"],
            "project_metadata": {"test_type": "unit"},
            "settings": {"notifications": True}
        }

    def test_create_project_success(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test successful project creation."""
        # Arrange
        project_create = ProjectCreate(**sample_project_data)
        
        # Act
        project = project_service.create_project(project_create, test_user.id)
        
        # Assert
        assert project is not None
        assert project.name == sample_project_data["name"]
        assert project.description == sample_project_data["description"]
        assert project.organization_id == sample_project_data["organization_id"]
        assert project.status == sample_project_data["status"]
        assert project.priority == sample_project_data["priority"]
        assert project.start_date == sample_project_data["start_date"]
        assert project.expected_completion == sample_project_data["expected_completion"]
        assert project.budget == sample_project_data["budget"]
        assert project.tags == sample_project_data["tags"]
        assert project.project_metadata == sample_project_data["project_metadata"]
        assert project.settings == sample_project_data["settings"]
        assert project.project_lead_id == test_user.id
        assert project.progress_percentage == 0
        assert project.is_active is True
        assert project.created_at is not None

    def test_create_project_invalid_organization(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test project creation with invalid organization ID fails."""
        # Arrange
        sample_project_data["organization_id"] = uuid4()  # Non-existent organization
        project_create = ProjectCreate(**sample_project_data)
        
        # Act & Assert
        with pytest.raises(OrganizationNotFoundException):
            project_service.create_project(project_create, test_user.id)

    def test_create_project_invalid_project_lead(self, project_service: ProjectService, sample_project_data: dict):
        """Test project creation with invalid project lead fails."""
        # Arrange
        sample_project_data["project_lead_id"] = uuid4()  # Non-existent user
        project_create = ProjectCreate(**sample_project_data)
        
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            project_service.create_project(project_create, uuid4())

    def test_create_project_validation_error(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test project creation with validation errors."""
        # Test empty name
        sample_project_data["name"] = ""
        project_create = ProjectCreate(**sample_project_data)
        
        with pytest.raises(ValidationException):
            project_service.create_project(project_create, test_user.id)

        # Test invalid date range
        sample_project_data["name"] = "Valid Name"
        sample_project_data["start_date"] = date.today()
        sample_project_data["end_date"] = date.today() - timedelta(days=5)  # End before start
        project_create = ProjectCreate(**sample_project_data)
        
        with pytest.raises(ValidationException):
            project_service.create_project(project_create, test_user.id)

    def test_get_projects_by_organization(self, project_service: ProjectService, sample_project_data: dict, test_user, test_organization):
        """Test getting projects by organization."""
        # Arrange - Create multiple projects
        project1_data = sample_project_data.copy()
        project1_data["name"] = "Project 1"
        project1 = project_service.create_project(ProjectCreate(**project1_data), test_user.id)
        
        project2_data = sample_project_data.copy()
        project2_data["name"] = "Project 2"
        project2_data["status"] = "completed"
        project2 = project_service.create_project(ProjectCreate(**project2_data), test_user.id)
        
        # Act
        all_projects = project_service.get_projects_by_organization(test_organization.id)
        active_projects = project_service.get_projects_by_organization(test_organization.id, "active")
        completed_projects = project_service.get_projects_by_organization(test_organization.id, "completed")
        
        # Assert
        assert len(all_projects) >= 2
        assert len(active_projects) >= 1
        assert len(completed_projects) >= 1
        assert all(project.organization_id == test_organization.id for project in all_projects)

    def test_get_projects_by_user(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test getting projects by user (project lead)."""
        # Arrange - Create a project with user as lead
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        
        # Act
        user_projects = project_service.get_projects_by_user(test_user.id, "lead")
        
        # Assert
        assert len(user_projects) >= 1
        assert any(p.id == project.id for p in user_projects)
        assert all(p.project_lead_id == test_user.id for p in user_projects)

    def test_update_project_progress(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test updating project progress percentage."""
        # Arrange - Create a project
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        
        # Act
        updated_project = project_service.update_project_progress(project.id, 75)
        
        # Assert
        assert updated_project.progress_percentage == 75
        assert updated_project.status == "active"  # Should remain active

        # Test automatic completion at 100%
        completed_project = project_service.update_project_progress(project.id, 100)
        assert completed_project.progress_percentage == 100
        assert completed_project.status == "completed"
        assert completed_project.actual_completion is not None

    def test_update_project_progress_invalid(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test updating project progress with invalid values."""
        # Arrange - Create a project
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        
        # Test invalid progress values
        with pytest.raises(ValidationException):
            project_service.update_project_progress(project.id, -1)
        
        with pytest.raises(ValidationException):
            project_service.update_project_progress(project.id, 101)

    def test_get_overdue_projects(self, project_service: ProjectService, sample_project_data: dict, test_user, test_organization):
        """Test getting overdue projects."""
        # Arrange - Create an overdue project
        overdue_data = sample_project_data.copy()
        overdue_data["expected_completion"] = date.today() - timedelta(days=5)  # 5 days overdue
        overdue_data["status"] = "active"
        project_create = ProjectCreate(**overdue_data)
        overdue_project = project_service.create_project(project_create, test_user.id)
        
        # Act
        overdue_projects = project_service.get_overdue_projects(test_organization.id)
        all_overdue = project_service.get_overdue_projects()
        
        # Assert
        assert len(overdue_projects) >= 1
        assert len(all_overdue) >= 1
        assert any(p.id == overdue_project.id for p in overdue_projects)
        assert all(p.is_overdue for p in overdue_projects)

    def test_get_project_statistics(self, project_service: ProjectService, sample_project_data: dict, test_user, test_organization):
        """Test getting project statistics."""
        # Arrange - Create projects with different statuses
        statuses = ["active", "completed", "on_hold"]
        created_projects = []
        
        for i, status in enumerate(statuses):
            project_data = sample_project_data.copy()
            project_data["name"] = f"Project {i+1}"
            project_data["status"] = status
            project_data["progress_percentage"] = (i + 1) * 25  # 25%, 50%, 75%
            project_create = ProjectCreate(**project_data)
            project = project_service.create_project(project_create, test_user.id)
            created_projects.append(project)
        
        # Act
        org_stats = project_service.get_project_statistics(test_organization.id)
        global_stats = project_service.get_project_statistics()
        
        # Assert
        assert isinstance(org_stats, ProjectStatistics)
        assert isinstance(global_stats, ProjectStatistics)
        assert org_stats.total_projects >= 3
        assert org_stats.active_projects >= 1
        assert org_stats.completed_projects >= 1
        assert org_stats.on_hold_projects >= 1
        assert org_stats.average_progress > 0

    def test_archive_project(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test archiving a project."""
        # Arrange - Create a project
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        original_status = project.status
        
        # Act
        result = project_service.archive_project(project.id)
        
        # Assert
        assert result is True
        
        # Verify project is archived
        archived_project = project_service.get_by_id(project.id)
        assert archived_project.status == "archived"
        assert archived_project.updated_at > project.updated_at

    def test_archive_project_not_found(self, project_service: ProjectService):
        """Test archiving non-existent project fails."""
        # Act & Assert
        with pytest.raises(ProjectNotFoundException):
            project_service.archive_project(uuid4())

    def test_validate_project_data(self, project_service: ProjectService, sample_project_data: dict):
        """Test project data validation."""
        # Test valid data
        valid_project = ProjectCreate(**sample_project_data)
        assert project_service.validate_project_data(valid_project) is True
        
        # Test invalid name lengths
        with pytest.raises(ValidationException):
            invalid_data = sample_project_data.copy()
            invalid_data["name"] = "x"  # Too short
            project_service.validate_project_data(ProjectCreate(**invalid_data))
        
        with pytest.raises(ValidationException):
            invalid_data = sample_project_data.copy()
            invalid_data["name"] = "x" * 300  # Too long
            project_service.validate_project_data(ProjectCreate(**invalid_data))
        
        # Test invalid description length
        with pytest.raises(ValidationException):
            invalid_data = sample_project_data.copy()
            invalid_data["description"] = "x" * 2500  # Too long
            project_service.validate_project_data(ProjectCreate(**invalid_data))
        
        # Test invalid progress percentage
        with pytest.raises(ValidationException):
            invalid_data = sample_project_data.copy()
            invalid_data["progress_percentage"] = 150  # Too high
            project_service.validate_project_data(ProjectCreate(**invalid_data))

    def test_project_properties_and_methods(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test project model properties and methods."""
        # Arrange - Create projects with different statuses
        active_data = sample_project_data.copy()
        active_data["status"] = "active"
        active_project = project_service.create_project(ProjectCreate(**active_data), test_user.id)
        
        completed_data = sample_project_data.copy()
        completed_data["name"] = "Completed Project"
        completed_data["status"] = "completed"
        completed_project = project_service.create_project(ProjectCreate(**completed_data), test_user.id)
        
        overdue_data = sample_project_data.copy()
        overdue_data["name"] = "Overdue Project"
        overdue_data["expected_completion"] = date.today() - timedelta(days=1)
        overdue_data["status"] = "active"
        overdue_project = project_service.create_project(ProjectCreate(**overdue_data), test_user.id)
        
        # Assert properties
        assert active_project.is_active is True
        assert active_project.is_completed is False
        assert active_project.is_overdue is False
        
        assert completed_project.is_active is False
        assert completed_project.is_completed is True
        assert completed_project.is_overdue is False
        
        assert overdue_project.is_active is True
        assert overdue_project.is_completed is False
        assert overdue_project.is_overdue is True
        
        # Test duration calculation
        if active_project.start_date:
            duration = active_project.get_duration_days()
            assert isinstance(duration, int)
            assert duration >= 0

    def test_project_tags_management(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test project tags functionality."""
        # Arrange - Create a project
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        
        # Test adding tags
        project.add_tag("new-tag")
        assert "new-tag" in project.tags
        
        # Test duplicate tag (should not add)
        original_length = len(project.tags)
        project.add_tag("testing")  # Already exists
        assert len(project.tags) == original_length
        
        # Test removing tags
        project.remove_tag("testing")
        assert "testing" not in project.tags

    def test_project_to_dict(self, project_service: ProjectService, sample_project_data: dict, test_user):
        """Test project to_dict method."""
        # Arrange - Create a project
        project_create = ProjectCreate(**sample_project_data)
        project = project_service.create_project(project_create, test_user.id)
        
        # Act
        project_dict = project.to_dict()
        
        # Assert
        assert isinstance(project_dict, dict)
        assert "id" in project_dict
        assert "name" in project_dict
        assert "status" in project_dict
        assert "priority" in project_dict
        assert "progress_percentage" in project_dict
        assert "is_active" in project_dict
        assert "is_completed" in project_dict
        assert "is_overdue" in project_dict
        assert project_dict["name"] == project.name
        assert project_dict["status"] == project.status 