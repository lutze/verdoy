# Process Flows: User & Organization Management

## Overview
This document outlines the process flows for user creation, organization creation, user authentication, and user permissions in the LMS Core system. The design follows a single-table inheritance model where all entities (users, organizations, devices, etc.) are stored in the `entities` table with polymorphic identities.

## Key Design Principles

1. **Single-Table Inheritance**: All entities use the same `entities` table with `entity_type` differentiation
2. **User-First Creation**: Organizations must be created by an existing user who automatically becomes the organization owner. Empty organizations without any members are not allowed.
3. **Entity Association**: Users have a one-to-one relationship with an Entity record
4. **Organization Membership**: Users can belong to organizations via `organization_id` field
5. **Permission-Based Access**: Access control based on user roles and organization membership

---

## Process Flow 1: User Registration

### Flow Description
New user registration process that creates both a User record and an associated Entity record.

### Steps
1. **Validate Input**
   - Email format validation
   - Password strength validation
   - Name validation
   - Check if email already exists

2. **Create User Entity**
   ```python
   # Create Entity record for user profile
   user_entity = Entity(
       entity_type='user',
       name=user_data.name,
       description=f"User profile for {user_data.email}",
       organization_id=user_data.organization_id,  # Can be None for standalone users
       properties={
           'email': user_data.email,
           'user_type': 'standard'
       }
   )
   ```

3. **Create User Record**
   ```python
   # Create User record with hashed password
   user = User(
       entity_id=user_entity.id,
       email=user_data.email,
       hashed_password=hashed_password,
       is_active=True,
       is_superuser=False
   )
   ```

4. **Save to Database**
   - Save user_entity first
   - Save user record with entity_id reference
   - Commit transaction

5. **Return Result**
   - Return user object with entity relationship
   - Include success message and user ID

### Error Handling
- **Email Already Exists**: Return 409 Conflict
- **Invalid Data**: Return 400 Bad Request
- **Database Error**: Return 500 Internal Server Error

---

## Process Flow 2: Organization Creation

### Flow Description
Organization creation process that requires at least one existing user to be the organization owner.

### Prerequisites
- At least one user must exist in the system
- Creating user must be authenticated
- User must not already belong to another organization (unless superuser)

### Steps
1. **Validate Prerequisites**
   - Verify creating user exists and is authenticated
   - Check if user already belongs to an organization
   - Validate organization data (name, type, etc.)

2. **Create Organization Entity**
   ```python
   # Create Entity record for organization
   org_entity = Entity(
       entity_type='organization',
       name=org_data.name,
       description=org_data.description,
       organization_id=None,  # Organizations are top-level entities
       properties={
           'organization_type': org_data.organization_type,
           'contact_email': org_data.contact_email,
           'website': org_data.website,
           'address': org_data.address,
           'subscription_plan': 'free',
           'member_count': 1,  # Starting with creator
           'created_by': creating_user.id
       }
   )
   ```

3. **Update User's Organization**
   ```python
   # Update user's entity to reference the new organization
   user.entity.organization_id = org_entity.id
   ```

4. **Create Owner Relationship** 
   ```python
   # Create relationship record for ownership
   relationship = Relationship(
       from_entity=org_entity.id,
       to_entity=user.entity.id,
       relationship_type='owns',
       properties={'role': 'owner', 'permissions': ['all']}
   )
   ```

5. **Save to Database**
   - Save org_entity
   - Update user.entity
   - Save relationship (if using)
   - Commit transaction

6. **Return Result**
   - Return organization object
   - Include member count and owner information

### Error Handling
- **No Authenticated User**: Return 401 Unauthorized
- **User Already in Organization**: Return 400 Bad Request
- **Invalid Organization Data**: Return 400 Bad Request
- **Database Error**: Return 500 Internal Server Error

---

## Process Flow 3: User Authentication

### Flow Description
User login process that validates credentials and returns authentication tokens or sets session cookies based on client type.

### Dual Authentication System
The system supports both programmatic API clients and web browsers:
- **API Clients**: Receive JWT tokens in JSON response
- **Web Browsers**: Receive HTTP-only session cookies and redirects

### Steps
1. **Validate Input**
   - Email format validation
   - Password presence validation

