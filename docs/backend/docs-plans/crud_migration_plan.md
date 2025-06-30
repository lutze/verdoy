# CRUD Operations Migration Plan
## Phase 6: Legacy to Service Layer Refactoring

### Overview
This document outlines the migration strategy for refactoring legacy CRUD operations from `backend/crud.py` to use the new service layer architecture.

---

## Current State Analysis

### Legacy CRUD Classes Identified:
1. **DeviceCRUD** - Device management operations
2. **UserCRUD** - User management operations  
3. **OrganizationCRUD** - Organization management operations
4. **ReadingCRUD** - Sensor data operations

### Legacy Models:
- `User` - User authentication and profile
- `Entity` - Generic entity storage (devices, users, organizations)
- `Relationship` - Entity relationships
- `Event` - Event logging and audit trail
- `Schema` - Data schema definitions
- `Process` - Process definitions
- `ProcessInstance` - Process execution instances

### Legacy Schemas:
- Authentication schemas (UserCreate, UserLogin, TokenResponse)
- Device schemas (DeviceCreate, DeviceUpdate, DeviceResponse)
- Reading schemas (SensorReading, DeviceReadingsRequest)
- Organization schemas (OrganizationCreate, OrganizationResponse)

---

## Migration Strategy

### 1. Service Layer Mapping

#### DeviceCRUD → DeviceService
```python
# Legacy: DeviceCRUD.create_device()
# New: DeviceService.register_device()

# Legacy: DeviceCRUD.get_device()
# New: DeviceService.get_by_id()

# Legacy: DeviceCRUD.get_devices()
# New: DeviceService.get_all()

# Legacy: DeviceCRUD.update_device()
# New: DeviceService.update()

# Legacy: DeviceCRUD.delete_device()
# New: DeviceService.delete()

# Legacy: DeviceCRUD.update_device_status()
# New: DeviceService.update_device_status()
```

#### UserCRUD → AuthService
```python
# Legacy: UserCRUD.create_user()
# New: AuthService.register_user()

# Legacy: UserCRUD.get_user_by_email()
# New: AuthService.get_user_by_email()

# Legacy: UserCRUD.get_user_by_id()
# New: AuthService.get_by_id()

# Legacy: UserCRUD.get_users()
# New: AuthService.get_all()
```

#### OrganizationCRUD → OrganizationService (to be created)
```python
# Legacy: OrganizationCRUD.create_organization()
# New: OrganizationService.create()

# Legacy: OrganizationCRUD.get_organization()
# New: OrganizationService.get_by_id()

# Legacy: OrganizationCRUD.get_organizations()
# New: OrganizationService.get_all()
```

#### ReadingCRUD → ReadingService
```python
# Legacy: ReadingCRUD.store_readings()
# New: ReadingService.bulk_ingest_readings()

# Legacy: ReadingCRUD.get_readings()
# New: ReadingService.get_readings_by_device()
```

### 2. Model Migration Strategy

#### Entity Model → Domain-Specific Models
```python
# Legacy: Entity with entity_type="device.esp32"
# New: Device model with specific fields

# Legacy: Entity with entity_type="user"
# New: User model with profile information

# Legacy: Entity with entity_type="organization"
# New: Organization model with specific fields
```

#### Event Model → Audit Logging
```python
# Legacy: Event for audit trail
# New: Service layer audit_log() method
```

### 3. Schema Migration Strategy

#### Legacy Schemas → New Schemas
```python
# Legacy: DeviceCreate, DeviceUpdate
# New: app/schemas/device.py schemas

# Legacy: UserCreate, UserLogin
# New: app/schemas/user.py schemas

# Legacy: OrganizationCreate
# New: app/schemas/organization.py schemas

# Legacy: SensorReading
# New: app/schemas/reading.py schemas
```

---

## Implementation Plan

### Phase 6.1: Create Missing Services (Priority 1)

