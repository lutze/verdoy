# Entity Migration Plan: Hybrid to Pure Entity Approach

## Overview

This plan migrates the LMS Core system from a hybrid approach (separate tables for projects, users) to a pure entity approach where all entities are stored in the `entities` table with specialized fields in the `properties` JSONB column.

## Current State Analysis

### Hybrid Approach (Current)
- **Entities table**: Common fields (name, description, entity_type, etc.)
- **Projects table**: Project-specific fields (start_date, end_date, budget, etc.)
- **Users table**: User-specific fields (email, hashed_password, etc.)
- **Foreign key relationships**: Projects and Users link to Entities

### Pure Entity Approach (Target)
- **Entities table**: All entities with specialized fields in `properties` JSONB
- **No separate tables**: All data in single table with entity_type discrimination
- **Consistent patterns**: All entities work the same way

## Migration Benefits

1. **Consistency**: All entities follow the same pattern
2. **Flexibility**: Easy to add new entity types without schema changes
3. **Simplicity**: One table to rule them all
4. **Graph queries**: Better support for relationship queries
5. **Maintainability**: Less code duplication and complexity

## Phase 1: Database Schema Migration

### Step 1.1: Create Migration Script
**File**: `database/migrations/007_migrate_to_pure_entities.sql`

```sql
-- Migration to pure entity approach
-- This script migrates data from hybrid approach to pure entity approach

-- Step 1: Add missing properties to existing entities
UPDATE entities 
SET properties = properties || jsonb_build_object(
    'contact_email', o.contact_email,
    'contact_phone', o.contact_phone,
    'website', o.website,
    'address', o.address,
    'city', o.city,
    'state', o.state,
    'country', o.country,
    'postal_code', o.postal_code,
    'timezone', o.timezone
)
FROM (
    SELECT 
        id,
        contact_email,
        contact_phone,
        website,
        address,
        city,
        state,
        country,
        postal_code,
        timezone
    FROM organizations
) o
WHERE entities.id = o.id AND entities.entity_type = 'organization';

-- Step 2: Migrate project data to entity properties
UPDATE entities 
SET properties = properties || jsonb_build_object(
    'start_date', p.start_date,
    'end_date', p.end_date,
    'expected_completion', p.expected_completion,
    'actual_completion', p.actual_completion,
    'budget', p.budget,
    'progress_percentage', p.progress_percentage,
    'tags', p.tags,
    'project_metadata', p.project_metadata,
    'settings', p.settings,
    'organization_id', p.organization_id,
    'project_lead_id', p.project_lead_id,
    'priority', p.priority
)
FROM projects p
WHERE entities.id = p.id AND entities.entity_type = 'project';

-- Step 3: Migrate user data to entity properties
UPDATE entities 
SET properties = properties || jsonb_build_object(
    'email', u.email,
    'hashed_password', u.hashed_password,
    'is_superuser', u.is_superuser,
    'entity_id', u.entity_id
)
FROM users u
WHERE entities.id = u.entity_id AND entities.entity_type = 'user';

-- Step 4: Update entity types for consistency
UPDATE entities SET entity_type = 'user' WHERE entity_type = 'user_profile';
UPDATE entities SET entity_type = 'organization' WHERE entity_type = 'org';

-- Step 5: Clean up orphaned records (optional)
-- DELETE FROM projects WHERE id NOT IN (SELECT id FROM entities WHERE entity_type = 'project');
-- DELETE FROM users WHERE entity_id NOT IN (SELECT id FROM entities WHERE entity_type = 'user');
```

### Step 1.2: Create Rollback Script
**File**: `database/migrations/007_migrate_to_pure_entities_rollback.sql`