2. **Determine Client Type**
   ```python
   def accepts_json(request: Request) -> bool:
       """Check if client prefers JSON responses"""
       accept_header = request.headers.get("accept", "")
       return (
           "application/json" in accept_header or
           "application/ld+json" in accept_header or
           request.url.path.startswith("/api/")
       )
   ```

3. **Find User**
   ```python
   # Query user by email
   user = db.query(User).filter(User.email == email).first()
   if not user:
       raise AuthenticationException("Invalid credentials")
   ```

4. **Verify Password**
   ```python
   # Verify password hash using User model method
   if not user.check_password(password):
       raise AuthenticationException("Invalid credentials")
   ```

5. **Check User Status**
   ```python
   # Verify user is active
   if not user.is_active:
       raise AuthenticationException("Account is deactivated")
   ```

6. **Generate JWT Token**
   ```python
   # Set token expiration based on remember_me
   if remember_me == "true":
       expires_delta = timedelta(days=30)  # 30 days if remember me is checked
   else:
       expires_delta = timedelta(hours=1)  # 1 hour default
   
   access_token = create_access_token(
       data={"sub": str(user.id), "email": user.email},
       expires_delta=expires_delta
   )
   
   # Update last login
   user.last_login = datetime.utcnow()
   db.commit()
   ```

7. **Return Authentication Result (Client-Specific)**
   
   **For API Clients (JSON Response):**
   ```python
   return {
       "access_token": access_token,
       "token_type": "bearer",
       "expires_in": int(expires_delta.total_seconds()),
       "user": {
           "id": str(user.id),
           "email": user.email,
           "name": user.entity.name if user.entity else "Unknown User",
           "is_active": user.is_active
       }
   }
   ```
   
   **For Web Browsers (Session Cookie + Redirect):**
   ```python
   # Create redirect response to dashboard
   response = RedirectResponse(url="/app/dashboard", status_code=303)
   
   # Set HTTP-only session cookie
   response.set_cookie(
       key="session_token",
       value=access_token,
       max_age=int(expires_delta.total_seconds()),
       httponly=True,  # Prevent XSS attacks
       secure=True if request.url.scheme == "https" else False,  # HTTPS only in production
       samesite="lax"  # CSRF protection
   )
   
   return response
   ```

### Authentication Validation (Unified Dependency)
```python
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
        
        # Validate user exists in database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise CredentialsException()
        
        # Return user object
        return user
    except JWTError:
        raise CredentialsException()
```

### Error Handling
- **Invalid Credentials**: Return 401 Unauthorized (JSON) or render login page with error (HTML)
- **Account Deactivated**: Return 401 Unauthorized (JSON) or render login page with error (HTML)
- **Token Generation Error**: Return 500 Internal Server Error

### Security Features
- **HTTP-Only Cookies**: Prevent XSS attacks on session tokens
- **Secure Flag**: HTTPS-only cookies in production (auto-detected)
- **SameSite Protection**: CSRF attack prevention
- **Remember Me**: Configurable token expiration (1 hour vs 30 days)
- **Unified Validation**: Same JWT validation for both Bearer tokens and session cookies

---

## Process Flow 4: User Permissions & Access Control

### Flow Description
Permission checking process that determines user access rights based on roles and organization membership.

### Permission Levels
1. **System Level**: Superuser permissions across all organizations
2. **Organization Level**: Admin/member permissions within specific organization
3. **Resource Level**: Specific permissions on individual resources (devices, data, etc.)

### Steps
1. **Extract User Context**
   ```python
   # Get current user from token
   current_user = get_current_user(token)
   
   # Get user's organization
   user_org = current_user.entity.organization_id
   ```

2. **Check System-Level Permissions**
   ```python
   # Superuser bypass
   if current_user.is_superuser:
       return True
   ```

3. **Check Organization-Level Permissions**
   ```python
   # Verify user belongs to the target organization
   if target_org_id and current_user.entity.organization_id != target_org_id:
       raise PermissionException("Access denied to organization")
   ```

4. **Check Resource-Level Permissions**
   ```python
   # Check specific resource permissions
   if not has_resource_permission(current_user, resource_id, action):
       raise PermissionException(f"Cannot {action} resource {resource_id}")
   ```

5. **Return Permission Result**
   - Allow or deny access
   - Log permission check for audit

### Permission Matrix

