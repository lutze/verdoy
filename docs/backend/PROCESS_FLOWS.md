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

## Process Flow 5: User-Organization Association

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

## Data Model Relationships

### Entity Hierarchy
```
Entity (base table)
├── User (entity_type='user')
├── Organization (entity_type='organization')
├── Device (entity_type='device.esp32')
├── AlertRule (entity_type='alert.rule')
└── Billing (entity_type='billing.account')
```

### Key Relationships
- **User ↔ Entity**: One-to-one via `entity_id`
- **Entity ↔ Organization**: Many-to-one via `organization_id`
- **Organization ↔ Members**: One-to-many via `organization_id` (reverse)
- **Entity ↔ Entity**: Many-to-many via `relationships` table

---

## Implementation Notes

### Test User for Development & CI
- A default test user is always created via migration (`test@example.com` / `testpassword123`).
- The password hash is generated using the backend's bcrypt environment to ensure compatibility.
- This user is guaranteed to work after every database rebuild and is used for Playwright/CI login tests.
- The test user is created in the `006_add_users_table.sql` migration, after the users table exists.

### Password Hashing
- All passwords are hashed using bcrypt (12 rounds) via passlib in the backend container.
- Never store plain text passwords or hashes generated outside the backend environment.

### Registration & Login Flow
- Registration and login are robust and tested end-to-end.
- Registration creates both an Entity and a User, with proper foreign key relationships.
- Login verifies the password using the User model's `check_password` method.
- Post-login and logout redirects use `/auth/profile` and `/auth/login` (no `/api/v1/` prefix).

### Migration Order
- The test user is created only after the users table exists (in `006_add_users_table.sql`).
- If you add new migrations, ensure the test user creation remains after the users table.

### Testing
- Playwright and API tests use the test user for login and registration flows.
- The test user is always available for local development and CI.

---

## Testing Scenarios

### User Registration Tests
- [ ] Valid user registration
- [ ] Duplicate email handling
- [ ] Invalid data validation
- [ ] Password strength requirements

### Organization Creation Tests
- [ ] Valid organization creation
- [ ] Organization creation without user
- [ ] Duplicate organization names
- [ ] User already in organization

### Authentication Tests
- [ ] Valid login
- [ ] Invalid credentials
- [ ] Deactivated account
- [ ] Token refresh

### Permission Tests
- [ ] Superuser access
- [ ] Organization member access
- [ ] Cross-organization access denial
- [ ] Resource-level permissions

### Edge Cases
- [ ] User leaving organization
- [ ] Organization deletion with members
- [ ] Permission inheritance
- [ ] Audit trail verification 