"""
Tests for authentication API endpoints.

This module tests the authentication endpoints:
- User registration
- User login
- Token refresh
- User profile management
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAuthEndpoints:
    """Test suite for authentication API endpoints."""

    def test_register_user_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration endpoint."""
        # Act
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == test_user_data["email"]
        assert "password" not in data  # Password should not be returned

    def test_register_user_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test user registration with duplicate email fails."""
        # Arrange
        client.post("/api/v1/auth/register", json=test_user_data)  # First registration
        
        # Act
        response = client.post("/api/v1/auth/register", json=test_user_data)  # Second registration
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "already exists" in data["error"].lower()

    def test_register_user_invalid_email(self, client: TestClient, test_user_data: dict):
        """Test user registration with invalid email fails."""
        # Arrange
        test_user_data["email"] = "invalid-email"
        
        # Act
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_register_user_weak_password(self, client: TestClient, test_user_data: dict):
        """Test user registration with weak password fails."""
        # Arrange
        test_user_data["password"] = "weak"
        
        # Act
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful user login endpoint."""
        # Arrange
        register_response = client.post("/api/v1/auth/register", json=test_user_data)
        print(f"Register response: {register_response.status_code}, {register_response.text}")
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"Login response: {response.status_code}, {response.text}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]

    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email fails."""
        # Arrange
        login_data = {
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_login_invalid_password(self, client: TestClient, test_user_data: dict):
        """Test login with invalid password fails."""
        # Arrange
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_refresh_token_success(self, authenticated_client: TestClient):
        """Test successful token refresh endpoint."""
        # Act
        response = authenticated_client.post("/api/v1/auth/refresh")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_refresh_token_unauthorized(self, client: TestClient):
        """Test token refresh without authentication fails."""
        # Act
        response = client.post("/api/v1/auth/refresh")
        
        # Assert
        assert response.status_code == 401

    def test_get_current_user_success(self, authenticated_client: TestClient):
        """Test successful current user retrieval endpoint."""
        # Act
        response = authenticated_client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "is_active" in data
        assert "created_at" in data

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test current user retrieval without authentication fails."""
        # Act
        response = client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 401

    def test_logout_success(self, authenticated_client: TestClient):
        """Test successful logout endpoint."""
        # Act
        response = authenticated_client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    def test_logout_unauthorized(self, client: TestClient):
        """Test logout without authentication fails."""
        # Act
        response = client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 401

    def test_change_password_success(self, authenticated_client: TestClient, test_user_data: dict):
        """Test successful password change endpoint."""
        # Arrange
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "NewPassword123!"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "password changed" in data["message"].lower()

    def test_change_password_invalid_current(self, authenticated_client: TestClient):
        """Test password change with invalid current password fails."""
        # Arrange
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_change_password_weak_new(self, authenticated_client: TestClient, test_user_data: dict):
        """Test password change with weak new password fails."""
        # Arrange
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "weak"
        }
        
        # Act
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_reset_password_request_success(self, client: TestClient, test_user_data: dict):
        """Test successful password reset request endpoint."""
        # Arrange
        client.post("/api/v1/auth/register", json=test_user_data)
        
        reset_data = {
            "email": test_user_data["email"]
        }
        
        # Act
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset" in data["message"].lower()

    def test_reset_password_request_invalid_email(self, client: TestClient):
        """Test password reset request with invalid email fails."""
        # Arrange
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        # Act
        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        # Act
        response = client.get("/api/v1/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_system_info(self, client: TestClient):
        """Test system info endpoint."""
        # Act
        response = client.get("/api/v1/health/info")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "status" in data 