#### 1. OrganizationService
```python
# File: app/services/organization_service.py
class OrganizationService(BaseService[Organization]):
    def create_organization(self, org_data: OrganizationCreate) -> Organization
    def get_organizations_by_user(self, user_id: UUID) -> List[Organization]
    def add_user_to_organization(self, user_id: UUID, org_id: UUID) -> bool
    def remove_user_from_organization(self, user_id: UUID, org_id: UUID) -> bool
```

#### 2. CommandService
```python
# File: app/services/command_service.py
class CommandService(BaseService[Command]):
    def send_command(self, device_id: UUID, command: CommandCreate) -> Command
    def get_pending_commands(self, device_id: UUID) -> List[Command]
    def mark_command_completed(self, command_id: UUID, result: Dict) -> Command
```

#### 3. AlertService
```python
# File: app/services/alert_service.py
class AlertService(BaseService[Alert]):
    def create_alert(self, alert_data: AlertCreate) -> Alert
    def get_active_alerts(self, organization_id: UUID) -> List[Alert]
    def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> Alert
```

### Phase 6.2: Update Legacy Files (Priority 2)

#### 1. Update crud.py
```python
# Add service layer imports
from app.services import AuthService, DeviceService, ReadingService, OrganizationService

# Update CRUD classes to use services
class DeviceCRUD:
    @staticmethod
    def create_device(db: Session, device_data: DeviceCreate, organization_id: Optional[UUID] = None, created_by: str = "system") -> Entity:
        device_service = DeviceService(db)
        return device_service.register_device(device_data, organization_id)
```

#### 2. Update models.py
```python
# Add imports for new models
from app.models.device import Device
from app.models.user import User
from app.models.organization import Organization

# Keep legacy models for backward compatibility
# Add migration notes
```

#### 3. Update schemas.py
```python
# Add imports for new schemas
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.organization import OrganizationCreate, OrganizationResponse

# Keep legacy schemas for backward compatibility
# Add deprecation warnings
```

### Phase 6.3: Router Integration (Priority 3)

#### 1. Update Legacy Routers
```python
# File: backend/routers/devices.py
from app.services import DeviceService

@router.get("/devices/")
async def get_devices(
    device_service: DeviceService = Depends(get_device_service),
    skip: int = 0,
    limit: int = 100
):
    return device_service.get_all(skip=skip, limit=limit)
```

#### 2. Update Dependencies
```python
# File: app/dependencies.py
def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    return DeviceService(db)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)
```

### Phase 6.4: Data Migration (Priority 4)

#### 1. Entity to Domain Model Migration
```sql
-- Migration script to convert Entity records to domain-specific models
-- Device entities → Device table
INSERT INTO devices (id, name, serial_number, device_type, organization_id, created_at)
SELECT id, name, properties->>'serial_number', entity_type, organization_id, created_at
FROM entities 
WHERE entity_type = 'device.esp32';

-- User entities → User profile information
UPDATE users 
SET name = (SELECT properties->>'name' FROM entities WHERE entities.id = users.entity_id)
WHERE entity_id IN (SELECT id FROM entities WHERE entity_type = 'user');
```

#### 2. Event to Audit Log Migration
```python
# Convert Event records to service layer audit logs
def migrate_events_to_audit_logs():
    events = db.query(Event).all()
    for event in events:
        # Convert to service layer audit format
        audit_log = {
            "action": event.event_type,
            "entity_id": event.entity_id,
            "timestamp": event.timestamp,
            "details": event.data
        }
        # Store in audit log system
```

---

## Backward Compatibility Strategy

### 1. Gradual Migration
- Keep legacy CRUD classes functional during transition
- Add deprecation warnings to legacy methods
- Provide migration guides for consumers

### 2. Dual Implementation
```python
# Legacy method with deprecation warning
@staticmethod
def create_device(db: Session, device_data: DeviceCreate, organization_id: Optional[UUID] = None, created_by: str = "system") -> Entity:
    import warnings
    warnings.warn("DeviceCRUD.create_device is deprecated. Use DeviceService.register_device instead.", DeprecationWarning)
    
    # Delegate to service layer
    device_service = DeviceService(db)
    return device_service.register_device(device_data, organization_id)
```