```sql
-- Rollback script for pure entity migration
-- This script restores the hybrid approach if needed

-- Note: This is a destructive rollback that would lose data
-- Only use in development/testing environments

-- Step 1: Restore projects table data
INSERT INTO projects (
    id, organization_id, project_lead_id, status, priority,
    start_date, end_date, expected_completion, actual_completion,
    budget, progress_percentage, tags, project_metadata, settings,
    created_at, updated_at
)
SELECT 
    id,
    (properties->>'organization_id')::uuid,
    (properties->>'project_lead_id')::uuid,
    status,
    properties->>'priority',
    (properties->>'start_date')::date,
    (properties->>'end_date')::date,
    (properties->>'expected_completion')::date,
    (properties->>'actual_completion')::date,
    properties->>'budget',
    (properties->>'progress_percentage')::integer,
    properties->'tags',
    properties->'project_metadata',
    properties->'settings',
    created_at,
    updated_at
FROM entities 
WHERE entity_type = 'project';

-- Step 2: Restore users table data
INSERT INTO users (
    entity_id, email, hashed_password, is_active, is_superuser,
    created_at, updated_at
)
SELECT 
    id,
    properties->>'email',
    properties->>'hashed_password',
    is_active,
    (properties->>'is_superuser')::boolean,
    created_at,
    updated_at
FROM entities 
WHERE entity_type = 'user';
```

## Phase 2: Model Layer Refactoring

### Step 2.1: Update Project Model
**File**: `backend/app/models/project.py`

```python
"""
Project model for laboratory project management.

Projects organize experiments, processes, and research activities
within an organization. They serve as containers for related work
and help with organization, permissions, and data management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import relationship
from uuid import UUID

from .entity import Entity


class Project(Entity):
    """
    Project model for organizing laboratory work and experiments.
    
    Maps to the entities table with entity_type = 'project'
    and stores project-specific fields in the properties JSONB column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'project',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for projects
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'project'
        super().__init__(*args, **kwargs)
    
    # Project-specific property accessors
    @property
    def start_date(self) -> Optional[datetime]:
        """Get project start date from properties."""
        start_date_str = self.get_property('start_date')
        if start_date_str:
            return datetime.fromisoformat(start_date_str)
        return None
    
    @start_date.setter
    def start_date(self, value: Optional[datetime]):
        """Set project start date in properties."""
        if value:
            self.set_property('start_date', value.isoformat())
        else:
            self.set_property('start_date', None)
    
    @property
    def end_date(self) -> Optional[datetime]:
        """Get project end date from properties."""
        end_date_str = self.get_property('end_date')
        if end_date_str:
            return datetime.fromisoformat(end_date_str)
        return None
    
    @end_date.setter
    def end_date(self, value: Optional[datetime]):
        """Set project end date in properties."""
        if value:
            self.set_property('end_date', value.isoformat())
        else:
            self.set_property('end_date', None)
    
    @property
    def expected_completion(self) -> Optional[datetime]:
        """Get expected completion date from properties."""
        completion_str = self.get_property('expected_completion')
        if completion_str:
            return datetime.fromisoformat(completion_str)
        return None
    
    @expected_completion.setter
    def expected_completion(self, value: Optional[datetime]):
        """Set expected completion date in properties."""
        if value:
            self.set_property('expected_completion', value.isoformat())
        else:
            self.set_property('expected_completion', None)
    
    @property
    def actual_completion(self) -> Optional[datetime]:
        """Get actual completion date from properties."""
        completion_str = self.get_property('actual_completion')
        if completion_str:
            return datetime.fromisoformat(completion_str)
        return None
    
    @actual_completion.setter
    def actual_completion(self, value: Optional[datetime]):
        """Set actual completion date in properties."""
        if value:
            self.set_property('actual_completion', value.isoformat())
        else:
            self.set_property('actual_completion', None)
    
    @property
    def budget(self) -> Optional[str]:
        """Get project budget from properties."""
        return self.get_property('budget')
    
    @budget.setter
    def budget(self, value: Optional[str]):
        """Set project budget in properties."""
        self.set_property('budget', value)
    
    @property
    def progress_percentage(self) -> int:
        """Get project progress percentage from properties."""
        return self.get_property('progress_percentage', 0)
    
    @progress_percentage.setter
    def progress_percentage(self, value: int):
        """Set project progress percentage in properties."""
        self.set_property('progress_percentage', value)
    
    @property
    def tags(self) -> List[str]:
        """Get project tags from properties."""
        return self.get_property('tags', [])
    
    @tags.setter
    def tags(self, value: List[str]):
        """Set project tags in properties."""
        self.set_property('tags', value)
    
    @property
    def project_metadata(self) -> Dict[str, Any]:
        """Get project metadata from properties."""
        return self.get_property('project_metadata', {})
    
    @project_metadata.setter
    def project_metadata(self, value: Dict[str, Any]):
        """Set project metadata in properties."""
        self.set_property('project_metadata', value)
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Get project settings from properties."""
        return self.get_property('settings', {})
    
    @settings.setter
    def settings(self, value: Dict[str, Any]):
        """Set project settings in properties."""
        self.set_property('settings', value)
    
    @property
    def organization_id(self) -> Optional[UUID]:
        """Get organization ID from properties."""
        org_id_str = self.get_property('organization_id')
        if org_id_str:
            return UUID(org_id_str)
        return None
    
    @organization_id.setter
    def organization_id(self, value: Optional[UUID]):
        """Set organization ID in properties."""
        if value:
            self.set_property('organization_id', str(value))
        else:
            self.set_property('organization_id', None)
    
    @property
    def project_lead_id(self) -> Optional[UUID]:
        """Get project lead ID from properties."""
        lead_id_str = self.get_property('project_lead_id')
        if lead_id_str:
            return UUID(lead_id_str)
        return None
    
    @project_lead_id.setter
    def project_lead_id(self, value: Optional[UUID]):
        """Set project lead ID in properties."""
        if value:
            self.set_property('project_lead_id', str(value))
        else:
            self.set_property('project_lead_id', None)
    
    @property
    def priority(self) -> str:
        """Get project priority from properties."""
        return self.get_property('priority', 'medium')
    
    @priority.setter
    def priority(self, value: str):
        """Set project priority in properties."""
        self.set_property('priority', value)
    
    # Business logic methods
    @property
    def is_active(self) -> bool:
        """Check if project is currently active."""
        return self.status == "active"
    
    @property
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == "completed"
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is past its expected completion date."""
        if not self.expected_completion:
            return False
        return datetime.utcnow() > self.expected_completion and not self.is_completed
    
    def get_duration_days(self) -> int:
        """Get project duration in days."""
        if not self.start_date:
            return 0
        
        end = self.actual_completion or self.end_date or datetime.utcnow()
        return (end - self.start_date).days
    
    def update_progress(self, percentage: int):
        """Update project progress percentage."""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            if percentage == 100 and self.status == "active":
                self.status = "completed"
                self.actual_completion = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a tag to the project."""
        current_tags = self.tags
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = current_tags
    
    def remove_tag(self, tag: str):
        """Remove a tag from the project."""
        current_tags = self.tags
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = current_tags
    
    def to_dict(self):
        """Convert project to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "status": self.status,
            "priority": self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "expected_completion": self.expected_completion.isoformat() if self.expected_completion else None,
            "actual_completion": self.actual_completion.isoformat() if self.actual_completion else None,
            "project_lead_id": str(self.project_lead_id) if self.project_lead_id else None,
            "budget": self.budget,
            "progress_percentage": self.progress_percentage,
            "tags": self.tags,
            "project_metadata": self.project_metadata,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "is_overdue": self.is_overdue
        }
```

