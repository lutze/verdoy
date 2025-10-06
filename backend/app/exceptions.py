"""
Custom exceptions for VerdoyLab API.

This module defines custom exceptions and exception handlers for
consistent error handling across the application.
"""

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request


class LMSException(HTTPException):
    """Base exception for VerdoyLab API custom errors."""
    def __init__(self, detail: str = "An LMS error occurred", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class DatabaseConnectionException(HTTPException):
    """Exception raised when database connection fails."""
    def __init__(self, detail: str = "Database connection failed"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class ConfigurationException(HTTPException):
    """Exception raised when application configuration is invalid."""
    def __init__(self, detail: str = "Invalid application configuration"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class CredentialsException(HTTPException):
    """Exception raised when authentication credentials are invalid."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(HTTPException):
    """Exception raised when JWT token has expired."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(HTTPException):
    """Exception raised when JWT token is invalid."""
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsException(HTTPException):
    """Exception raised when user lacks required permissions."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ResourceNotFoundException(HTTPException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id {resource_id} not found"
        )


class ValidationException(HTTPException):
    """Exception raised when data validation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ConflictException(HTTPException):
    """Exception raised when there's a conflict with existing data."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RateLimitException(HTTPException):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class DatabaseException(HTTPException):
    """Exception raised when database operations fail."""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ExternalServiceException(HTTPException):
    """Exception raised when external service calls fail."""
    def __init__(self, service_name: str, detail: str = None):
        detail = detail or f"External service {service_name} is unavailable"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class DeviceOfflineException(HTTPException):
    """Exception raised when trying to communicate with offline device."""
    def __init__(self, device_id: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Device {device_id} is offline"
        )


class CommandTimeoutException(HTTPException):
    """Exception raised when device command times out."""
    def __init__(self, device_id: str, command_id: str):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Command {command_id} for device {device_id} timed out"
        )


class ServiceException(HTTPException):
    """Exception raised for general service layer errors."""
    def __init__(self, detail: str = "A service error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class NotFoundException(HTTPException):
    """Exception raised when a requested resource is not found (generic)."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UserAlreadyExistsException(HTTPException):
    """Exception raised when a user with the given email already exists."""
    def __init__(self, detail: str = "A user with this email already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class AuthenticationException(HTTPException):
    """Exception raised when authentication fails."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(HTTPException):
    """Exception raised when authorization fails."""
    def __init__(self, detail: str = "Authorization failed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class InactiveUserException(HTTPException):
    """Exception raised when user account is deactivated."""
    def __init__(self, detail: str = "User account is deactivated"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class UserNotFoundException(HTTPException):
    """Exception raised when a user is not found."""
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DeviceNotFoundException(HTTPException):
    """Exception raised when a device is not found."""
    def __init__(self, detail: str = "Device not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DeviceAlreadyExistsException(HTTPException):
    """Exception raised when a device with the given serial number already exists."""
    def __init__(self, detail: str = "A device with this serial number already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class DeviceAuthenticationException(HTTPException):
    """Exception raised when device authentication fails."""
    def __init__(self, detail: str = "Device authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class OrganizationAlreadyExistsException(HTTPException):
    """Exception raised when an organization with the given name already exists."""
    def __init__(self, detail: str = "An organization with this name already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class OrganizationNotFoundException(HTTPException):
    """Exception raised when an organization is not found."""
    def __init__(self, detail: str = "Organization not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ProjectNotFoundException(HTTPException):
    """Exception raised when a project is not found."""
    def __init__(self, detail: str = "Project not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ReadingNotFoundException(HTTPException):
    """Exception raised when a reading is not found."""
    def __init__(self, detail: str = "Reading not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DataProcessingException(HTTPException):
    """Exception raised when data processing fails."""
    def __init__(self, detail: str = "Data processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class AccessDeniedException(HTTPException):
    """Exception raised when access is denied to a resource."""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class CommandNotFoundException(HTTPException):
    """Exception raised when a command is not found."""
    def __init__(self, detail: str = "Command not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class SafetyException(HTTPException):
    """Exception raised when safety checks fail or safety operations are blocked."""
    def __init__(self, detail: str = "Safety check failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class PermissionException(HTTPException):
    """Exception raised when user lacks required permissions for an operation."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class BusinessLogicException(HTTPException):
    """Exception raised when business logic validation fails."""
    def __init__(self, detail: str = "Business logic validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class PermissionDeniedException(HTTPException):
    """Exception raised when user lacks required permissions."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class MemberNotFoundException(HTTPException):
    """Exception raised when a member is not found."""
    def __init__(self, detail: str = "Member not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DuplicateMemberException(HTTPException):
    """Exception raised when a user is already a member of an organization."""
    def __init__(self, detail: str = "User is already a member of this organization"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class InvitationNotFoundException(HTTPException):
    """Exception raised when an invitation is not found."""
    def __init__(self, detail: str = "Invitation not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class InvitationExpiredException(HTTPException):
    """Exception raised when an invitation has expired."""
    def __init__(self, detail: str = "Invitation has expired"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class DuplicateInvitationException(HTTPException):
    """Exception raised when an invitation already exists."""
    def __init__(self, detail: str = "Invitation already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RemovalRequestNotFoundException(HTTPException):
    """Exception raised when a removal request is not found."""
    def __init__(self, detail: str = "Removal request not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DuplicateRemovalRequestException(HTTPException):
    """Exception raised when a removal request already exists."""
    def __init__(self, detail: str = "Removal request already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
        
    Returns:
        JSONResponse with error details
    """
    # Log the exception for debugging
    print(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for HTTPException instances.
    
    Args:
        request: FastAPI request object
        exc: HTTPException that was raised
        
    Returns:
        JSONResponse with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        },
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """
    Handler for validation exceptions.
    
    Args:
        request: FastAPI request object
        exc: ValidationException that was raised
        
    Returns:
        JSONResponse with validation error details
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    ) 