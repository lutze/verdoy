"""
Dependency injection for LMS Core API.

This module provides dependency injection functions for database sessions,
authentication, and other common dependencies used across the application.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import UUID

from .config import settings
from .database import get_db
from .exceptions import CredentialsException, TokenExpiredException
from .utils.auth_utils import create_access_token, verify_password, decode_access_token

# Import service layer
from .services import (
    AuthService,
    DeviceService,
    ReadingService,
    CommandService,
    AnalyticsService,
    AlertService,
    OrganizationService,
    BillingService,
    CacheService,
    NotificationService,
    BackgroundService,
    WebSocketService
)

# Security scheme for JWT tokens
security = HTTPBearer()

device_security = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        User data from token
        
    Raises:
        CredentialsException: If token is invalid
        TokenExpiredException: If token has expired
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
        
        # TODO: Add user validation from database
        # user = crud.user.get(db, id=user_id)
        # if user is None:
        #     raise CredentialsException()
        
        return payload
    except JWTError:
        raise CredentialsException()


def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user data
        
    Raises:
        HTTPException: If user is inactive
    """
    # TODO: Add user status validation
    # if not current_user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Inactive user"
    #     )
    return current_user


def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current admin user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Admin user data
        
    Raises:
        HTTPException: If user is not admin
    """
    # TODO: Add admin role validation
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Get optional user (for endpoints that work with or without authentication).
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        User data if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except (CredentialsException, TokenExpiredException):
        return None


# Service Layer Dependencies

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Get authentication service instance.
    
    Args:
        db: Database session
        
    Returns:
        AuthService instance
    """
    return AuthService(db)


def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    """
    Get device service instance.
    
    Args:
        db: Database session
        
    Returns:
        DeviceService instance
    """
    return DeviceService(db)


def get_reading_service(db: Session = Depends(get_db)) -> ReadingService:
    """
    Get reading service instance.
    
    Args:
        db: Database session
        
    Returns:
        ReadingService instance
    """
    return ReadingService(db)


def get_command_service(db: Session = Depends(get_db)) -> CommandService:
    """
    Get command service instance.
    
    Args:
        db: Database session
        
    Returns:
        CommandService instance
    """
    return CommandService(db)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """
    Get analytics service instance.
    
    Args:
        db: Database session
        
    Returns:
        AnalyticsService instance
    """
    return AnalyticsService(db)


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    """
    Get alert service instance.
    
    Args:
        db: Database session
        
    Returns:
        AlertService instance
    """
    return AlertService(db)


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """
    Get organization service instance.
    
    Args:
        db: Database session
        
    Returns:
        OrganizationService instance
    """
    return OrganizationService(db)


def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    """
    Get billing service instance.
    
    Args:
        db: Database session
        
    Returns:
        BillingService instance
    """
    return BillingService(db)


def get_cache_service() -> CacheService:
    """
    Get cache service instance.
    
    Returns:
        CacheService instance
    """
    return CacheService()


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """
    Get notification service instance.
    
    Args:
        db: Database session
        
    Returns:
        NotificationService instance
    """
    return NotificationService(db)


def get_background_service() -> BackgroundService:
    """
    Get background service instance.
    
    Returns:
        BackgroundService instance
    """
    return BackgroundService()


def get_websocket_service() -> WebSocketService:
    """
    Get WebSocket service instance.
    
    Returns:
        WebSocketService instance
    """
    return WebSocketService()


def get_rate_limit_dependency():
    """
    Rate limiting dependency.
    
    TODO: Implement rate limiting logic
    """
    # TODO: Implement rate limiting
    pass


def get_file_size_validator():
    """
    File size validation dependency.
    
    Returns:
        Function to validate file size
    """
    def validate_file_size(file_size: int):
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        return file_size
    
    return validate_file_size


def get_file_type_validator():
    """
    File type validation dependency.
    
    Returns:
        Function to validate file type
    """
    def validate_file_type(file_extension: str):
        if file_extension.lower() not in settings.allowed_file_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_file_types)}"
            )
        return file_extension
    
    return validate_file_type


def authenticate_device(
    device_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(device_security),
    db: Session = Depends(get_db)
):
    """
    Authenticate a device using its API key (Bearer token).
    Args:
        device_id: Device UUID from path
        credentials: HTTP Bearer credentials (API key)
        db: Database session
    Returns:
        Device object if authenticated
    Raises:
        HTTPException 401 if API key is invalid
        HTTPException 404 if device not found
    """
    from app.models.device import Device
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    api_key = credentials.credentials
    stored_key = None
    # Device properties may be a dict or JSONB
    if hasattr(device, 'properties') and device.properties:
        stored_key = device.properties.get('api_key')
    if not stored_key or stored_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid device API key")
    return device 