| User Type | System Access | Organization Access | Resource Access |
|-----------|---------------|-------------------|-----------------|
| Superuser | All | All | All |
| Org Owner | None | All (own org) | All (own org) |
| Org Admin | None | Manage (own org) | Manage (own org) |
| Org Member | None | Read (own org) | Limited (own org) |
| Standalone User | None | None | Own resources only |

---

## Process Flow 5: Bioreactor Enrollment

### Flow Description
Multi-step bioreactor enrollment process that creates a new bioreactor entity with comprehensive configuration.

### Prerequisites
- User must be authenticated and belong to an organization
- Organization must exist and be accessible to the user
- User must have permission to create bioreactors in the organization

### Steps
1. **Step 1: Basic Information Collection**
   ```python
   # Validate organization access
   if not user_has_org_access(current_user, organization_id):
       raise PermissionException("Access denied to organization")
   
   # Collect basic bioreactor information
   basic_info = {
       'name': name,  # Required
       'description': description,  # Optional
       'location': location,  # Optional
       'bioreactor_type': bioreactor_type or 'stirred_tank'
   }
   ```

2. **Step 2: Hardware Configuration**
   ```python
   # Validate required hardware parameters
   if not vessel_volume:
       raise ValidationException("Vessel volume is required")
   
   hardware_config = {
       'vessel_volume': vessel_volume,  # Required
       'working_volume': working_volume,  # Optional
       'sensors': sensors or [],  # Selected sensor types
       'actuators': actuators or []  # Selected actuator types
   }
   ```

3. **Step 3: Device Configuration**
   ```python
   # Set device-specific parameters with defaults
   device_config = {
       'firmware_version': firmware_version or '1.0.0',
       'hardware_model': hardware_model or 'Generic Bioreactor',
       'mac_address': mac_address or '00:00:00:00:00:00',
       'reading_interval': reading_interval or 300
   }
   ```

4. **Step 4: Review and Database Creation**
   ```python
   # Create bioreactor entity
   bioreactor = Bioreactor(
       name=name,
       description=description,
       organization_id=organization_id,
       entity_type='device.bioreactor',
       status='offline'
   )
   
   # Store optional fields in properties
   if location:
       bioreactor.set_property('location', location)
   
   # Set bioreactor-specific properties
   bioreactor.set_bioreactor_type(bioreactor_type or "stirred_tank")
   bioreactor.set_vessel_volume(vessel_volume)
   if working_volume:
       bioreactor.set_working_volume(working_volume)
   
   # Set hardware configuration
   hardware_config = {
       'model': hardware_model or 'Generic Bioreactor',
       'macAddress': mac_address or '00:00:00:00:00:00',
       'sensors': [{"type": sensor, "unit": "standard", "status": "active"} 
                   for sensor in (sensors or [])],
       'actuators': [{"type": actuator, "unit": "standard", "status": "active"} 
                     for actuator in (actuators or [])]
   }
   bioreactor.set_property('hardware', hardware_config)
   
   # Set firmware configuration
   firmware_config = {
       'version': firmware_version or '1.0.0',
       'lastUpdate': datetime.utcnow().isoformat()
   }
   bioreactor.set_property('firmware', firmware_config)
   
   # Set reading interval
   bioreactor.set_property('reading_interval', reading_interval or 300)
   
   # Save to database
   db.add(bioreactor)
   db.commit()
   db.refresh(bioreactor)
   ```

### Data Persistence Strategy
- **URL Parameters**: Form data passed between steps via URL query parameters
- **Hidden Inputs**: Each step includes hidden form fields to preserve previous data
- **Template Context**: Organization and form data maintained across validation errors

### Error Handling
- **Missing Required Fields**: Return to current step with error message
- **Invalid Organization Access**: Return 403 Forbidden
- **Database Errors**: Rollback transaction and return error
- **Validation Errors**: Preserve form data and display specific error messages

### Security Considerations
- **Organization Access Control**: Verify user has permission to create bioreactors
- **Input Validation**: Sanitize all user inputs
- **Transaction Safety**: Ensure database operations are atomic
- **Audit Logging**: Log all bioreactor creation events

---

## Process Flow 6: User-Organization Association

### Flow Description
Process for adding existing users to organizations or changing user organization membership.

### Steps
1. **Validate Request**
   - Verify target organization exists
   - Check if user is already in an organization
   - Verify requesting user has permission to add members

