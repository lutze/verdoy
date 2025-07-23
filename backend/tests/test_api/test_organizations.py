"""
Tests for organization management API endpoints.

This module tests the organization management endpoints:
- Organization CRUD operations (create, read, update, delete)
- Member management and access control
- Organization statistics and reporting
- Content negotiation for HTML and JSON responses
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4


class TestOrganizationEndpoints:
    """Test suite for organization management API endpoints."""

    def test_list_organizations_success_json(self, authenticated_client: TestClient):
        """Test successful organizations list retrieval for JSON API."""
        # Act
        response = authenticated_client.get(
            "/api/v1/organizations",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "organizations" in data["data"]

    def test_list_organizations_html(self, authenticated_client: TestClient):
        """Test organizations list page for HTML clients."""
        # Act
        response = authenticated_client.get(
            "/app/admin/organization/",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Organizations" in response.text

    def test_list_organizations_unauthorized(self, client: TestClient):
        """Test organizations list without authentication fails."""
        # Act
        response = client.get("/api/v1/organizations")
        
        # Assert
        assert response.status_code == 401

    def test_create_organization_page_html(self, authenticated_client: TestClient):
        """Test create organization page loads for HTML clients."""
        # Act
        response = authenticated_client.get(
            "/app/admin/organization/create",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Create Organization" in response.text

    def test_create_organization_success_json(self, authenticated_client: TestClient):
        """Test successful organization creation via JSON API."""
        # Arrange
        org_data = {
            "name": f"Test Org {uuid4().hex[:8]}",
            "description": "Test organization for API testing",
            "organization_type": "small_business",
            "contact_email": "test@testorg.com",
            "contact_phone": "+1-555-0123",
            "website": "https://testorg.com",
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "postal_code": "12345",
            "timezone": "UTC"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/organizations", json=org_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organization" in data["data"]
        assert data["data"]["organization"]["name"] == org_data["name"]
        assert data["data"]["organization"]["description"] == org_data["description"]

    def test_create_organization_success_html(self, authenticated_client: TestClient):
        """Test successful organization creation via HTML form."""
        # Arrange
        org_data = {
            "name": f"Test Org HTML {uuid4().hex[:8]}",
            "description": "Test organization for HTML form testing",
            "organization_type": "academic",
            "contact_email": "html@testorg.com",
            "timezone": "UTC"
        }
        
        # Act
        response = authenticated_client.post(
            "/app/admin/organization/create",
            data=org_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 303  # Redirect after successful creation
        assert "location" in response.headers
        assert "/app/admin/organization/" in response.headers["location"]

    def test_create_organization_invalid_data(self, authenticated_client: TestClient):
        """Test organization creation with invalid data fails."""
        # Arrange
        org_data = {
            "name": "",  # Empty name should fail
            "description": "Test organization",
            "organization_type": "business"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/organizations", json=org_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_organization_duplicate_name(self, authenticated_client: TestClient):
        """Test organization creation with duplicate name fails."""
        # Arrange
        org_name = f"Duplicate Org {uuid4().hex[:8]}"
        org_data = {
            "name": org_name,
            "description": "First organization",
            "organization_type": "business"
        }
        
        # Create first organization
        authenticated_client.post("/api/v1/organizations", json=org_data)
        
        # Try to create duplicate
        duplicate_data = {
            "name": org_name,
            "description": "Duplicate organization",
            "organization_type": "business"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/organizations", json=duplicate_data)
        
        # Assert
        assert response.status_code == 400  # Business logic error

    def test_create_organization_unauthorized(self, client: TestClient):
        """Test organization creation without authentication fails."""
        # Arrange
        org_data = {
            "name": "Unauthorized Org",
            "description": "Test organization",
            "organization_type": "business"
        }
        
        # Act
        response = client.post("/api/v1/organizations", json=org_data)
        
        # Assert
        assert response.status_code == 401

    def test_get_organization_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful organization retrieval via JSON API."""
        # Act
        response = authenticated_client.get(
            f"/api/v1/organizations/{test_organization.id}",
            headers={"Accept": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organization" in data["data"]
        assert data["data"]["organization"]["id"] == str(test_organization.id)
        assert data["data"]["organization"]["name"] == test_organization.name

    def test_get_organization_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful organization detail page for HTML clients."""
        # Act
        response = authenticated_client.get(
            f"/app/admin/organization/{test_organization.id}",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert test_organization.name in response.text

    def test_get_organization_not_found(self, authenticated_client: TestClient):
        """Test organization retrieval with invalid ID fails."""
        # Act
        response = authenticated_client.get(f"/api/v1/organizations/{uuid4()}")
        
        # Assert
        assert response.status_code == 404

    def test_edit_organization_page_html(self, authenticated_client: TestClient, test_organization):
        """Test edit organization page loads for HTML clients."""
        # Act
        response = authenticated_client.get(
            f"/app/admin/organization/{test_organization.id}/edit",
            headers={"Accept": "text/html"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Edit Organization" in response.text
        assert test_organization.name in response.text

    def test_update_organization_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful organization update via JSON API."""
        # Arrange
        update_data = {
            "name": f"Updated {test_organization.name}",
            "description": "Updated description",
            "contact_email": "updated@testorg.com"
        }
        
        # Act
        response = authenticated_client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organization" in data["data"]
        assert data["data"]["organization"]["name"] == update_data["name"]
        assert data["data"]["organization"]["description"] == update_data["description"]

    def test_update_organization_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful organization update via HTML form."""
        # Arrange
        update_data = {
            "name": f"HTML Updated {test_organization.name}",
            "description": "HTML updated description",
            "organization_type": "enterprise",
            "timezone": "UTC"
        }
        
        # Act
        response = authenticated_client.post(
            f"/app/admin/organization/{test_organization.id}/edit",
            data=update_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 303  # Redirect after successful update
        assert "location" in response.headers
        assert f"/app/admin/organization/{test_organization.id}" in response.headers["location"]

    def test_update_organization_invalid_data(self, authenticated_client: TestClient, test_organization):
        """Test organization update with invalid data fails."""
        # Arrange
        update_data = {
            "name": "",  # Empty name should fail
            "description": "Updated description"
        }
        
        # Act
        response = authenticated_client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_update_organization_not_found(self, authenticated_client: TestClient):
        """Test organization update with invalid ID fails."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        
        # Act
        response = authenticated_client.put(f"/api/v1/organizations/{uuid4()}", json=update_data)
        
        # Assert
        assert response.status_code == 404

    def test_delete_organization_success_json(self, authenticated_client: TestClient, test_organization):
        """Test successful organization deletion (archival) via JSON API."""
        # Act
        response = authenticated_client.delete(f"/api/v1/organizations/{test_organization.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organization_id" in data["data"]
        assert data["data"]["organization_id"] == str(test_organization.id)

    def test_delete_organization_success_html(self, authenticated_client: TestClient, test_organization):
        """Test successful organization deletion via HTML form."""
        # Arrange
        delete_data = {"confirm": "delete"}
        
        # Act
        response = authenticated_client.post(
            f"/app/admin/organization/{test_organization.id}/delete",
            data=delete_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 303  # Redirect after successful deletion
        assert "location" in response.headers
        assert "/app/admin/organization/" in response.headers["location"]

    def test_delete_organization_invalid_confirmation(self, authenticated_client: TestClient, test_organization):
        """Test organization deletion with invalid confirmation fails."""
        # Arrange
        delete_data = {"confirm": "wrong"}  # Should be "delete"
        
        # Act
        response = authenticated_client.post(
            f"/app/admin/organization/{test_organization.id}/delete",
            data=delete_data,
            headers={"Accept": "text/html"},
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 400

    def test_delete_organization_not_found(self, authenticated_client: TestClient):
        """Test organization deletion with invalid ID fails."""
        # Act
        response = authenticated_client.delete(f"/api/v1/organizations/{uuid4()}")
        
        # Assert
        assert response.status_code == 404

    def test_organization_content_negotiation(self, authenticated_client: TestClient, test_organization):
        """Test content negotiation works correctly for organization endpoints."""
        # Test JSON response
        json_response = authenticated_client.get(
            f"/app/admin/organization/{test_organization.id}",
            headers={"Accept": "application/json"}
        )
        assert json_response.status_code == 200
        assert json_response.headers["content-type"].startswith("application/json")
        
        # Test HTML response
        html_response = authenticated_client.get(
            f"/app/admin/organization/{test_organization.id}",
            headers={"Accept": "text/html"}
        )
        assert html_response.status_code == 200
        assert html_response.headers["content-type"].startswith("text/html")

    def test_organization_unauthorized_access(self, client: TestClient, test_organization):
        """Test all organization endpoints require authentication."""
        endpoints = [
            f"/api/v1/organizations/{test_organization.id}",
            f"/app/admin/organization/{test_organization.id}",
            f"/app/admin/organization/{test_organization.id}/edit",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication" 