### 3. Configuration-Based Routing
```python
# Allow switching between legacy and new implementations
USE_SERVICE_LAYER = os.getenv("USE_SERVICE_LAYER", "true").lower() == "true"

def create_device(db: Session, device_data: DeviceCreate, **kwargs):
    if USE_SERVICE_LAYER:
        device_service = DeviceService(db)
        return device_service.register_device(device_data, **kwargs)
    else:
        # Legacy implementation
        return DeviceCRUD.create_device(db, device_data, **kwargs)
```

---

## Testing Strategy

### 1. Unit Tests
```python
# Test service layer methods
def test_device_service_register_device():
    device_service = DeviceService(db)
    device_data = DeviceCreate(name="Test Device", ...)
    device = device_service.register_device(device_data)
    assert device.name == "Test Device"

# Test legacy CRUD compatibility
def test_legacy_device_crud_compatibility():
    device_data = DeviceCreate(name="Test Device", ...)
    device = DeviceCRUD.create_device(db, device_data)
    assert device.name == "Test Device"
```

### 2. Integration Tests
```python
# Test end-to-end functionality
def test_device_creation_flow():
    # Test through router
    response = client.post("/api/v1/devices/", json=device_data)
    assert response.status_code == 200
    
    # Verify service layer was used
    # Verify audit logs were created
    # Verify database state
```

### 3. Performance Tests
```python
# Compare legacy vs new implementation performance
def test_performance_comparison():
    # Benchmark legacy CRUD
    start_time = time.time()
    DeviceCRUD.create_device(db, device_data)
    legacy_time = time.time() - start_time
    
    # Benchmark service layer
    start_time = time.time()
    device_service.register_device(device_data)
    service_time = time.time() - start_time
    
    assert service_time <= legacy_time * 1.1  # Allow 10% overhead
```

---

## Success Metrics

### 1. Functional Metrics
- ✅ All legacy CRUD operations successfully migrated
- ✅ No breaking changes to existing API endpoints
- ✅ All tests passing (unit, integration, performance)
- ✅ Data integrity maintained during migration

### 2. Performance Metrics
- 📈 Response times maintained or improved
- 📈 Database query efficiency improved
- 📈 Memory usage optimized
- 📈 Error rates reduced

### 3. Code Quality Metrics
- 📈 Code coverage >90% for service layer
- 📈 Reduced code duplication
- 📈 Improved maintainability scores
- 📈 Better separation of concerns

---

## Risk Mitigation

### 1. Data Loss Prevention
- Create comprehensive backups before migration
- Implement rollback procedures
- Test migration on staging environment first
- Monitor data integrity during migration

### 2. Performance Impact
- Implement gradual rollout with feature flags
- Monitor performance metrics during transition
- Have rollback plan ready
- Test with production-like data volumes

### 3. Breaking Changes
- Maintain backward compatibility during transition
- Provide clear migration documentation
- Implement deprecation warnings
- Support both implementations during transition period

---

## Timeline

### Week 1: Foundation
- Create missing services (OrganizationService, CommandService, AlertService)
- Update service layer imports and dependencies
- Add comprehensive unit tests

### Week 2: Migration
- Update legacy CRUD classes to use service layer
- Implement backward compatibility layer
- Add deprecation warnings and migration guides

### Week 3: Integration
- Update router dependencies
- Test end-to-end functionality
- Performance testing and optimization

### Week 4: Validation
- Comprehensive testing and validation
- Documentation updates
- Production deployment preparation

---

## Conclusion

This migration plan provides a structured approach to refactoring legacy CRUD operations to use the new service layer architecture. The phased approach ensures minimal disruption while providing clear benefits in terms of code quality, maintainability, and performance.

The key success factors are:
1. **Gradual migration** with backward compatibility
2. **Comprehensive testing** at all levels
3. **Clear documentation** and migration guides
4. **Performance monitoring** throughout the process
5. **Rollback procedures** for risk mitigation 