### Step 2.2: Update User Model
**File**: `backend/app/models/user.py`

```python
"""
User model for LMS Core API.

This module contains the User model and related functionality
for user authentication and management.
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from typing import Optional
import uuid

from .entity import Entity

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Entity):
    """
    User model for authentication and user management.
    
    Maps to the entities table with entity_type = 'user'
    and stores user-specific fields in the properties JSONB column.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }
    
    def __init__(self, *args, **kwargs):
        # Set default entity_type for users
        if 'entity_type' not in kwargs:
            kwargs['entity_type'] = 'user'
        super().__init__(*args, **kwargs)
    
    # User-specific property accessors
    @property
    def email(self) -> str:
        """Get user email from properties."""
        return self.get_property('email', '')
    
    @email.setter
    def email(self, value: str):
        """Set user email in properties."""
        self.set_property('email', value)
    
    @property
    def hashed_password(self) -> str:
        """Get hashed password from properties."""
        return self.get_property('hashed_password', '')
    
    @hashed_password.setter
    def hashed_password(self, value: str):
        """Set hashed password in properties."""
        self.set_property('hashed_password', value)
    
    @property
    def is_superuser(self) -> bool:
        """Get superuser status from properties."""
        return self.get_property('is_superuser', False)
    
    @is_superuser.setter
    def is_superuser(self, value: bool):
        """Set superuser status in properties."""
        self.set_property('is_superuser', value)
    
    @property
    def entity_id(self) -> Optional[uuid.UUID]:
        """Get entity ID from properties (for backward compatibility)."""
        entity_id_str = self.get_property('entity_id')
        if entity_id_str:
            return uuid.UUID(entity_id_str)
        return self.id  # Use own ID as entity_id
    
    @entity_id.setter
    def entity_id(self, value: Optional[uuid.UUID]):
        """Set entity ID in properties (for backward compatibility)."""
        if value:
            self.set_property('entity_id', str(value))
        else:
            self.set_property('entity_id', str(self.id))
    
    # Password management methods
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def check_password(self, plain_password: str) -> bool:
        """
        Verify a password against this user's hashed password.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return self.verify_password(plain_password, self.hashed_password)
    
    # Query methods
    @classmethod
    def get_by_email(cls, db, email: str):
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "user",
            cls.properties['email'].astext == email
        ).first()
    
    @classmethod
    def get_active_users(cls, db, skip: int = 0, limit: int = 100):
        """
        Get all active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active user instances
        """
        return db.query(cls).filter(
            cls.entity_type == "user",
            cls.is_active == True
        ).offset(skip).limit(limit).all()
    
    @classmethod
    def get_by_entity_id(cls, db, entity_id):
        """
        Get user by entity ID.
        
        Args:
            db: Database session
            entity_id: Entity ID
            
        Returns:
            User instance or None
        """
        return db.query(cls).filter(
            cls.entity_type == "user",
            cls.id == entity_id
        ).first()
    
    def is_admin(self) -> bool:
        """
        Check if user is an admin.
        
        Returns:
            True if user is admin, False otherwise
        """
        return self.is_superuser or self.get_property('is_admin', False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
```

