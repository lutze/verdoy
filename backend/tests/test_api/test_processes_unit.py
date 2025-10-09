"""
Unit tests for Process API endpoints with entity-based service.

This module tests the process API routes using mocks to avoid database setup issues.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

from app.schemas.process import ProcessCreate, ProcessType, ProcessDefinition, ProcessInstanceCreate


class TestProcessAPIUnit:
    """Unit test class for Process API endpoints with mocked dependencies."""

    def test_create_process_api_unit(self):
        """Test creating a process via API with mocked service."""
        # Setup mocks
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.organization_id = None
        
        mock_service = Mock()
        mock_process = Mock()
        mock_process.id = uuid4()
        mock_process.name = "Test Process"
        mock_process.version = "1.0"
        mock_process.process_type = "fermentation"
        mock_process.status = "active"
        mock_process.created_at = "2024-01-01T12:00:00Z"
        mock_process.updated_at = "2024-01-01T12:00:00Z"
        mock_service.create_process.return_value = mock_process
        mock_service._entity_to_process_dict.return_value = {
            "id": str(mock_process.id),
            "name": "Test Process",
            "version": "1.0",
            "process_type": "fermentation",
            "status": "active",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        
        # Create test app with dependency overrides
        from fastapi import FastAPI
        from app.routers.processes import router
        from app.database import get_db
        from app.dependencies import get_current_user
        
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        client = TestClient(app)
        
        # Test data
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
        
        # Mock the service class
        with patch('app.routers.processes.ProcessServiceEntity') as mock_service_class:
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.post("/api/v1/processes/", json=process_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == process_data["name"]
            assert data["version"] == process_data["version"]
            assert data["process_type"] == process_data["process_type"]
            assert data["status"] == "active"
            assert "id" in data
            
            # Verify service was called correctly
            mock_service_class.assert_called_once_with(mock_db)
            mock_service.create_process.assert_called_once()
            mock_service._entity_to_process_dict.assert_called_once_with(mock_process)

    def test_get_process_api_unit(self):
        """Test retrieving a process via API with mocked service."""
        # Setup mocks
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.organization_id = None
        
        mock_service = Mock()
        mock_process = Mock()
        mock_process.id = uuid4()
        mock_process.name = "Test Process"
        mock_service.get_process.return_value = mock_process
        mock_service._entity_to_process_dict.return_value = {
            "id": str(mock_process.id),
            "name": "Test Process",
            "version": "1.0",
            "process_type": "fermentation",
            "status": "active",
            "step_count": 3,
            "estimated_duration": 60
        }
        
        # Create test app with dependency overrides
        from fastapi import FastAPI
        from app.routers.processes import router
        from app.database import get_db
        from app.dependencies import get_current_user
        
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        client = TestClient(app)
        
        # Test data
        process_id = uuid4()
        
        # Mock the service class
        with patch('app.routers.processes.ProcessServiceEntity') as mock_service_class:
            mock_service_class.return_value = mock_service
            
            # Make request
            response = client.get(f"/api/v1/processes/{process_id}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(process_id)
            assert data["name"] == "Test Process"
            assert "step_count" in data
            assert "estimated_duration" in data
            
            # Verify service was called correctly
            mock_service_class.assert_called_once_with(mock_db)
            mock_service.get_process.assert_called_once_with(process_id, mock_user)
            mock_service._entity_to_process_dict.assert_called_once_with(mock_process)

    def test_process_api_error_handling_unit(self):
        """Test error handling in process API endpoints with mocked service."""
        # Setup mocks
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.organization_id = None
        
        mock_service = Mock()
        from app.exceptions import NotFoundException
        mock_service.get_process.side_effect = NotFoundException("Process not found")
        
        # Create test app with dependency overrides
        from fastapi import FastAPI
        from app.routers.processes import router
        from app.database import get_db
        from app.dependencies import get_current_user
        
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        client = TestClient(app)
        
        # Mock the service class
        with patch('app.routers.processes.ProcessServiceEntity') as mock_service_class:
            mock_service_class.return_value = mock_service
            
            # Test getting non-existent process
            fake_id = uuid4()
            response = client.get(f"/api/v1/processes/{fake_id}")
            assert response.status_code == 404
            
            # Verify service was called correctly
            mock_service_class.assert_called_once_with(mock_db)
            mock_service.get_process.assert_called_once_with(fake_id, mock_user)

    def test_process_api_validation_errors_unit(self):
        """Test validation error handling in process API endpoints."""
        # Setup mocks
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.organization_id = None
        
        # Create test app with dependency overrides
        from fastapi import FastAPI
        from app.routers.processes import router
        from app.database import get_db
        from app.dependencies import get_current_user
        
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        client = TestClient(app)
        
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
        
        response = client.post("/api/v1/processes/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_process_api_backward_compatibility_unit(self):
        """Test that API responses maintain backward compatibility."""
        # Setup mocks
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.organization_id = None
        
        mock_service = Mock()
        mock_process = Mock()
        mock_process.id = uuid4()
        mock_service.create_process.return_value = mock_process
        mock_service._entity_to_process_dict.return_value = {
            "id": str(mock_process.id),
            "name": "Backward Compatibility Test",
            "version": "1.0",
            "process_type": "fermentation",
            "description": "Test for backward compatibility",
            "status": "active",
            "organization_id": None,
            "created_by": str(mock_user.id),
            "is_template": False,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "step_count": 3,
            "estimated_duration": 60
        }
        
        # Create test app with dependency overrides
        from fastapi import FastAPI
        from app.routers.processes import router
        from app.database import get_db
        from app.dependencies import get_current_user
        
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        client = TestClient(app)
        
        # Test data
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
        
        # Mock the service class
        with patch('app.routers.processes.ProcessServiceEntity') as mock_service_class:
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/v1/processes/", json=process_data)
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
