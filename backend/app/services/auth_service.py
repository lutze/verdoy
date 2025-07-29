"""
Authentication service for user management and security operations.

This service handles:
- User registration and account creation
- Authentication and token management
- Password hashing and verification
- User profile management
- Security operations and validation
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from uuid import UUID
import logging

from .base import BaseService
from ..models.user import User
from ..models.organization import Organization
from ..models.entity import Entity
from ..schemas.user import UserCreate, UserUpdate, UserLogin
from ..exceptions import (
    ServiceException,
    ValidationException,
    UserAlreadyExistsException,
    AuthenticationException,
    InactiveUserException
)
from ..utils.auth_utils import create_access_token, verify_password

logger = logging.getLogger(__name__)


class AuthService(BaseService[User]):
    """
    Authentication service for user management and security operations.
    
    This service provides business logic for:
    - User registration and account creation
    - Authentication and token management
    - Password security and validation
    - User profile management
    - Security operations
    """
    
    @property
    def model_class(self) -> type[User]:
        """Return the User model class."""
        return User
    
    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user account using pure entity approach.
        
        Args:
            user_data: User registration data
            
        Returns:
            The created user
            
        Raises:
            UserAlreadyExistsException: If user already exists
            ValidationException: If data validation fails
            ServiceException: If registration fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate user data
            self.validate_user_data(user_data)
            
            # Check if user already exists
            if self.user_exists_by_email(user_data.email):
                raise UserAlreadyExistsException(f"User with email {user_data.email} already exists")
            
            # Create user using pure entity approach
            user = User(
                name=user_data.name,
                description=f"User profile for {user_data.email}",
                email=user_data.email,
                hashed_password=User.hash_password(user_data.password),
                is_superuser=user_data.is_superuser or False,
                organization_id=user_data.organization_id,
                status="active"
            )
            
            # Save user and commit
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Audit log
            self.audit_log("user_registered", user.id, {
                "email": user.email,
                "name": user_data.name,
                "organization_id": str(user_data.organization_id) if user_data.organization_id else None
            })
            
            # Performance monitoring
            self.performance_monitor("user_registration", start_time)
            
            logger.info(f"User registered successfully: {user.email}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during user registration: {e}")
            raise UserAlreadyExistsException("User with this email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during user registration: {e}")
            raise ServiceException("Failed to register user")
    
    def authenticate_user(self, credentials: UserLogin) -> Dict[str, Any]:
        """
        Authenticate user and generate access token.
        
        Args:
            credentials: User login credentials
            
        Returns:
            Dictionary containing access token and user information
            
        Raises:
            AuthenticationException: If authentication fails
            InactiveUserException: If user account is inactive
            ServiceException: If authentication process fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Find user by email
            user = self.get_user_by_email(credentials.email)
            if not user:
                raise AuthenticationException("Invalid email or password")
            
            # Verify password
            if not user.verify_password(credentials.password):
                raise AuthenticationException("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise InactiveUserException("User account is deactivated")
            
            # Generate access token
            access_token_expires = timedelta(minutes=30)  # 30 minutes
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email},
                expires_delta=access_token_expires
            )
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Audit log
            self.audit_log("user_login", user.id, {
                "email": user.email,
                "login_time": datetime.utcnow().isoformat()
            })
            
            # Performance monitoring
            self.performance_monitor("user_authentication", start_time)
            
            logger.info(f"User authenticated successfully: {user.email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 30 * 60,  # 30 minutes in seconds
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "organization_id": user.organization_id,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error during user authentication: {e}")
            raise ServiceException("Authentication failed")
    
    def refresh_token(self, user_id: UUID) -> Dict[str, Any]:
        """
        Refresh access token for authenticated user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary containing new access token and user information
            
        Raises:
            NotFoundException: If user not found
            InactiveUserException: If user account is inactive
            ServiceException: If token refresh fails
        """
        try:
            # Get user
            user = self.get_by_id_or_raise(user_id)
            
            # Check if user is active
            if not user.is_active:
                raise InactiveUserException("User account is deactivated")
            
            # Generate new access token
            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email},
                expires_delta=access_token_expires
            )
            
            # Audit log
            self.audit_log("token_refreshed", user.id, {
                "email": user.email,
                "refresh_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Token refreshed for user: {user.email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 30 * 60,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "organization_id": user.organization_id,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error during token refresh: {e}")
            raise ServiceException("Token refresh failed")
    
    def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> User:
        """
        Update user profile information.
        
        Args:
            user_id: The user ID
            user_data: Updated user data
            
        Returns:
            The updated user
            
        Raises:
            NotFoundException: If user not found
            ValidationException: If data validation fails
            ServiceException: If update fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Get user
            user = self.get_by_id_or_raise(user_id)
            
            # Validate update data
            self.validate_update_data(user_data)
            
            # Update user name if provided
            if user_data.name:
                user.name = user_data.name
                user.updated_at = datetime.utcnow()
            
            # Update organization_id if provided
            if user_data.organization_id is not None:  # Allow setting to None to remove from organization
                user.organization_id = user_data.organization_id
                user.updated_at = datetime.utcnow()
            
            # Update password if provided (only if password field exists in schema)
            if hasattr(user_data, 'password') and user_data.password:
                user.hashed_password = User.hash_password(user_data.password)
            
            # Save changes
            self.db.commit()
            self.db.refresh(user)
            
            # Audit log
            self.audit_log("profile_updated", user.id, {
                "email": user.email,
                "updated_fields": list(user_data.dict(exclude_unset=True).keys())
            })
            
            # Performance monitoring
            self.performance_monitor("profile_update", start_time)
            
            logger.info(f"User profile updated: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise ServiceException("Failed to update user profile")
    
    def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: The user ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            NotFoundException: If user not found
            AuthenticationException: If current password is incorrect
            ValidationException: If new password validation fails
            ServiceException: If password change fails
        """
        try:
            # Get user
            user = self.get_by_id_or_raise(user_id)
            
            # Verify current password
            if not user.verify_password(current_password):
                raise AuthenticationException("Current password is incorrect")
            
            # Validate new password
            self.validate_password(new_password)
            
            # Update password
            user.hashed_password = User.hash_password(new_password)
            self.db.commit()
            
            # Audit log
            self.audit_log("password_changed", user.id, {
                "email": user.email,
                "change_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Password changed for user: {user.email}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing password: {e}")
            raise ServiceException("Failed to change password")
    
    def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate user account.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if user deactivated successfully
            
        Raises:
            NotFoundException: If user not found
            ServiceException: If deactivation fails
        """
        try:
            # Get user
            user = self.get_by_id_or_raise(user_id)
            
            # Deactivate user
            user.is_active = False
            user.deactivated_at = datetime.utcnow()
            self.db.commit()
            
            # Audit log
            self.audit_log("user_deactivated", user.id, {
                "email": user.email,
                "deactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User deactivated: {user.email}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deactivating user: {e}")
            raise ServiceException("Failed to deactivate user")
    
    def reactivate_user(self, user_id: UUID) -> bool:
        """
        Reactivate user account.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if user reactivated successfully
            
        Raises:
            NotFoundException: If user not found
            ServiceException: If reactivation fails
        """
        try:
            # Get user
            user = self.get_by_id_or_raise(user_id)
            
            # Reactivate user
            user.is_active = True
            user.deactivated_at = None
            self.db.commit()
            
            # Audit log
            self.audit_log("user_reactivated", user.id, {
                "email": user.email,
                "reactivation_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User reactivated: {user.email}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating user: {e}")
            raise ServiceException("Failed to reactivate user")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        try:
            return User.get_by_email(self.db, email)
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def user_exists_by_email(self, email: str) -> bool:
        """
        Check if user exists by email address.
        
        Args:
            email: User's email address
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            return User.get_by_email(self.db, email) is not None
        except Exception as e:
            logger.error(f"Error checking user existence by email: {e}")
            return False
    
    def validate_user_data(self, user_data: UserCreate) -> bool:
        """
        Validate user registration data.
        
        Args:
            user_data: User registration data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        if not user_data.email:
            raise ValidationException("Email is required")
        
        if not user_data.password:
            raise ValidationException("Password is required")
        
        if len(user_data.password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        if not user_data.name:
            raise ValidationException("Name is required")
        
        return True
    
    def validate_update_data(self, user_data: UserUpdate) -> bool:
        """
        Validate user update data.
        
        Args:
            user_data: User update data
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationException: If data validation fails
        """
        # Only validate password if the field exists and has a value
        if hasattr(user_data, 'password') and user_data.password and len(user_data.password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        return True
    
    def validate_password(self, password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password is valid
            
        Raises:
            ValidationException: If password validation fails
        """
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        # TODO: Add more password strength requirements
        # - Require uppercase letters
        # - Require lowercase letters
        # - Require numbers
        # - Require special characters
        
        return True
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for analytics.
        
        Returns:
            Dictionary containing user statistics
        """
        try:
            # Query users using entity_type filter
            total_users = self.db.query(User).filter(User.entity_type == "user").count()
            active_users = self.db.query(User).filter(
                User.entity_type == "user",
                User.is_active == True
            ).count()
            inactive_users = self.db.query(User).filter(
                User.entity_type == "user",
                User.is_active == False
            ).count()
            
            # Get users created in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_users = self.db.query(User).filter(
                User.entity_type == "user",
                User.created_at >= thirty_days_ago
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "new_users_30_days": new_users,
                "activation_rate": (active_users / total_users * 100) if total_users > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "inactive_users": 0,
                "new_users_30_days": 0,
                "activation_rate": 0
            } 