## Phase 3: Service Layer Updates

### Step 3.1: Update Project Service
**File**: `backend/app/services/project_service.py`

```python
# Update create_project method to use pure entity approach
def create_project(self, project_data: ProjectCreate, created_by: Optional[UUID] = None) -> Project:
    """
    Create a new project using pure entity approach.
    
    Args:
        project_data: Project creation data
        created_by: User ID who created the project
        
    Returns:
        The created project
        
    Raises:
        OrganizationNotFoundException: If organization not found
        UserNotFoundException: If project lead not found
        ValidationException: If data validation fails
        ServiceException: If creation fails
    """
    start_time = datetime.utcnow()
    
    try:
        # Validate project data
        self.validate_project_data(project_data)
        
        # Verify organization exists
        organization = self.db.query(Organization).filter(
            Organization.id == project_data.organization_id
        ).first()
        if not organization:
            raise OrganizationNotFoundException(f"Organization {project_data.organization_id} not found")
        
        # Verify project lead exists if provided
        if project_data.project_lead_id:
            project_lead = self.db.query(User).filter(
                User.id == project_data.project_lead_id
            ).first()
            if not project_lead:
                raise UserNotFoundException(f"User {project_data.project_lead_id} not found")
        
        # Create project using pure entity approach
        project = Project(
            name=project_data.name,
            description=project_data.description,
            organization_id=project_data.organization_id,
            status=project_data.status.value,
            priority=project_data.priority.value,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            expected_completion=project_data.expected_completion,
            project_lead_id=project_data.project_lead_id,
            budget=project_data.budget,
            progress_percentage=project_data.progress_percentage,
            tags=project_data.tags,
            project_metadata=project_data.project_metadata,
            settings=project_data.settings
        )
        
        # Save to database
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        # Audit log
        self.audit_log("project_created", project.id, {
            "name": project.name,
            "organization_id": str(project.organization_id),
            "created_by": str(created_by) if created_by else "system"
        })
        
        # Performance monitoring
        self.performance_monitor("project_creation", start_time)
        
        logger.info(f"Project created successfully: {project.name}")
        return project
        
    except IntegrityError as e:
        self.db.rollback()
        logger.error(f"Database integrity error during project creation: {e}")
        raise ServiceException("Failed to create project due to data conflict")
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error during project creation: {e}")
        raise ServiceException("Failed to create project")
```

### Step 3.2: Update Auth Service
**File**: `backend/app/services/auth_service.py`