2. **Update User Entity**
   ```python
   # Update user's organization_id
   user.entity.organization_id = target_org_id
   user.entity.last_updated = datetime.utcnow()
   ```

3. **Create Membership Relationship**
   ```python
   # Create relationship record
   relationship = Relationship(
       from_entity=target_org_id,
       to_entity=user.entity.id,
       relationship_type='member_of',
       properties={'role': 'member', 'joined_at': datetime.utcnow()}
   )
   ```

4. **Update Organization Member Count**
   ```python
   # Increment organization member count
   org = db.query(Entity).filter(Entity.id == target_org_id).first()
   current_count = org.get_property('member_count', 0)
   org.set_property('member_count', current_count + 1)
   ```

5. **Save Changes**
   - Update user entity
   - Save relationship
   - Update organization
   - Commit transaction

### Error Handling
- **Organization Not Found**: Return 404 Not Found
- **User Already in Organization**: Return 400 Bad Request
- **Permission Denied**: Return 403 Forbidden

---

## Process Flow 7: Process Management

### Flow Description
Multi-step process creation and management system that supports process templates, instances, and comprehensive lifecycle management.

### Prerequisites
- User must be authenticated and belong to an organization
- Organization must exist and be accessible to the user
- User must have permission to create processes in the organization

### Steps
1. **Step 1: Basic Process Information**
   ```python
   # Validate organization access
   if not user_has_org_access(current_user, organization_id):
       raise PermissionException("Access denied to organization")
   
   # Collect basic process information
   basic_info = {
       'name': name,  # Required
       'version': version,  # Required
       'process_type': process_type,  # Required
       'description': description,  # Optional
       'is_template': is_template or False
   }
   ```

2. **Step 2: Process Configuration**
   ```python
   # Validate process type and configuration
   if not process_type:
       raise ValidationException("Process type is required")
   
   process_config = {
       'estimated_duration': estimated_duration,  # Optional
       'target_volume': target_volume,  # Optional
       'parameters': parameters or [],  # Process parameters
       'notes': notes  # Optional notes
   }
   ```

3. **Step 3: Process Steps and Review**
   ```python
   # Validate process steps
   if not steps:
       raise ValidationException("At least one process step is required")
   
   # Create process entity
   process = Process(
       name=name,
       version=version,
       process_type=process_type,
       description=description,
       organization_id=organization_id,
       status='draft',
       is_template=is_template
   )
   
   # Store configuration in properties
   if estimated_duration:
       process.set_property('estimated_duration', estimated_duration)
   if target_volume:
       process.set_property('target_volume', target_volume)
   if parameters:
       process.set_property('parameters', parameters)
   if notes:
       process.set_property('notes', notes)
   
   # Save to database
   db.add(process)
   db.commit()
   db.refresh(process)
   ```

### Process Instance Management
```python
# Create process instance for execution
instance = ProcessInstance(
    process_id=process.id,
    organization_id=organization_id,
    status='pending',
    started_by=current_user.id
)

# Execute process instance
instance.status = 'running'
instance.started_at = datetime.utcnow()
db.commit()
```

### Template System
```python
# Save process as template
if is_template:
    process.is_template = True
    process.set_property('template_shared', True)
    db.commit()

# Create process from template
template_process = db.query(Process).filter(
    Process.id == template_id,
    Process.is_template == True
).first()

new_process = Process(
    name=f"{template_process.name} - Copy",
    version=template_process.version,
    process_type=template_process.process_type,
    description=template_process.description,
    organization_id=organization_id,
    status='draft',
    is_template=False
)
```

### Error Handling
- **Missing Required Fields**: Return to current step with error message
- **Invalid Process Type**: Return validation error with available types
- **Permission Denied**: Return 403 Forbidden
- **Database Errors**: Rollback transaction and return error
- **Validation Errors**: Preserve form data and display specific error messages

---

## Process Flow 8: Bioreactor Control

### Flow Description
Safety-focused bioreactor control system with manual controls, emergency procedures, and real-time monitoring.

### Prerequisites
- User must be authenticated and have access to the bioreactor
- Bioreactor must exist and be accessible to the user
- User must have permission to control the bioreactor

### Steps
1. **Control Interface Access**
   ```python
   # Validate bioreactor access
   bioreactor = db.query(Bioreactor).filter(
       Bioreactor.id == bioreactor_id,
       Bioreactor.organization_id == current_user.organization_id
   ).first()
   
   if not bioreactor:
       raise PermissionException("Access denied to bioreactor")
   ```

