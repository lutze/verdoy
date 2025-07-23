"""
Tests for project management API endpoints.

This module tests the project management endpoints:
- Project CRUD operations (create, read, update, delete/archive)
- Project status and progress management
- Project filtering and statistics
- Content negotiation for HTML and JSON responses
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import date, datetime, timedelta


class TestProjectEndpoints:
    """Test suite for project management API endpoints."""

    def test_list_projects_success_json(self, authenticated_client: TestClient):
        """Test successful projects list retrieval for JSON API."""
        # Act
        response = authenticated_client.get(
            "/api/v1/projects",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "projects" in data["data"]

    def test_list_projects_html(self, authenticated_client: TestClient):
        """Test projects list page for HTML clients."""
        # Act
        response = authenticated_client.get(
            "/app/projects",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Projects" in response.text

    def test_list_projects_with_organization_filter(self, authenticated_client: TestClient, test_organization):
        """Test projects list with organization filter."""
        # Act
        response = authenticated_client.get(
            f"/api/v1/projects?organization_id={test_organization.id}",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data["data"]

    def test_list_projects_with_status_filter(self, authenticated_client: TestClient):
        """Test projects list with status filter."""
        # Act
        response = authenticated_client.get(
            "/api/v1/projects?status=active",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data["data"]

    def test_list_projects_unauthorized(self, client: TestClient):
        """Test projects list without authentication fails."""
        # Act
        response = client.get("/api/v1/projects")
        
        # Assert
        assert response.status_code == 401

    def test_create_project_page_html(self, authenticated_client: TestClient):
        """Test create project page loads for HTML clients."""
        # Act
        response = authenticated_client.get(
            "/app/projects/create",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Create Project" in response.text

    def test_create_project_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful project creation via JSON API."""
        # Arrange
        project_data = {
            "name": f"Test Project {uuid4().hex[:8]}",
            "description": "Test project for API testing",
            "organization_id": str(test_organization.id),
            "status": "active",
            "priority": "high",
            "start_date": date.today().isoformat(),
            "expected_completion": (date.today() + timedelta(days=30)).isoformat(),
            "budget": "$10,000",
            "tags": ["testing", "api", "automation"],
            "project_metadata": {"test_type": "unit"},
            "settings": {"notifications": True}
        }
        
        # Act
        response = authenticated_client.post("/api/v1/projects", json=project_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project" in data["data"]
        assert data["data"]["project"]["name"] == project_data["name"]
        assert data["data"]["project"]["status"] == project_data["status"]
        assert data["data"]["project"]["priority"] == project_data["priority"]

    def test_create_project_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful project creation via HTML form."""
        # Arrange
        project_data = {
            "name": f"HTML Test Project {uuid4().hex[:8]}",
            "description": "Test project for HTML form testing",
            "organization_id": str(test_organization.id),
            "status": "active",
            "priority": "medium",
            "start_date": date.today().isoformat(),
            "budget": "$5,000",
            "tags": "html,testing,form"
        }
        
        # Act
        response = authenticated_client.post(
            "/app/projects/create",
            data=project_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 303  # Redirect after successful creation
        assert "location" in response.headers
        assert "/app/projects/" in response.headers["location"]

    def test_create_project_invalid_data(self, authenticated_client: TestClient, test_organization):
        """Test project creation with invalid data fails."""
        # Arrange
        project_data = {
            "name": "",  # Empty name should fail
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/projects", json=project_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_project_invalid_organization(self, authenticated_client: TestClient):
        """Test project creation with invalid organization ID fails."""
        # Arrange
        project_data = {
            "name": "Test Project",
            "organization_id": str(uuid4()),  # Non-existent organization
            "status": "active"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/projects", json=project_data)
        
        # Assert
        assert response.status_code == 404  # Organization not found

    def test_create_project_invalid_dates(self, authenticated_client: TestClient, test_organization):
        """Test project creation with invalid date ranges fails."""
        # Arrange
        project_data = {
            "name": "Test Project",
            "organization_id": str(test_organization.id),
            "start_date": date.today().isoformat(),
            "end_date": (date.today() - timedelta(days=5)).isoformat(),  # End before start
            "status": "active"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/projects", json=project_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_project_unauthorized(self, client: TestClient, test_organization):
        """Test project creation without authentication fails."""
        # Arrange
        project_data = {
            "name": "Unauthorized Project",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        
        # Act
        response = client.post("/api/v1/projects", json=project_data)
        
        # Assert
        assert response.status_code == 401

    def test_get_project_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful project retrieval via JSON API."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Get",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Act
        response = authenticated_client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project" in data["data"]
        assert data["data"]["project"]["id"] == project_id
        assert data["data"]["project"]["name"] == project_data["name"]

    def test_get_project_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful project detail page for HTML clients."""
        # Arrange - Create a project first
        project_data = {
            "name": "HTML Test Project for Get",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Act
        response = authenticated_client.get(
            f"/app/projects/{project_id}",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert project_data["name"] in response.text

    def test_get_project_not_found(self, authenticated_client: TestClient):
        """Test project retrieval with invalid ID fails."""
        # Act
        response = authenticated_client.get(f"/api/v1/projects/{uuid4()}")
        
        # Assert
        assert response.status_code == 404

    def test_edit_project_page_html(self, authenticated_client: TestClient, test_organization):
        """Test edit project page loads for HTML clients."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Edit Page",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Act
        response = authenticated_client.get(
            f"/app/projects/{project_id}/edit",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Edit Project" in response.text
        assert project_data["name"] in response.text

    def test_update_project_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful project update via JSON API."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Update",
            "organization_id": str(test_organization.id),
            "status": "active",
            "progress_percentage": 25
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "status": "on_hold",
            "progress_percentage": 50
        }
        
        # Act
        response = authenticated_client.put(
            f"/api/v1/projects/{project_id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project" in data["data"]
        assert data["data"]["project"]["name"] == update_data["name"]
        assert data["data"]["project"]["status"] == update_data["status"]
        assert data["data"]["project"]["progress_percentage"] == update_data["progress_percentage"]

    def test_update_project_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful project update via HTML form."""
        # Arrange - Create a project first
        project_data = {
            "name": "HTML Test Project for Update",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        update_data = {
            "name": "HTML Updated Project Name",
            "description": "HTML updated description",
            "status": "completed",
            "priority": "low",
            "progress_percentage": "100"
        }
        
        # Act
        response = authenticated_client.post(
            f"/app/projects/{project_id}/edit",
            data=update_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 303  # Redirect after successful update
        assert "location" in response.headers
        assert f"/app/projects/{project_id}" in response.headers["location"]

    def test_update_project_invalid_data(self, authenticated_client: TestClient, test_organization):
        """Test project update with invalid data fails."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Invalid Update",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        update_data = {
            "name": "",  # Empty name should fail
            "progress_percentage": 150  # Invalid percentage
        }
        
        # Act
        response = authenticated_client.put(
            f"/api/v1/projects/{project_id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_update_project_not_found(self, authenticated_client: TestClient):
        """Test project update with invalid ID fails."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        
        # Act
        response = authenticated_client.put(f"/api/v1/projects/{uuid4()}", json=update_data)
        
        # Assert
        assert response.status_code == 404

    def test_delete_project_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful project deletion (archival) via JSON API."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Delete",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Act
        response = authenticated_client.delete(f"/api/v1/projects/{project_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "project_id" in data["data"]
        assert data["data"]["project_id"] == project_id

    def test_delete_project_not_found(self, authenticated_client: TestClient):
        """Test project deletion with invalid ID fails."""
        # Act
        response = authenticated_client.delete(f"/api/v1/projects/{uuid4()}")
        
        # Assert
        assert response.status_code == 404

    def test_project_content_negotiation(self, authenticated_client: TestClient, test_organization):
        """Test content negotiation works correctly for project endpoints."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Content Negotiation",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Test JSON response
        json_response = authenticated_client.get(
            f"/app/projects/{project_id}",
            headers={"Accept": "application/json"}
        )
        assert json_response.status_code == 200
        assert json_response.headers["content-type"].startswith("application/json")
        
        # Test HTML response
        html_response = authenticated_client.get(
            f"/app/projects/{project_id}",
            headers={"Accept": "text/html"}
        )
        assert html_response.status_code == 200
        assert html_response.headers["content-type"].startswith("text/html")

    def test_project_progress_validation(self, authenticated_client: TestClient, test_organization):
        """Test project progress percentage validation."""
        # Arrange - Create a project first
        project_data = {
            "name": "Test Project for Progress",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Test invalid progress values
        invalid_progress_values = [-1, 101, 150]
        
        for invalid_progress in invalid_progress_values:
            update_data = {"progress_percentage": invalid_progress}
            response = authenticated_client.put(f"/api/v1/projects/{project_id}", json=update_data)
            assert response.status_code == 422, f"Progress {invalid_progress} should be invalid"

    def test_project_status_transitions(self, authenticated_client: TestClient, test_organization):
        """Test valid project status transitions."""
        # Arrange - Create a project
        project_data = {
            "name": "Test Project for Status",
            "organization_id": str(test_organization.id),
            "status": "active"
        }
        create_response = authenticated_client.post("/api/v1/projects", json=project_data)
        project_id = create_response.json()["data"]["project"]["id"]
        
        # Test valid status transitions
        valid_statuses = ["on_hold", "completed", "archived"]
        
        for status in valid_statuses:
            update_data = {"status": status}
            response = authenticated_client.put(f"/api/v1/projects/{project_id}", json=update_data)
            assert response.status_code == 200, f"Status transition to {status} should be valid"

    def test_project_unauthorized_access(self, client: TestClient, test_organization):
        """Test all project endpoints require authentication."""
        # Create a project ID for testing (won't actually exist without auth)
        project_id = str(uuid4())
        
        endpoints = [
            "/api/v1/projects",
            f"/api/v1/projects/{project_id}",
            "/app/projects",
            f"/app/projects/{project_id}",
            f"/app/projects/{project_id}/edit",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication" 