```python
# Update user creation to use pure entity approach
def create_user(self, user_data: UserCreate) -> User:
    """
    Create a new user using pure entity approach.
    
    Args:
        user_data: User creation data
        
    Returns:
        The created user
        
    Raises:
        ValidationException: If data validation fails
        ServiceException: If creation fails
    """
    try:
        # Validate user data
        self.validate_user_data(user_data)
        
        # Check if email already exists
        existing_user = User.get_by_email(self.db, user_data.email)
        if existing_user:
            raise ValidationException("Email already registered")
        
        # Create user using pure entity approach
        user = User(
            name=user_data.name,
            description=user_data.description or "",
            email=user_data.email,
            hashed_password=User.hash_password(user_data.password),
            is_superuser=user_data.is_superuser or False,
            organization_id=user_data.organization_id,
            status="active"
        )
        
        # Save to database
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User created successfully: {user.email}")
        return user
        
    except IntegrityError as e:
        self.db.rollback()
        logger.error(f"Database integrity error during user creation: {e}")
        raise ServiceException("Failed to create user due to data conflict")
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error during user creation: {e}")
        raise ServiceException("Failed to create user")
```

## Phase 4: Schema Layer Updates

### Step 4.1: Update Project Schemas
**File**: `backend/app/schemas/project.py`

```python
# Update schema validation to work with pure entity approach
class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    organization_id: UUID = Field(..., description="Organization ID")
    project_lead_id: Optional[UUID] = Field(None, description="Project lead user ID")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Project priority")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    expected_completion: Optional[datetime] = Field(None, description="Expected completion date")
    budget: Optional[str] = Field(None, max_length=100, description="Project budget")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    project_metadata: Dict[str, Any] = Field(default_factory=dict, description="Project metadata")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Project settings")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Bioreactor Optimization Study",
                "description": "Study to optimize bioreactor parameters for maximum yield",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "project_lead_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "active",
                "priority": "high",
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": "2024-06-15T00:00:00Z",
                "expected_completion": "2024-05-15T00:00:00Z",
                "budget": "$50,000",
                "progress_percentage": 25,
                "tags": ["optimization", "bioreactor", "yield"],
                "project_metadata": {
                    "research_area": "biotechnology",
                    "funding_source": "internal"
                },
                "settings": {
                    "data_retention_days": 365,
                    "alert_thresholds": {
                        "temperature": {"min": 20, "max": 30},
                        "ph": {"min": 6.5, "max": 7.5}
                    }
                }
            }
        }
```

### Step 4.2: Update User Schemas
**File**: `backend/app/schemas/user.py`

```python
# Update schema validation to work with pure entity approach
class UserCreate(BaseModel):
    """Schema for creating a new user."""
    
    name: str = Field(..., min_length=1, max_length=255, description="User name")
    description: Optional[str] = Field(None, max_length=1000, description="User description")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    is_superuser: bool = Field(default=False, description="Superuser status")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "description": "Senior Research Scientist",
                "email": "john.doe@example.com",
                "password": "securepassword123",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_superuser": False
            }
        }
```

## Phase 5: Router Layer Updates

### Step 5.1: Update Project Router
**File**: `backend/app/routers/web/web_projects.py`

```python
# Update router to work with pure entity approach
@router.get("/projects/")
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List projects with optional filtering.
    
    Returns projects accessible to the current user with optional filtering
    by status and organization.
    """
    try:
        # Use service layer for project retrieval
        project_service = ProjectService(db)
        
        # Get projects for user's organization
        projects = project_service.get_projects_by_organization(
            organization_id=current_user.organization_id,
            status=status
        )
        
        # Apply pagination
        total = len(projects)
        projects = projects[skip:skip + limit]
        
        return {
            "projects": [project.to_dict() for project in projects],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")
```

### Step 5.2: Update Auth Router
**File**: `backend/app/routers/api/api_auth.py`

```python
# Update auth router to work with pure entity approach
@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with the provided information.
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(user_data)
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            organization_id=str(user.organization_id) if user.organization_id else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceException as e:
        logger.error(f"Service error during user registration: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")
```

## Phase 6: Testing Updates

### Step 6.1: Update Test Fixtures
**File**: `backend/tests/conftest.py`

