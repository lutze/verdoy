# VerdoyLab API Exception Documentation

This document provides a comprehensive overview of all custom exceptions used in the VerdoyLab API, including their HTTP status codes, default messages, and usage scenarios.

## 📊 Exception Overview

The VerdoyLab API defines **28 custom exceptions** organized by HTTP status codes and functional categories.

---

## 🔴 HTTP 400 - Bad Request

### LMSException
- **Default Message**: `"An LMS error occurred"`
- **Status Code**: 400
- **Customizable**: Yes (detail and status_code)
- **Usage**: Base exception for VerdoyLab API custom errors
- **Example**:
  ```python
  raise LMSException("Custom error message")
  raise LMSException("Error occurred", status_code=422)
  ```

---

## 🔐 HTTP 401 - Unauthorized

### CredentialsException
- **Default Message**: `"Could not validate credentials"`
- **Status Code**: 401
- **Headers**: `WWW-Authenticate: Bearer`
- **Customizable**: No (fixed message)
- **Usage**: Authentication credentials are invalid
- **Example**:
  ```python
  raise CredentialsException()
  ```

### TokenExpiredException
- **Default Message**: `"Token has expired"`
- **Status Code**: 401
- **Headers**: `WWW-Authenticate: Bearer`
- **Customizable**: No (fixed message)
- **Usage**: JWT token has expired
- **Example**:
  ```python
  raise TokenExpiredException()
  ```

### AuthenticationException
- **Default Message**: `"Authentication failed"`
- **Status Code**: 401
- **Headers**: `WWW-Authenticate: Bearer`
- **Customizable**: Yes (detail)
- **Usage**: General authentication failures
- **Example**:
  ```python
  raise AuthenticationException("Invalid email or password")
  ```

### DeviceAuthenticationException
- **Default Message**: `"Device authentication failed"`
- **Status Code**: 401
- **Customizable**: Yes (detail)
- **Usage**: Device authentication failures (ID mismatch)
- **Example**:
  ```python
  raise DeviceAuthenticationException("Device ID mismatch")
  ```

---

## 🚫 HTTP 403 - Forbidden

### InsufficientPermissionsException
- **Default Message**: `"Insufficient permissions"`
- **Status Code**: 403
- **Customizable**: Yes (detail)
- **Usage**: User lacks required permissions
- **Example**:
  ```python
  raise InsufficientPermissionsException("Admin access required")
  ```

### InactiveUserException
- **Default Message**: `"User account is deactivated"`
- **Status Code**: 403
- **Customizable**: Yes (detail)
- **Usage**: User account is deactivated
- **Example**:
  ```python
  raise InactiveUserException("Account is deactivated")
  ```

### AccessDeniedException
- **Default Message**: `"Access denied"`
- **Status Code**: 403
- **Customizable**: Yes (detail)
- **Usage**: Access denied to resource
- **Example**:
  ```python
  raise AccessDeniedException("Access denied to this device")
  ```

---

## 🔍 HTTP 404 - Not Found

### ResourceNotFoundException
- **Default Message**: `"{resource_type} with id {resource_id} not found"` (dynamic)
- **Status Code**: 404
- **Parameters**: `resource_type` (str), `resource_id` (str)
- **Customizable**: No (built from parameters)
- **Usage**: Specific resource not found
- **Example**:
  ```python
  raise ResourceNotFoundException("User", "123e4567-e89b-12d3-a456-426614174000")
  ```

### NotFoundException
- **Default Message**: `"Resource not found"`
- **Status Code**: 404
- **Customizable**: Yes (detail)
- **Usage**: Generic resource not found
- **Example**:
  ```python
  raise NotFoundException("User not found")
  ```

### UserNotFoundException
- **Default Message**: `"User not found"`
- **Status Code**: 404
- **Customizable**: Yes (detail)
- **Usage**: User not found in database
- **Example**:
  ```python
  raise UserNotFoundException("User 123 not found")
  ```

### DeviceNotFoundException
- **Default Message**: `"Device not found"`
- **Status Code**: 404
- **Customizable**: Yes (detail)
- **Usage**: Device not found in database
- **Example**:
  ```python
  raise DeviceNotFoundException("Device not found")
  ```

