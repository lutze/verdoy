"""
Tests for Process API endpoints with entity-based service.

This module tests the process API routes to ensure they work correctly
with the ProcessServiceEntity and maintain backward compatibility.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.entity import Entity
from app.models.organization import Organization
from app.services.process_service_entity import ProcessServiceEntity
from app.schemas.process import ProcessCreate, ProcessType, ProcessDefinition, ProcessUpdate, ProcessStatus


class TestProcessAPIEntity:
    """Test class for Process API endpoints with entity-based service."""

    def test_create_process_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test creating a process via API with entity-based service."""
        process_data = {
            "name": "Test Fermentation Process",
            "version": "1.0",
            "process_type": "fermentation",
            "description": "A test fermentation process",
            "organization_id": None,
            "is_template": False,
            "definition": {
                "steps": [
                    {
                        "name": "Initial Setup",
                        "type": "setup",
                        "duration_minutes": 30,
                        "parameters": {"temperature": 25.0}
                    }
                ],
                "parameters": {"target_temperature": 25.0},
                "estimated_duration": 60,
                "requirements": {"equipment": ["bioreactor"]},
                "expected_outcomes": {"yield": "high"}
            }
        }
        
        response = authenticated_client.post("/api/v1/processes/", json=process_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == process_data["name"]
        assert data["version"] == process_data["version"]
        assert data["process_type"] == process_data["process_type"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_process_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test retrieving a process via API with entity-based service."""
        # First create a process
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Retrieval",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for API retrieval",
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
        
        # Now test retrieval
        response = authenticated_client.get(f"/api/v1/processes/{process.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(process.id)
        assert data["name"] == process_data.name
        assert data["version"] == process_data.version
        assert data["process_type"] == process_data.process_type.value
        assert "step_count" in data
        assert "estimated_duration" in data

    def test_list_processes_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test listing processes via API with entity-based service."""
        # Create multiple processes
        service = ProcessServiceEntity(db_session)
        for i in range(3):
            process_data = ProcessCreate(
                name=f"Test Process {i}",
                version="1.0",
                process_type=ProcessType.FERMENTATION,
                description=f"Test process {i}",
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
        
        # Test listing
        response = authenticated_client.get("/api/v1/processes/")
        
        assert response.status_code == 200
        data = response.json()
        assert "processes" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] >= 3
        assert len(data["processes"]) >= 3

    def test_update_process_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test updating a process via API with entity-based service."""
        # First create a process
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Update",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for API update",
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
        
        # Now test update
        update_data = {
            "name": "Updated Test Process",
            "version": "1.1",
            "description": "Updated description"
        }
        
        response = authenticated_client.put(f"/api/v1/processes/{process.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["version"] == update_data["version"]
        assert data["description"] == update_data["description"]

    def test_archive_process_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test archiving a process via API with entity-based service."""
        # First create a process
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Archive",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for API archive",
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
        
        # Now test archive
        response = authenticated_client.delete(f"/api/v1/processes/{process.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"

    def test_create_process_instance_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test creating a process instance via API with entity-based service."""
        # First create a process
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Instance",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for instance creation",
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
        
        # Now test instance creation
        instance_data = {
            "process_id": str(process.id),
            "batch_id": "TEST-001",
            "parameters": {"temperature": 25.0}
        }
        
        response = authenticated_client.post("/api/v1/processes/instances", json=instance_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["process_id"] == str(process.id)
        assert data["batch_id"] == instance_data["batch_id"]
        assert data["status"] == "running"
        assert "id" in data
        assert "started_at" in data

    def test_list_process_instances_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test listing process instances via API with entity-based service."""
        # First create a process and instances
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Instances",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for instance listing",
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
        
        # Create multiple instances
        from app.schemas.process import ProcessInstanceCreate
        for i in range(3):
            instance_data = ProcessInstanceCreate(
                process_id=process.id,
                batch_id=f"TEST-{i:03d}",
                parameters={"temperature": 25.0 + i}
            )
            service.create_process_instance(instance_data, test_user)
        
        # Test listing
        response = authenticated_client.get(f"/api/v1/processes/instances?process_id={process.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "instances" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] >= 3
        assert len(data["instances"]) >= 3

    def test_get_process_instance_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test retrieving a process instance via API with entity-based service."""
        # First create a process and instance
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Instance Retrieval",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for instance retrieval",
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
        
        from app.schemas.process import ProcessInstanceCreate
        instance_data = ProcessInstanceCreate(
            process_id=process.id,
            batch_id="TEST-RETRIEVAL",
            parameters={"temperature": 25.0}
        )
        instance = service.create_process_instance(instance_data, test_user)
        
        # Test retrieval
        response = authenticated_client.get(f"/api/v1/processes/instances/{instance.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(instance.id)
        assert data["process_id"] == str(process.id)
        assert data["batch_id"] == instance_data.batch_id
        assert data["status"] == "running"
        assert "duration" in data

    def test_update_process_instance_api(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test updating a process instance via API with entity-based service."""
        # First create a process and instance
        service = ProcessServiceEntity(db_session)
        process_data = ProcessCreate(
            name="Test Process for Instance Update",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Test process for instance update",
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
        
        from app.schemas.process import ProcessInstanceCreate
        instance_data = ProcessInstanceCreate(
            process_id=process.id,
            batch_id="TEST-UPDATE",
            parameters={"temperature": 25.0}
        )
        instance = service.create_process_instance(instance_data, test_user)
        
        # Test update
        update_data = {
            "status": "completed",
            "results": {"yield": 0.85, "quality": "excellent"}
        }
        
        response = authenticated_client.put(f"/api/v1/processes/instances/{instance.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "results" in data
        assert data["results"]["yield"] == 0.85

    def test_process_api_error_handling(self, authenticated_client: TestClient, test_user: User):
        """Test error handling in process API endpoints."""
        # Test getting non-existent process
        fake_id = str(uuid4())
        response = authenticated_client.get(f"/api/v1/processes/{fake_id}")
        assert response.status_code == 404
        
        # Test updating non-existent process
        update_data = {"name": "Updated Name"}
        response = authenticated_client.put(f"/api/v1/processes/{fake_id}", json=update_data)
        assert response.status_code == 404
        
        # Test archiving non-existent process
        response = authenticated_client.delete(f"/api/v1/processes/{fake_id}")
        assert response.status_code == 404

    def test_process_api_validation_errors(self, authenticated_client: TestClient, test_user: User):
        """Test validation error handling in process API endpoints."""
        # Test creating process with invalid data
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "version": "1.0",
            "process_type": "invalid_type",  # Invalid process type
            "description": "Test process",
            "organization_id": None,
            "is_template": False,
            "definition": {
                "steps": [],
                "parameters": {},
                "estimated_duration": 60,
                "requirements": {},
                "expected_outcomes": {}
            }
        }
        
        response = authenticated_client.post("/api/v1/processes/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_process_api_pagination(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test pagination in process API endpoints."""
        # Create multiple processes
        service = ProcessServiceEntity(db_session)
        for i in range(15):
            process_data = ProcessCreate(
                name=f"Test Process {i}",
                version="1.0",
                process_type=ProcessType.FERMENTATION,
                description=f"Test process {i}",
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
        
        # Test pagination
        response = authenticated_client.get("/api/v1/processes/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert len(data["processes"]) <= 10
        
        # Test second page
        response = authenticated_client.get("/api/v1/processes/?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10

    def test_process_api_filtering(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test filtering in process API endpoints."""
        # Create processes with different types
        service = ProcessServiceEntity(db_session)
        
        # Create fermentation process
        fermentation_data = ProcessCreate(
            name="Fermentation Process",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="Fermentation process",
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
        service.create_process(fermentation_data, test_user)
        
        # Create purification process
        purification_data = ProcessCreate(
            name="Purification Process",
            version="1.0",
            process_type=ProcessType.PURIFICATION,
            description="Purification process",
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
        service.create_process(purification_data, test_user)
        
        # Test filtering by process type
        response = authenticated_client.get("/api/v1/processes/?process_type=fermentation")
        assert response.status_code == 200
        data = response.json()
        assert all(p["process_type"] == "fermentation" for p in data["processes"])
        
        # Test filtering by template status
        response = authenticated_client.get("/api/v1/processes/?is_template=false")
        assert response.status_code == 200
        data = response.json()
        assert all(p["is_template"] == False for p in data["processes"])

    def test_process_api_search(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test search functionality in process API endpoints."""
        # Create processes with searchable names
        service = ProcessServiceEntity(db_session)
        
        searchable_data = ProcessCreate(
            name="Unique Searchable Process Name",
            version="1.0",
            process_type=ProcessType.FERMENTATION,
            description="This process has a unique name for searching",
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
        response = authenticated_client.get("/api/v1/processes/?search=Unique")
        assert response.status_code == 200
        data = response.json()
        assert len(data["processes"]) >= 1
        assert any("Unique" in p["name"] for p in data["processes"])
        
        # Test search by description
        response = authenticated_client.get("/api/v1/processes/?search=unique name")
        assert response.status_code == 200
        data = response.json()
        assert len(data["processes"]) >= 1
        assert any("unique name" in p["description"].lower() for p in data["processes"])


class TestProcessAPIEntityIntegration:
    """Integration tests for Process API with entity-based service."""

    def test_process_workflow_integration(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test complete process workflow: create -> update -> create instance -> update instance."""
        # 1. Create process
        process_data = {
            "name": "Integration Test Process",
            "version": "1.0",
            "process_type": "fermentation",
            "description": "Process for integration testing",
            "organization_id": None,
            "is_template": False,
            "definition": {
                "steps": [
                    {
                        "name": "Setup",
                        "type": "setup",
                        "duration_minutes": 30,
                        "parameters": {"temperature": 25.0}
                    }
                ],
                "parameters": {"target_temperature": 25.0},
                "estimated_duration": 60,
                "requirements": {"equipment": ["bioreactor"]},
                "expected_outcomes": {"yield": "high"}
            }
        }
        
        create_response = authenticated_client.post("/api/v1/processes/", json=process_data)
        assert create_response.status_code == 200
        process = create_response.json()
        process_id = process["id"]
        
        # 2. Update process
        update_data = {
            "name": "Updated Integration Test Process",
            "version": "1.1"
        }
        
        update_response = authenticated_client.put(f"/api/v1/processes/{process_id}", json=update_data)
        assert update_response.status_code == 200
        updated_process = update_response.json()
        assert updated_process["name"] == update_data["name"]
        assert updated_process["version"] == update_data["version"]
        
        # 3. Create process instance
        instance_data = {
            "process_id": process_id,
            "batch_id": "INTEGRATION-001",
            "parameters": {"temperature": 25.0}
        }
        
        instance_response = authenticated_client.post("/api/v1/processes/instances", json=instance_data)
        assert instance_response.status_code == 200
        instance = instance_response.json()
        instance_id = instance["id"]
        
        # 4. Update process instance
        instance_update_data = {
            "status": "completed",
            "results": {"yield": 0.9, "quality": "excellent"}
        }
        
        instance_update_response = authenticated_client.put(f"/api/v1/processes/instances/{instance_id}", json=instance_update_data)
        assert instance_update_response.status_code == 200
        updated_instance = instance_update_response.json()
        assert updated_instance["status"] == "completed"
        assert updated_instance["results"]["yield"] == 0.9
        
        # 5. Verify instance appears in process instance list
        list_response = authenticated_client.get(f"/api/v1/processes/instances?process_id={process_id}")
        assert list_response.status_code == 200
        instances = list_response.json()
        assert instances["total"] >= 1
        assert any(inst["id"] == instance_id for inst in instances["instances"])

    def test_process_api_backward_compatibility(self, authenticated_client: TestClient, test_user: User, db_session: Session):
        """Test that API responses maintain backward compatibility."""
        # Create a process
        process_data = {
            "name": "Backward Compatibility Test",
            "version": "1.0",
            "process_type": "fermentation",
            "description": "Test for backward compatibility",
            "organization_id": None,
            "is_template": False,
            "definition": {
                "steps": [],
                "parameters": {},
                "estimated_duration": 60,
                "requirements": {},
                "expected_outcomes": {}
            }
        }
        
        response = authenticated_client.post("/api/v1/processes/", json=process_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present (backward compatibility)
        expected_fields = [
            "id", "name", "version", "process_type", "description", "status",
            "organization_id", "created_by", "is_template", "created_at", "updated_at",
            "step_count", "estimated_duration"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types are correct
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["process_type"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["is_template"], bool)
        assert isinstance(data["step_count"], int)
        assert isinstance(data["estimated_duration"], (int, type(None)))