```python
# Update test fixtures to work with pure entity approach
@pytest.fixture
def sample_project(db: Session) -> Project:
    """Create a sample project for testing."""
    project = Project(
        name="Test Project",
        description="A test project for unit testing",
        organization_id=uuid.uuid4(),
        status="active",
        priority="medium",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        budget="$10,000",
        progress_percentage=25,
        tags=["test", "unit-testing"],
        project_metadata={"test": True},
        settings={"data_retention_days": 30}
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@pytest.fixture
def sample_user(db: Session) -> User:
    """Create a sample user for testing."""
    user = User(
        name="Test User",
        description="A test user for unit testing",
        email="test@example.com",
        hashed_password=User.hash_password("testpassword123"),
        is_superuser=False,
        organization_id=uuid.uuid4(),
        status="active"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Step 6.2: Update Service Tests
**File**: `backend/tests/test_core/test_project_service.py`

```python
# Update project service tests for pure entity approach
def test_create_project_pure_entity(db: Session, sample_organization: Organization):
    """Test project creation using pure entity approach."""
    project_service = ProjectService(db)
    
    project_data = ProjectCreate(
        name="Test Project",
        description="Test project description",
        organization_id=sample_organization.id,
        status=ProjectStatus.ACTIVE,
        priority=ProjectPriority.MEDIUM,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        budget="$10,000",
        progress_percentage=0,
        tags=["test"],
        project_metadata={"test": True},
        settings={"data_retention_days": 30}
    )
    
    project = project_service.create_project(project_data)
    
    assert project.name == "Test Project"
    assert project.description == "Test project description"
    assert project.organization_id == sample_organization.id
    assert project.status == "active"
    assert project.priority == "medium"
    assert project.budget == "$10,000"
    assert project.progress_percentage == 0
    assert "test" in project.tags
    assert project.project_metadata["test"] is True
    assert project.settings["data_retention_days"] == 30
```

## Phase 7: Documentation Updates

### Step 7.1: Update API Documentation
**File**: `docs/backend/API_DOCUMENTATION.md`

```markdown
# API Documentation - Pure Entity Approach

## Overview

The LMS Core API now uses a pure entity approach where all entities (users, projects, organizations, devices) are stored in the `entities` table with specialized fields in the `properties` JSONB column.

## Entity Types

### Project Entities
- **entity_type**: `project`
- **properties**: Contains project-specific fields like start_date, end_date, budget, etc.

### User Entities
- **entity_type**: `user`
- **properties**: Contains user-specific fields like email, hashed_password, etc.

### Organization Entities
- **entity_type**: `organization`
- **properties**: Contains organization-specific fields like contact_email, address, etc.

## Benefits

1. **Consistency**: All entities follow the same pattern
2. **Flexibility**: Easy to add new entity types without schema changes
3. **Simplicity**: One table to rule them all
4. **Graph queries**: Better support for relationship queries
5. **Maintainability**: Less code duplication and complexity

## Migration Notes

- All existing data has been migrated to the pure entity approach
- Backward compatibility is maintained through property accessors
- No breaking changes to the API interface
```

### Step 7.2: Update Architecture Documentation
**File**: `docs/backend/ARCHITECTURE.md`

```markdown
# Architecture Documentation - Pure Entity Approach

## Data Model

### Single Table Inheritance
All entities in the system are stored in the `entities` table with the following structure:

```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    organization_id UUID REFERENCES entities(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

### Entity Types
- **project**: Laboratory projects with timeline, budget, progress tracking
- **user**: System users with authentication and profile information
- **organization**: Multi-tenant organizations with contact information
- **device**: IoT devices with sensor data and configuration
- **alert**: Alert rules and notification configurations

### Properties JSONB
Specialized fields for each entity type are stored in the `properties` JSONB column:

```json
// Project properties
{
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-06-15T00:00:00Z",
  "budget": "$50,000",
  "progress_percentage": 25,
  "tags": ["optimization", "bioreactor"],
  "organization_id": "123e4567-e89b-12d3-a456-426614174000"
}

// User properties
{
  "email": "john.doe@example.com",
  "hashed_password": "$2b$12$...",
  "is_superuser": false
}
```

## Benefits

1. **Consistency**: All entities work the same way
2. **Flexibility**: Easy to add new entity types
3. **Simplicity**: Single table design
4. **Graph queries**: Better relationship support
5. **Maintainability**: Less code duplication
```