### OrganizationNotFoundException
- **Default Message**: `"Organization not found"`
- **Status Code**: 404
- **Customizable**: Yes (detail)
- **Usage**: Organization not found in database
- **Example**:
  ```python
  raise OrganizationNotFoundException("Organization not found")
  ```

### ReadingNotFoundException
- **Default Message**: `"Reading not found"`
- **Status Code**: 404
- **Customizable**: Yes (detail)
- **Usage**: Reading not found in database
- **Example**:
  ```python
  raise ReadingNotFoundException("Reading not found")
  ```

---

## ⏱️ HTTP 408 - Request Timeout

### CommandTimeoutException
- **Default Message**: `"Command {command_id} for device {device_id} timed out"` (dynamic)
- **Status Code**: 408
- **Parameters**: `device_id` (str), `command_id` (str)
- **Customizable**: No (built from parameters)
- **Usage**: Device command times out
- **Example**:
  ```python
  raise CommandTimeoutException("device-123", "cmd-456")
  ```

---

## ⚠️ HTTP 409 - Conflict

### ConflictException
- **Default Message**: Custom detail message (required)
- **Status Code**: 409
- **Parameters**: `detail` (str) - required
- **Customizable**: Yes (detail required)
- **Usage**: Conflict with existing data
- **Example**:
  ```python
  raise ConflictException("Resource already exists")
  ```

### UserAlreadyExistsException
- **Default Message**: `"A user with this email already exists"`
- **Status Code**: 409
- **Customizable**: Yes (detail)
- **Usage**: User with given email already exists
- **Example**:
  ```python
  raise UserAlreadyExistsException("User with this email already exists")
  ```

### DeviceAlreadyExistsException
- **Default Message**: `"A device with this serial number already exists"`
- **Status Code**: 409
- **Customizable**: Yes (detail)
- **Usage**: Device with same serial number already exists
- **Example**:
  ```python
  raise DeviceAlreadyExistsException("Device with this serial number already exists")
  ```

### OrganizationAlreadyExistsException
- **Default Message**: `"An organization with this name already exists"`
- **Status Code**: 409
- **Customizable**: Yes (detail)
- **Usage**: Organization with same name already exists
- **Example**:
  ```python
  raise OrganizationAlreadyExistsException("Organization with this name already exists")
  ```

---

## 📝 HTTP 422 - Unprocessable Entity

### ValidationException
- **Default Message**: Custom detail message (required)
- **Status Code**: 422
- **Parameters**: `detail` (str) - required
- **Customizable**: Yes (detail required)
- **Usage**: Data validation fails
- **Example**:
  ```python
  raise ValidationException("Email is required")
  raise ValidationException("Password must be at least 8 characters long")
  ```

---

## 🚦 HTTP 429 - Too Many Requests

### RateLimitException
- **Default Message**: `"Rate limit exceeded"`
- **Status Code**: 429
- **Headers**: `Retry-After: {retry_after}` (default 60s)
- **Parameters**: `retry_after` (int) - optional, default 60
- **Customizable**: Yes (retry_after parameter)
- **Usage**: Rate limit is exceeded
- **Example**:
  ```python
  raise RateLimitException()  # Default 60s retry
  raise RateLimitException(120)  # 120s retry
  ```

---

## 🔧 HTTP 500 - Internal Server Error

### ConfigurationException
- **Default Message**: `"Invalid application configuration"`
- **Status Code**: 500
- **Customizable**: Yes (detail)
- **Usage**: Application configuration is invalid
- **Example**:
  ```python
  raise ConfigurationException("Database URL is invalid")
  ```

### DatabaseException
- **Default Message**: `"Database operation failed"`
- **Status Code**: 500
- **Customizable**: Yes (detail)
- **Usage**: Database operations fail
- **Example**:
  ```python
  raise DatabaseException("Failed to create user")
  ```

### ServiceException
- **Default Message**: `"A service error occurred"`
- **Status Code**: 500
- **Customizable**: Yes (detail)
- **Usage**: General service layer errors
- **Example**:
  ```python
  raise ServiceException("Failed to process request")
  ```

### DataProcessingException
- **Default Message**: `"Data processing failed"`
- **Status Code**: 500
- **Customizable**: Yes (detail)
- **Usage**: Data processing failures
- **Example**:
  ```python
  raise DataProcessingException("Failed to parse sensor data")
  ```

