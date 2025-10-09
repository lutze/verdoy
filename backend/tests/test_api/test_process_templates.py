"""
Tests for Process Template rendering with entity-based data.

This module tests that process templates properly handle entity properties
and display data correctly with proper error handling for missing properties.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.entity import Entity
from app.services.process_service_entity import ProcessServiceEntity
from app.schemas.process import ProcessCreate, ProcessType, ProcessDefinition


class TestProcessTemplateRendering:
    """Test class for Process Template rendering with entity-based service."""

    def test_process_list_template_rendering(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that process list template renders correctly with entity properties."""
        # Create a process with entity-based service
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Template Test Process",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Process for template testing",
            organization_id=None,
            is_template=False,
            definition=ProcessDefinition(
                steps=[
                    {
                        "name": "Setup",
                        "type": "setup",
                        "duration_minutes": 30,
                        "parameters": {"temperature": 25.0}
                    }
                ],
                parameters={"target_temperature": 25.0},
                estimated_duration=60,
                requirements={"equipment": ["bioreactor"]},
                expected_outcomes={"yield": "high"}
            )
        )
        process = service.create_process(process_data, test_user)
        
        # Test web endpoint (HTML response)
        response = authenticated_client.get("/app/processes/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that template contains expected content
        content = response.text
        assert "Template Test Process" in content
        assert "Process Designer" in content
        assert "Create Process" in content
        
        # Check that entity properties are displayed correctly
        assert "1.0" in content  # Version
        assert "Fermentation" in content  # Process type (formatted)
        assert "active" in content  # Status

    def test_process_detail_template_rendering(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that process detail template renders correctly with entity properties."""
        # Create a process with entity-based service
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Detail Template Test Process",
            version="2.0",
            process_type=ProcessType.PURIFICATION,
            description="Process for detail template testing",
            organization_id=None,
            is_template=True,
            definition=ProcessDefinition(
                steps=[
                    {
                        "name": "Initial Setup",
                        "type": "setup",
                        "duration_minutes": 15,
                        "parameters": {"temperature": 20.0}
                    },
                    {
                        "name": "Purification Step",
                        "type": "purification",
                        "duration_minutes": 45,
                        "parameters": {"flow_rate": 10.0}
                    }
                ],
                parameters={"target_flow_rate": 10.0},
                estimated_duration=60,
                requirements={"equipment": ["chromatography_column"]},
                expected_outcomes={"purity": "high"}
            )
        )
        process = service.create_process(process_data, test_user)
        
        # Test web endpoint (HTML response)
        response = authenticated_client.get(f"/app/processes/{process.id}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that template contains expected content
        content = response.text
        assert "Detail Template Test Process" in content
        assert "2.0" in content  # Version
        assert "Purification" in content  # Process type (formatted)
        assert "Template" in content  # Template badge
        assert "Process for detail template testing" in content  # Description
        
        # Check that entity properties are displayed in stats cards
        assert "active" in content  # Status
        assert "2" in content  # Step count
        assert "60" in content  # Estimated duration

    def test_process_create_template_rendering(self, authenticated_client: TestClient, test_user: User):
        """Test that process create template renders correctly."""
        # Test web endpoint (HTML response)
        response = authenticated_client.get("/app/processes/create")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that template contains expected content
        content = response.text
        assert "Create Process" in content
        assert "Basic Information" in content
        assert "Process Configuration" in content
        assert "Review & Create" in content
        
        # Check that form fields are present
        assert 'name="name"' in content
        assert 'name="version"' in content
        assert 'name="process_type"' in content
        assert 'name="description"' in content

    def test_process_edit_template_rendering(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that process edit template renders correctly with entity properties."""
        # Create a process with entity-based service
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Edit Template Test Process",
            version="1.5",
            process_type=ProcessType.FERMENTATION,
            description="Process for edit template testing",
            organization_id=None,
            is_template=False,
            definition=ProcessDefinition(
                steps=[],
                parameters={},
                estimated_duration=30,
                requirements={},
                expected_outcomes={}
            )
        )
        process = service.create_process(process_data, test_user)
        
        # Test web endpoint (HTML response)
        response = authenticated_client.get(f"/app/processes/{process.id}/edit")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that template contains expected content
        content = response.text
        assert "Edit Process" in content
        assert "Edit Template Test Process" in content
        assert "1.5" in content  # Version
        assert "Fermentation" in content  # Process type (formatted)
        assert "Process for edit template testing" in content  # Description
        
        # Check that form fields are pre-populated with entity properties
        assert f'value="{process.name}"' in content
        version = process.properties.get('version')
        process_type = process.properties.get('process_type')
        assert f'value="{version}"' in content
        assert f'value="{process_type}"' in content

    def test_template_error_handling_missing_properties(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that templates handle missing entity properties gracefully."""
        # Create a process entity with minimal properties
        process_entity = Entity(
            entity_type='process.definition',
            name="Minimal Process",
            description="Process with minimal properties",
            status="active",
            organization_id=None,
            properties={
                'version': '1.0',
                'process_type': 'fermentation',
                'definition': {},
                'is_template': False,
                'created_by': str(test_user.id)
            }
        )
        db_session.add(process_entity)
        db_session.commit()
        db_session.refresh(process_entity)
        
        # Test that template renders without errors even with missing properties
        response = authenticated_client.get(f"/app/processes/{process_entity.id}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that template handles missing properties gracefully
        content = response.text
        assert "Minimal Process" in content
        assert "1.0" in content  # Version should still be displayed
        assert "Fermentation" in content  # Process type should still be formatted
        assert "0" in content  # Step count should default to 0

    def test_template_entity_property_access(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that templates properly access entity properties through service layer."""
        # Create a process with comprehensive entity properties
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Comprehensive Test Process",
            version="3.0",
            process_type=ProcessType.PURIFICATION,
            description="Process with comprehensive properties",
            organization_id=None,
            is_template=True,
            definition=ProcessDefinition(
                steps=[
                    {
                        "name": "Step 1",
                        "type": "setup",
                        "duration_minutes": 10,
                        "parameters": {"temp": 25.0}
                    },
                    {
                        "name": "Step 2",
                        "type": "process",
                        "duration_minutes": 20,
                        "parameters": {"flow": 5.0}
                    },
                    {
                        "name": "Step 3",
                        "type": "cleanup",
                        "duration_minutes": 5,
                        "parameters": {"wash": True}
                    }
                ],
                parameters={"target_temp": 25.0, "target_flow": 5.0},
                estimated_duration=35,
                requirements={"equipment": ["column", "pump"], "materials": ["buffer"]},
                expected_outcomes={"purity": 0.95, "yield": 0.8}
            )
        )
        process = service.create_process(process_data, test_user)
        
        # Test list template
        list_response = authenticated_client.get("/app/processes/")
        assert list_response.status_code == 200
        list_content = list_response.text
        
        # Check that entity properties are properly converted and displayed
        assert "Comprehensive Test Process" in list_content
        assert "3.0" in list_content  # Version from properties
        assert "Purification" in list_content  # Process type from properties
        assert "Template" in list_content  # Template badge from properties
        
        # Test detail template
        detail_response = authenticated_client.get(f"/app/processes/{process.id}")
        assert detail_response.status_code == 200
        detail_content = detail_response.text
        
        # Check that all entity properties are accessible
        assert "Comprehensive Test Process" in detail_content
        assert "3.0" in detail_content  # Version
        assert "Purification" in detail_content  # Process type
        assert "Template" in detail_content  # Template badge
        assert "Process with comprehensive properties" in detail_content  # Description
        assert "3" in detail_content  # Step count (from definition.steps)
        assert "35" in detail_content  # Estimated duration (from definition.estimated_duration)

    def test_template_form_submission_with_entity_properties(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that form submission works correctly with entity-based data."""
        # Create a process first
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Form Test Process",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Process for form testing",
            organization_id=None,
            is_template=False,
            definition=ProcessDefinition(
                steps=[],
                parameters={},
                estimated_duration=60,
                requirements={},
                expected_outcomes={}
            )
        )
        process = service.create_process(process_data, test_user)
        
        # Test form submission for process update
        form_data = {
            "name": "Updated Form Test Process",
            "version": "1.1",
            "process_type": "fermentation",
            "description": "Updated description",
            "status": "active",
            "is_template": "false"
        }
        
        response = authenticated_client.post(f"/app/processes/{process.id}/edit", data=form_data)
        
        # Should redirect to process detail page
        assert response.status_code == 303
        assert f"/app/processes/{process.id}" in response.headers["location"]
        
        # Verify the update worked by checking the detail page
        detail_response = authenticated_client.get(f"/app/processes/{process.id}")
        assert detail_response.status_code == 200
        detail_content = detail_response.text
        assert "Updated Form Test Process" in detail_content
        assert "1.1" in detail_content

    def test_template_entity_property_validation(self, authenticated_client: TestClient, test_user: User):
        """Test that templates handle entity property validation correctly."""
        # Test creating process with invalid data
        invalid_form_data = {
            "name": "",  # Empty name should fail
            "version": "1.0",
            "process_type": "fermentation",
            "description": "Test process",
            "organization_id": "",
            "is_template": "false"
        }
        
        response = authenticated_client.post("/app/processes/create", data=invalid_form_data)
        
        # Should return form with error message
        assert response.status_code == 200
        content = response.text
        assert "error" in content.lower() or "invalid" in content.lower()

    def test_template_pagination_with_entity_data(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that template pagination works correctly with entity-based data."""
        # Create multiple processes
        service = ProcessServiceEntity(db_session)
        for i in range(15):
            process_data = ProcessCreate(
                name=f"Pagination Test Process {i}",
                version="1.0",
                process_type=ProcessType.FERMENTATION,
                description=f"Process {i} for pagination testing",
                organization_id=None,
                is_template=False,
                definition=ProcessDefinition(
                    steps=[],
                    parameters={},
                    estimated_duration=60,
                    requirements={},
                    expected_outcomes={}
                )
            )
            service.create_process(process_data, test_user)
        
        # Test first page
        response = authenticated_client.get("/app/processes/?page=1&per_page=10")
        assert response.status_code == 200
        content = response.text
        assert "Pagination Test Process 0" in content
        assert "Pagination Test Process 9" in content
        
        # Test second page
        response = authenticated_client.get("/app/processes/?page=2&per_page=10")
        assert response.status_code == 200
        content = response.text
        assert "Pagination Test Process 10" in content
        assert "Pagination Test Process 14" in content

    def test_template_search_with_entity_data(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that template search works correctly with entity-based data."""
        # Create processes with searchable content
        service = ProcessServiceEntity(db_session)
        
        searchable_data = ProcessCreate(
            name="Unique Searchable Process",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="This process has unique searchable content",
            organization_id=None,
            is_template=False,
            definition=ProcessDefinition(
                steps=[],
                parameters={},
                estimated_duration=60,
                requirements={},
                expected_outcomes={}
            )
        )
        service.create_process(searchable_data, test_user)
        
        # Test search by name
        response = authenticated_client.get("/app/processes/?search=Unique")
        assert response.status_code == 200
        content = response.text
        assert "Unique Searchable Process" in content
        
        # Test search by description
        response = authenticated_client.get("/app/processes/?search=unique content")
        assert response.status_code == 200
        content = response.text
        assert "Unique Searchable Process" in content