## Phase 8: Cleanup and Validation

### Step 8.1: Remove Legacy Tables
**File**: `database/migrations/008_remove_legacy_tables.sql`

```sql
-- Remove legacy tables after successful migration
-- Only run after confirming all data has been migrated successfully

-- Drop projects table (data migrated to entities.properties)
DROP TABLE IF EXISTS projects CASCADE;

-- Drop users table (data migrated to entities.properties)
DROP TABLE IF EXISTS users CASCADE;

-- Drop organizations table (data migrated to entities.properties)
DROP TABLE IF EXISTS organizations CASCADE;

-- Update indexes for better performance
CREATE INDEX IF NOT EXISTS idx_entities_type_properties ON entities(entity_type) WHERE properties IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_entities_properties_gin ON entities USING GIN (properties);
```

### Step 8.2: Update Database Indexes
**File**: `database/migrations/009_optimize_entity_indexes.sql`

```sql
-- Optimize indexes for pure entity approach

-- Index for entity type queries
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);

-- Index for organization queries
CREATE INDEX IF NOT EXISTS idx_entities_organization ON entities(organization_id);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);

-- GIN index for JSONB properties queries
CREATE INDEX IF NOT EXISTS idx_entities_properties_gin ON entities USING GIN (properties);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_entities_type_org ON entities(entity_type, organization_id);
CREATE INDEX IF NOT EXISTS idx_entities_type_status ON entities(entity_type, status);
CREATE INDEX IF NOT EXISTS idx_entities_org_status ON entities(organization_id, status);

-- Partial indexes for active entities
CREATE INDEX IF NOT EXISTS idx_entities_active ON entities(entity_type, organization_id) WHERE is_active = true;
```

## Implementation Timeline

### Week 1: Database Migration
- [ ] Create migration scripts
- [ ] Test migration on development database
- [ ] Backup production data
- [ ] Execute migration on production
- [ ] Validate data integrity

### Week 2: Model Layer Updates
- [ ] Update Project model
- [ ] Update User model
- [ ] Update Organization model
- [ ] Add property accessors
- [ ] Update business logic methods

### Week 3: Service Layer Updates
- [ ] Update Project service
- [ ] Update Auth service
- [ ] Update Organization service
- [ ] Update query methods
- [ ] Add caching layer

### Week 4: Schema and Router Updates
- [ ] Update Pydantic schemas
- [ ] Update API routers
- [ ] Update WebSocket handlers
- [ ] Update dependency injection
- [ ] Add validation rules

### Week 5: Testing and Documentation
- [ ] Update test fixtures
- [ ] Update service tests
- [ ] Update API tests
- [ ] Update documentation
- [ ] Performance testing

### Week 6: Cleanup and Validation
- [ ] Remove legacy tables
- [ ] Optimize database indexes
- [ ] Performance validation
- [ ] Security review
- [ ] Production deployment

## Success Criteria

### Quantitative Metrics
1. **Data Integrity**: 100% of data successfully migrated
2. **Performance**: No performance degradation in API responses
3. **Test Coverage**: >90% test coverage for new entity approach
4. **Error Rate**: <0.1% error rate in production

### Qualitative Metrics
1. **Code Consistency**: All entities follow the same patterns
2. **Developer Experience**: Easier to add new entity types
3. **Maintainability**: Reduced code duplication
4. **Flexibility**: Easy to extend entity properties

## Risk Mitigation

### High Risk Areas
1. **Data Migration**: Comprehensive backup and rollback plan
2. **Performance**: Thorough performance testing before production
3. **Breaking Changes**: Maintain backward compatibility during transition
4. **Team Training**: Comprehensive documentation and training

### Mitigation Strategies
1. **Staged Migration**: Migrate one entity type at a time
2. **Rollback Plan**: Keep legacy tables until migration is validated
3. **Performance Monitoring**: Continuous performance monitoring during migration
4. **Team Communication**: Regular updates and training sessions

## Conclusion

This migration plan provides a comprehensive roadmap for transitioning from the hybrid approach to the pure entity approach. The plan ensures data integrity, maintains backward compatibility, and provides a clear path for team adoption.

The pure entity approach will provide significant benefits in terms of consistency, flexibility, and maintainability, making the LMS Core system more robust and easier to extend in the future. 