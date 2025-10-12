"""
Dependency injection for VerdoyLab API.

This module provides dependency injection functions for database sessions,
authentication, and other common dependencies used across the application.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from jose import JWTError, jwt
from uuid import UUID
import uuid

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
    OrganizationServiceEntity,
    BillingService,
    CacheService,
    NotificationService,
    BackgroundService,
    WebSocketService
)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)  # Set auto_error=False to allow session fallback

device_security = HTTPBearer(auto_error=True)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user from JWT token or session cookie.
    
    Supports both Bearer token authentication (for API clients) and 
    session cookie authentication (for web browsers).
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials (Bearer token)
        session_token: Session token from HTTP-only cookie
        db: Database session
        
    Returns:
        User object from database
        
    Raises:
        CredentialsException: If token is invalid or missing
        TokenExpiredException: If token has expired
    """
    token = None
    
    # Try Bearer token first (for API clients)
    if credentials and credentials.credentials:
        token = credentials.credentials
    # Fall back to session cookie (for web browsers)
    elif session_token:
        token = session_token
    
    if not token:
        raise CredentialsException()
    
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
        # Convert user_id to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except Exception:
                raise CredentialsException()
        from .models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise CredentialsException()
        
        # Return user object instead of just payload
        return user
    except JWTError:
        raise CredentialsException()


def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user data
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user = Depends(get_current_user)
):
    """
    Get current admin user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Admin user data
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Get optional user (for endpoints that work with or without authentication).
    
    Args:
        request: FastAPI request object
        credentials: Optional HTTP authorization credentials
        session_token: Session token from HTTP-only cookie
        db: Database session
        
    Returns:
        User data if authenticated, None otherwise
    """
    if not credentials and not session_token:
        return None
    
    try:
        return get_current_user(request, credentials, session_token, db)
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


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationServiceEntity:
    """
    Get organization service instance.
    
    Args:
        db: Database session
        
    Returns:
        OrganizationServiceEntity instance
    """
    return OrganizationServiceEntity(db)


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


def get_api_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user for API endpoints (Bearer token only).
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials (Bearer token)
        db: Database session
    Returns:
        User object from database
    Raises:
        CredentialsException: If token is invalid, missing, or session cookie is used
    """
    if not credentials or not credentials.credentials:
        raise CredentialsException()
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
        from .models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise CredentialsException()
        return user
    except JWTError:
        raise CredentialsException()

def get_web_user(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user for web endpoints (session cookie only).
    Args:
        request: FastAPI request object
        session_token: Session token from HTTP-only cookie
        db: Database session
    Returns:
        User object from database
    Raises:
        CredentialsException: If session cookie is invalid, missing, or Bearer token is used
    """
    # Reject Bearer tokens for web endpoints
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer"):
        raise CredentialsException()
    if not session_token:
        raise CredentialsException()
    try:
        payload = decode_access_token(session_token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
        from .models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise CredentialsException()
        return user
    except JWTError:
        raise CredentialsException() 