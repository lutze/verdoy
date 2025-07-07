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
User login process that validates credentials and returns authentication tokens.

### Steps
1. **Validate Input**
   - Email format validation
   - Password presence validation

2. **Find User**
   ```python
   # Query user by email
   user = db.query(User).filter(User.email == email).first()
   if not user:
       raise AuthenticationException("Invalid credentials")
   ```

3. **Verify Password**
   ```python
   # Verify password hash
   if not User.verify_password(password, user.hashed_password):
       raise AuthenticationException("Invalid credentials")
   ```

4. **Check User Status**
   ```python
   # Verify user is active
   if not user.is_active:
       raise AuthenticationException("Account is deactivated")
   ```

5. **Generate Tokens**
   ```python
   # Create access token
   access_token = create_access_token(
       data={"sub": str(user.id), "email": user.email}
   )
   
   # Create refresh token
   refresh_token = create_refresh_token(
       data={"sub": str(user.id)}
   )
   ```

6. **Return Authentication Result**
   ```python
   return {
       "access_token": access_token,
       "refresh_token": refresh_token,
       "token_type": "bearer",
       "user": {
           "id": str(user.id),
           "email": user.email,
           "name": user.entity.name,
           "organization_id": str(user.entity.organization_id) if user.entity.organization_id else None,
           "is_superuser": user.is_superuser
       }
   }
   ```

### Error Handling
- **Invalid Credentials**: Return 401 Unauthorized
- **Account Deactivated**: Return 401 Unauthorized
- **Token Generation Error**: Return 500 Internal Server Error

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

### Database Constraints
- `users.entity_id` must reference existing `entities.id`
- `entities.organization_id` can be NULL (for standalone users/organizations)
- `entities.organization_id` must reference existing `entities.id` when not NULL

### Security Considerations
- All passwords must be hashed using bcrypt
- JWT tokens should have appropriate expiration times
- Organization membership should be validated on all resource access
- Audit logging should track all user and organization changes

### Performance Considerations
- Index on `entities.organization_id` for fast organization queries
- Index on `users.email` for fast authentication
- Consider caching for frequently accessed permission checks
- Use database transactions for multi-step operations

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