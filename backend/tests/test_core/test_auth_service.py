"""
Tests for AuthService - Authentication and user management.

This module tests the fully implemented AuthService functionality:
- User registration
- User authentication
- Token management
- Password operations
- User profile management
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserLogin
from app.exceptions import (
    UserAlreadyExistsException,
    AuthenticationException,
    ValidationException,
    ServiceException
)


class TestAuthService:
    """Test suite for AuthService functionality."""

    def test_register_user_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user registration."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        
        # Act
        user = auth_service.register_user(user_create)
        
        # Assert
        assert user is not None
        assert user.email == test_user_data["email"]
        assert user.is_active is True
        assert user.hashed_password is not None
        assert user.hashed_password != test_user_data["password"]  # Password should be hashed
        assert user.created_at is not None

    def test_register_user_duplicate_email(self, auth_service: AuthService, test_user_data: dict):
        """Test user registration with duplicate email fails."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        auth_service.register_user(user_create)  # First registration
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsException):
            auth_service.register_user(user_create)  # Second registration should fail

    def test_register_user_invalid_email(self, auth_service: AuthService, test_user_data: dict):
        """Test user registration with invalid email fails."""
        # Arrange
        test_user_data["email"] = "invalid-email"
        user_create = UserCreate(**test_user_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.register_user(user_create)

    def test_register_user_weak_password(self, auth_service: AuthService, test_user_data: dict):
        """Test user registration with weak password fails."""
        # Arrange
        test_user_data["password"] = "weak"
        user_create = UserCreate(**test_user_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.register_user(user_create)

    def test_authenticate_user_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user authentication."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        login_data = UserLogin(
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        # Act
        result = auth_service.authenticate_user(login_data)
        
        # Assert
        assert result is not None
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        assert "expires_in" in result
        assert result["expires_in"] == 30 * 60  # 30 minutes
        assert "user" in result
        assert result["user"]["id"] == user.id
        assert result["user"]["email"] == user.email

    def test_authenticate_user_invalid_email(self, auth_service: AuthService):
        """Test authentication with invalid email fails."""
        # Arrange
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="TestPassword123!"
        )
        
        # Act & Assert
        with pytest.raises(AuthenticationException):
            auth_service.authenticate_user(login_data)

    def test_authenticate_user_invalid_password(self, auth_service: AuthService, test_user_data: dict):
        """Test authentication with invalid password fails."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        auth_service.register_user(user_create)
        
        login_data = UserLogin(
            email=test_user_data["email"],
            password="WrongPassword123!"
        )
        
        # Act & Assert
        with pytest.raises(AuthenticationException):
            auth_service.authenticate_user(login_data)

    def test_authenticate_user_inactive_account(self, auth_service: AuthService, test_user_data: dict):
        """Test authentication with inactive account fails."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        # Deactivate user
        auth_service.deactivate_user(user.id)
        
        login_data = UserLogin(
            email=test_user_data["email"],
            password=test_user_data["password"]
        )
        
        # Act & Assert
        with pytest.raises(AuthenticationException):
            auth_service.authenticate_user(login_data)

    def test_refresh_token_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful token refresh."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        # Act
        result = auth_service.refresh_token(user.id)
        
        # Assert
        assert result is not None
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        assert "expires_in" in result

    def test_get_user_by_email_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user retrieval by email."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        created_user = auth_service.register_user(user_create)
        
        # Act
        user = auth_service.get_user_by_email(test_user_data["email"])
        
        # Assert
        assert user is not None
        assert user.id == created_user.id
        assert user.email == test_user_data["email"]

    def test_get_user_by_email_not_found(self, auth_service: AuthService):
        """Test user retrieval by non-existent email returns None."""
        # Act
        user = auth_service.get_user_by_email("nonexistent@example.com")
        
        # Assert
        assert user is None

    def test_user_exists_by_email_true(self, auth_service: AuthService, test_user_data: dict):
        """Test user existence check returns True for existing user."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        auth_service.register_user(user_create)
        
        # Act
        exists = auth_service.user_exists_by_email(test_user_data["email"])
        
        # Assert
        assert exists is True

    def test_user_exists_by_email_false(self, auth_service: AuthService):
        """Test user existence check returns False for non-existent user."""
        # Act
        exists = auth_service.user_exists_by_email("nonexistent@example.com")
        
        # Assert
        assert exists is False

    def test_update_user_profile_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user profile update."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        update_data = UserUpdate(
            name="Updated Name",
            email="updated@example.com"
        )
        
        # Act
        updated_user = auth_service.update_user_profile(user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "updated@example.com"

    def test_change_password_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful password change."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        new_password = "NewPassword123!"
        
        # Act
        success = auth_service.change_password(
            user.id,
            test_user_data["password"],
            new_password
        )
        
        # Assert
        assert success is True
        
        # Verify new password works
        login_data = UserLogin(
            email=test_user_data["email"],
            password=new_password
        )
        result = auth_service.authenticate_user(login_data)
        assert result is not None

    def test_change_password_invalid_current(self, auth_service: AuthService, test_user_data: dict):
        """Test password change with invalid current password fails."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        # Act & Assert
        with pytest.raises(AuthenticationException):
            auth_service.change_password(
                user.id,
                "WrongPassword123!",
                "NewPassword123!"
            )

    def test_deactivate_user_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user deactivation."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        
        # Act
        success = auth_service.deactivate_user(user.id)
        
        # Assert
        assert success is True
        
        # Verify user is deactivated
        updated_user = auth_service.get_by_id(user.id)
        assert updated_user.is_active is False

    def test_reactivate_user_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user reactivation."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        user = auth_service.register_user(user_create)
        auth_service.deactivate_user(user.id)
        
        # Act
        success = auth_service.reactivate_user(user.id)
        
        # Assert
        assert success is True
        
        # Verify user is reactivated
        updated_user = auth_service.get_by_id(user.id)
        assert updated_user.is_active is True

    def test_get_user_statistics(self, auth_service: AuthService, test_user_data: dict):
        """Test user statistics retrieval."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        auth_service.register_user(user_create)
        
        # Act
        stats = auth_service.get_user_statistics()
        
        # Assert
        assert stats is not None
        assert "total_users" in stats
        assert "active_users" in stats
        assert "inactive_users" in stats
        assert stats["total_users"] >= 1
        assert stats["active_users"] >= 1

    def test_validate_user_data_success(self, auth_service: AuthService, test_user_data: dict):
        """Test successful user data validation."""
        # Arrange
        user_create = UserCreate(**test_user_data)
        
        # Act
        result = auth_service.validate_user_data(user_create)
        
        # Assert
        assert result is True

    def test_validate_user_data_invalid_email(self, auth_service: AuthService, test_user_data: dict):
        """Test user data validation with invalid email fails."""
        # Arrange
        test_user_data["email"] = "invalid-email"
        user_create = UserCreate(**test_user_data)
        
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_user_data(user_create)

    def test_validate_password_success(self, auth_service: AuthService):
        """Test successful password validation."""
        # Act
        result = auth_service.validate_password("StrongPassword123!")
        
        # Assert
        assert result is True

    def test_validate_password_weak(self, auth_service: AuthService):
        """Test weak password validation fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("weak")

    def test_validate_password_too_short(self, auth_service: AuthService):
        """Test password validation with too short password fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("Short1!")

    def test_validate_password_no_uppercase(self, auth_service: AuthService):
        """Test password validation without uppercase fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("lowercase123!")

    def test_validate_password_no_lowercase(self, auth_service: AuthService):
        """Test password validation without lowercase fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("UPPERCASE123!")

    def test_validate_password_no_digit(self, auth_service: AuthService):
        """Test password validation without digit fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("NoDigits!")

    def test_validate_password_no_special(self, auth_service: AuthService):
        """Test password validation without special character fails."""
        # Act & Assert
        with pytest.raises(ValidationException):
            auth_service.validate_password("NoSpecial123") 