---

## 🔌 HTTP 503 - Service Unavailable

### DatabaseConnectionException
- **Default Message**: `"Database connection failed"`
- **Status Code**: 503
- **Customizable**: Yes (detail)
- **Usage**: Database connection fails
- **Example**:
  ```python
  raise DatabaseConnectionException("Cannot connect to database")
  ```

### ExternalServiceException
- **Default Message**: `"External service {service_name} is unavailable"` (dynamic)
- **Status Code**: 503
- **Parameters**: `service_name` (str), `detail` (str) - optional
- **Customizable**: Yes (service_name required, detail optional)
- **Usage**: External service calls fail
- **Example**:
  ```python
  raise ExternalServiceException("email-service")
  raise ExternalServiceException("payment-gateway", "Service is down")
  ```

### DeviceOfflineException
- **Default Message**: `"Device {device_id} is offline"` (dynamic)
- **Status Code**: 503
- **Parameters**: `device_id` (str)
- **Customizable**: No (built from parameter)
- **Usage**: Trying to communicate with offline device
- **Example**:
  ```python
  raise DeviceOfflineException("device-123")
  ```

---

## 📈 Exception Statistics

### Status Code Distribution
| Status Code | Count | Exceptions |
|-------------|-------|------------|
| 404 | 6 | ResourceNotFoundException, NotFoundException, UserNotFoundException, DeviceNotFoundException, OrganizationNotFoundException, ReadingNotFoundException |
| 500 | 4 | ConfigurationException, DatabaseException, ServiceException, DataProcessingException |
| 401 | 4 | CredentialsException, TokenExpiredException, AuthenticationException, DeviceAuthenticationException |
| 409 | 4 | ConflictException, UserAlreadyExistsException, DeviceAlreadyExistsException, OrganizationAlreadyExistsException |
| 403 | 3 | InsufficientPermissionsException, InactiveUserException, AccessDeniedException |
| 503 | 3 | DatabaseConnectionException, ExternalServiceException, DeviceOfflineException |
| 422 | 1 | ValidationException |
| 429 | 1 | RateLimitException |
| 408 | 1 | CommandTimeoutException |
| 400 | 1 | LMSException |

### Customization Levels
| Level | Count | Exceptions |
|-------|-------|------------|
| Fully Customizable | 20 | Most exceptions with customizable detail messages |
| Parameter-Based | 5 | ResourceNotFoundException, CommandTimeoutException, ExternalServiceException, DeviceOfflineException, RateLimitException |
| Fixed Messages | 3 | CredentialsException, TokenExpiredException |

### Header Usage
| Header | Count | Exceptions |
|--------|-------|------------|
| WWW-Authenticate: Bearer | 3 | CredentialsException, TokenExpiredException, AuthenticationException |
| Retry-After | 1 | RateLimitException |

---

## 🎯 Best Practices

### When to Use Each Exception Type

1. **Authentication (401)**: Use for any authentication-related failures
2. **Authorization (403)**: Use for permission/access control issues
3. **Not Found (404)**: Use when resources don't exist
4. **Conflict (409)**: Use for duplicate/conflict scenarios
5. **Validation (422)**: Use for data validation failures
6. **Rate Limiting (429)**: Use when rate limits are exceeded
7. **Timeouts (408)**: Use for operation timeouts
8. **Server Errors (500)**: Use for internal service errors
9. **Service Unavailable (503)**: Use for external dependency failures

### Exception Handling Guidelines

1. **Always provide meaningful detail messages**
2. **Use appropriate HTTP status codes**
3. **Include required headers for authentication exceptions**
4. **Log exceptions for debugging**
5. **Handle exceptions at appropriate layers**
6. **Provide consistent error responses**

### Import Usage

```python
from app.exceptions import (
    AuthenticationException,
    ValidationException,
    NotFoundException,
    # ... other exceptions as needed
)
```

---

## 🔄 Exception Handlers

The `exceptions.py` file also includes three exception handlers:

1. **global_exception_handler**: Handles unhandled exceptions
2. **http_exception_handler**: Handles HTTPException instances
3. **validation_exception_handler**: Handles ValidationException instances

These handlers provide consistent JSON error responses across the application.

---

*Last Updated: Generated from exceptions.py analysis* 