2. **Safety Confirmation**
   ```python
   # Require safety confirmation for critical operations
   if control_type in ['emergency_stop', 'shutdown', 'restart']:
       if not safety_confirmation:
           raise ValidationException("Safety confirmation required for critical operations")
   ```

3. **Control Execution**
   ```python
   # Execute control command
   control_result = {
       'control_type': control_type,
       'parameter': parameter,
       'value': value,
       'timestamp': datetime.utcnow(),
       'executed_by': current_user.id,
       'status': 'executing'
   }
   
   # Update bioreactor status
   bioreactor.set_property('last_control_action', control_result)
   bioreactor.set_property('status', 'controlled')
   db.commit()
   ```

4. **Real-time Monitoring**
   ```python
   # HTMX polling for real-time updates
   def get_bioreactor_status(bioreactor_id):
       bioreactor = db.query(Bioreactor).filter(Bioreactor.id == bioreactor_id).first()
       return {
           'status': bioreactor.get_property('status', 'unknown'),
           'last_control': bioreactor.get_property('last_control_action'),
           'sensor_data': bioreactor.get_property('latest_readings', []),
           'timestamp': datetime.utcnow().isoformat()
       }
   ```

### Emergency Procedures
```python
# Emergency stop procedure
if control_type == 'emergency_stop':
    # Immediate halt of all systems
    emergency_result = {
        'type': 'emergency_stop',
        'timestamp': datetime.utcnow(),
        'executed_by': current_user.id,
        'status': 'emergency_stop_activated'
    }
    
    # Update bioreactor status
    bioreactor.set_property('emergency_stop', emergency_result)
    bioreactor.set_property('status', 'emergency_stop')
    db.commit()
    
    # Log emergency event
    log_emergency_event(bioreactor_id, current_user.id, 'emergency_stop')
```

### Safety Features
- **Emergency Stop**: Immediate halt of all bioreactor systems
- **Safety Confirmations**: Required for critical operations
- **Status Monitoring**: Real-time status tracking
- **Audit Logging**: Complete logging of all control actions
- **Mobile Interface**: Touch-friendly controls for mobile operation

### Error Handling
- **Permission Denied**: Return 403 Forbidden
- **Safety Confirmation Missing**: Return validation error
- **Control Execution Failure**: Return error with details
- **Emergency Stop Activation**: Immediate system halt
- **Real-time Update Failures**: Graceful degradation

---

## Process Flow 9: Real-time Data Integration

### Flow Description
HTMX-based real-time data integration for bioreactor monitoring and process tracking.

### Implementation
```python
# HTMX polling endpoints for real-time updates
@router.get("/{bioreactor_id}/status", response_class=HTMLResponse)
async def bioreactor_status_partial(request: Request, bioreactor_id: UUID):
    """Real-time bioreactor status updates via HTMX."""
    bioreactor = get_bioreactor_with_access(bioreactor_id, current_user)
    
    return templates.TemplateResponse(
        "partials/bioreactor_status.html",
        {
            "request": request,
            "bioreactor": bioreactor,
            "status": bioreactor.get_property('status', 'unknown'),
            "last_update": bioreactor.get_property('last_update')
        }
    )

@router.get("/{bioreactor_id}/data", response_class=HTMLResponse)
async def bioreactor_data_partial(request: Request, bioreactor_id: UUID):
    """Real-time sensor data updates via HTMX."""
    bioreactor = get_bioreactor_with_access(bioreactor_id, current_user)
    
    # Get latest sensor readings
    readings = get_latest_readings(bioreactor_id)
    
    return templates.TemplateResponse(
        "partials/bioreactor_data.html",
        {
            "request": request,
            "readings": readings,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Mobile-First Design
- **Touch-Friendly Controls**: Large touch targets for mobile operation
- **Responsive Layout**: Adaptive design for different screen sizes
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Real-time Updates**: HTMX polling for live data without page reloads

### Error Handling
- **Connection Failures**: Graceful degradation with cached data
- **Update Failures**: Retry mechanism with exponential backoff
- **Mobile Compatibility**: Fallback for unsupported mobile features
- **Data Validation**: Real-time validation of sensor data 