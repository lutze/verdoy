# Consolidated To-Do List: LMS Core POC

## 📊 **API ENDPOINT IMPLEMENTATION STATUS**

### **Analysis Summary**
Based on comparison between `API plan.md` and current `backend/app` implementation:

| Category | Total Planned | Fully Implemented | Partially Implemented | Missing |
|----------|---------------|-------------------|----------------------|---------|
| **Device Management** | 15+ | 15+ | 0 | 0 |
| **Device Commands** | 10+ | 10+ | 0 | 0 |
| **Authentication** | 8 | 8 | 0 | 0 |
| **WebSocket** | 3 | 0 | 3 | 0 |
| **Analytics** | 4 | 0 | 4 | 0 |
| **Alerts** | 7 | 0 | 7 | 0 |
| **Organizations** | 6 | 0 | 3 | 3 |
| **Billing** | 3 | 0 | 3 | 0 |
| **System** | 3 | 0 | 3 | 0 |
| **Admin** | 3 | 0 | 3 | 0 |
| **Data Export** | 3 | 0 | 0 | 3 |
| **User Account** | 1 | 0 | 0 | 1 |

**Overall**: ~70% of endpoints are **structurally present**, but ~50% are **functional stubs**.

---

### ✅ **FULLY IMPLEMENTED (All endpoints present and functional)**

#### **Device Management (`devices.py`)**
- ✅ **Device CRUD**: `GET/POST /devices`, `GET/PUT/DELETE /devices/{id}`
- ✅ **Device Status & Health**: `GET /devices/{id}/status`, `GET /devices/{id}/health`
- ✅ **Device Configuration**: `GET/PUT /devices/{id}/config`
- ✅ **Device Provisioning**: `POST /devices/provision`, `GET /devices/{id}/provision-status`
- ✅ **Data Ingestion**: `POST /devices/{id}/readings`, `POST /devices/{id}/heartbeat`, `POST /devices/{id}/status`
- ✅ **Data Retrieval**: `GET /devices/{id}/readings`, `GET /devices/{id}/readings/latest`
- ✅ **Device Control**: `POST /devices/{id}/reboot`

#### **Device Commands (`commands.py`)**
- ✅ **Command Queue**: `GET/POST /devices/{id}/commands`, `PUT /devices/{id}/commands/{cmd_id}/execute`
- ✅ **Device Polling**: `GET /devices/{id}/poll`
- ✅ **Device Control**: `POST /devices/{id}/control/restart`, `POST /devices/{id}/control/update-firmware`, `POST /devices/{id}/control/calibrate`, `POST /devices/{id}/control/set-reading-interval`
- ✅ **Command Management**: `GET/POST/PUT/DELETE /commands`, `GET /commands/{id}`
- ✅ **Command Templates**: `GET/POST /commands/templates`
- ✅ **Bulk Commands**: `POST /commands/bulk`

#### **Authentication (`auth.py`)**
- ✅ **User Registration**: `POST /auth/register`
- ✅ **User Login**: `POST /auth/login`
- ✅ **Token Management**: `POST /auth/logout`, `POST /auth/refresh`
- ✅ **Password Management**: `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/change-password`
- ✅ **User Profile**: `GET/PUT /auth/me` (equivalent to `/users/profile`)

---

### ⚠️ **PARTIALLY IMPLEMENTED (Endpoints exist but are stubs)**

#### **WebSocket Endpoints (All stubs)**
- ⚠️ `/ws/live-data` - **STUB**: Returns "Live data WebSocket not implemented."
- ⚠️ `/ws/device-status` - **STUB**: Returns "Device status WebSocket not implemented."
- ⚠️ `/ws/alerts` - **STUB**: Returns "Alerts WebSocket not implemented."

#### **Analytics (`analytics.py`)**
- ⚠️ `GET /analytics/summary` - **STUB**: Returns `{"summary": "Not implemented"}`
- ⚠️ `GET /analytics/trends` - **STUB**: Returns `{"trends": "Not implemented"}`
- ⚠️ `GET /analytics/alerts` - **STUB**: Returns `{"alerts": "Not implemented"}`
- ⚠️ `GET /analytics/reports` - **STUB**: Returns `{"reports": "Not implemented"}`

#### **Alerts (`alerts.py`)**
- ⚠️ `GET/POST /alerts/rules` - **STUB**: Returns `{"rules": "Not implemented"}`
- ⚠️ `PUT/DELETE /alerts/rules/{rule_id}` - **STUB**: Returns `{"rule": "Not implemented"}`
- ⚠️ `GET /alerts` - **STUB**: Returns `{"alerts": "Not implemented"}`
- ⚠️ `GET /alerts/active` - **STUB**: Returns `{"active_alerts": "Not implemented"}`
- ⚠️ `PUT /alerts/{alert_id}/acknowledge` - **STUB**: Returns `{"acknowledged": "Not implemented"}`

#### **Organizations (`organizations.py`)**
- ⚠️ `GET/POST /organizations` - **STUB**: Returns `{"organizations": "Not implemented"}`
- ⚠️ `GET /organizations/{org_id}` - **STUB**: Returns `{"organization": "Not implemented"}`

#### **Billing (`billing.py`)**
- ⚠️ `GET/POST /billing/subscription` - **STUB**: Returns `{"subscription": "Not implemented"}`
- ⚠️ `GET /billing/usage` - **STUB**: Returns `{"usage": "Not implemented"}`

#### **System (`system.py`)**
- ⚠️ `GET /system/health` - **STUB**: Returns `{"status": "ok"}`
- ⚠️ `GET /system/metrics` - **STUB**: Returns `{"metrics": "Not implemented"}`
- ⚠️ `GET /system/version` - **STUB**: Returns `{"version": "Not implemented"}`

#### **Admin (`admin.py`)**
- ⚠️ `GET /admin/users` - **STUB**: Returns `{"users": "Not implemented"}`
- ⚠️ `GET /admin/devices` - **STUB**: Returns `{"devices": "Not implemented"}`
- ⚠️ `GET /admin/stats` - **STUB**: Returns `{"stats": "Not implemented"}`

---

### ❌ **MISSING ENDPOINTS**

#### **Organization Team Management**
- ❌ `GET /organizations/{org_id}/members` - **MISSING**
- ❌ `POST /organizations/{org_id}/invite` - **MISSING**
- ❌ `DELETE /organizations/{org_id}/members/{user_id}` - **MISSING**

#### **Data Export & Streaming**
- ❌ `GET /readings/export` - **MISSING** (not in `readings.py`)
- ❌ `GET /api/v1/stream/readings` - **MISSING** (SSE endpoint)
- ❌ `GET /api/v1/stream/device-events` - **MISSING** (SSE endpoint)

#### **User Account Management**
- ❌ `DELETE /users/account` - **MISSING** (account deletion endpoint)

---

### 🎯 **PRIORITY RECOMMENDATIONS**

#### **High Priority (Critical for MVP)**
- [ ] **Implement WebSocket functionality** - Real-time data is core to IoT
- [ ] **Complete Analytics endpoints** - Dashboard functionality
- [ ] **Implement Alert rules** - Core monitoring feature

#### **Medium Priority**
- [ ] **Complete Organization team management** - Multi-tenant features
- [ ] **Implement System health/metrics** - Production monitoring
- [ ] **Add Data export functionality** - User data access

#### **Low Priority**
- [ ] **Complete Billing implementation** - Can be added later
- [ ] **Implement Admin endpoints** - Platform management
- [ ] **Add Account deletion** - User management

---

## 🚨 Critical Issues (Fix Immediately)

### ✅ **RESOLVED** - Authentication & Session Management (Fixed 21 July 2025)
- ✅ **Dual Authentication System**: Implemented JWT Bearer tokens for API clients and HTTP-only session cookies for web browsers
- ✅ **Session Security**: Secure cookie handling with httponly, secure, and samesite flags
- ✅ **Cross-Database Compatibility**: Fixed JSONType to handle both PostgreSQL (JSONB) and SQLite (TEXT) properly
- ✅ **Template System**: Created shared Jinja2 configuration with custom filters (number_format) across all routers
- ✅ **Login Flow**: Complete login → dashboard redirect with session persistence working end-to-end

### ✅ **RESOLVED** - Database & Template Infrastructure (Fixed 21 July 2025)
- ✅ **Database JSON Compatibility**: Fixed JSONType to handle PostgreSQL's auto-parsed JSONB vs SQLite's JSON strings
- ✅ **Shared Templates**: Created `templates_config.py` for consistent template configuration across routers
- ✅ **Custom Filters**: Added number_format filter for proper numeric display in templates
- ✅ **Template Data Flow**: Fixed dashboard stats data passing with proper Jinja2 context variables

### 1. Test Infrastructure & Data Validation (REMAINING)
- [ ] **Fix test database table creation** - Ensure `events` table is created in test setup
- [ ] **Update test fixtures** to match current schema requirements (DeviceCreate, UserCreate schemas)
- [ ] **Implement proper test isolation** to prevent "User already exists" errors
- [ ] **Add primary key defaults** to User model to fix SQLAlchemy warnings

### 2. Authorization & Status Code Alignment
- [ ] **Align expected status codes** with actual API behavior:
  - `test_get_alert_rules_unauthorized` expects 401, gets 403
  - `test_get_dashboard_data_unauthorized` expects 401, gets 404
- [ ] **Review and standardize** all authorization error responses

---

## 🔧 High Priority: Entity Graph Implementation

### 3. Reusable Helper Functions
- [ ] **Write helper functions** for entity graph queries:
  - Get all entities belonging to an organization (via `organization_id`)
  - Get all entities connected to a given entity (via `relationships` table)
  - Traverse the entity graph for multi-hop relationships
  - Filter connected entities by type (e.g., devices, users, etc.)

### 4. ORM Methods Enhancement
- [ ] **Add class methods** to the `Entity` model:
  - `get_connected_entities(self, db, relationship_type=None)`
  - `get_organization(self, db)`
  - `get_descendants(self, db, max_depth=None)`
- [ ] **Add convenience methods** to the `Organization` subclass

### 5. Query Pattern Documentation
- [ ] **Document common query patterns** for:
  - Direct membership (organization_id)
  - Graph traversal (relationships)
  - Filtering by entity type

---

## 🧪 Testing & Quality Assurance

### 6. Comprehensive Test Coverage
- [ ] **Add tests for all helper functions** and ORM methods
- [ ] **Test edge cases** (cycles, disconnected nodes, etc.)
- [ ] **Implement test scenarios** from PROCESS_FLOWS.md:
  - User registration tests (valid, duplicate email, invalid data, password strength)
  - Organization creation tests (valid, without user, duplicate names, user already in org)
  - Authentication tests (valid login, invalid credentials, deactivated account, token refresh)
  - Permission tests (superuser, org member, cross-org denial, resource-level)
  - Edge cases (user leaving org, org deletion with members, permission inheritance, audit trail)

### 7. Test Data Management
- [ ] **Create robust test fixtures** that work with current schema
- [ ] **Implement test data cleanup** between test runs
- [ ] **Add unique data generation** for tests to prevent conflicts

## 🔧 Current Test Issues (Priority Fixes)

### 1. Entities
- [x] **DateTime Comparison Error**: Fixed timezone handling in reading validation. The code now safely compares aware and naive datetimes.
- [x] **Reading Model Construction**: Refactored to use `entity_id` and `data` JSON field for sensor readings.
- [ ] **Test Database Table Creation**: Next step is to ensure the test database setup creates all tables, including `events` (required for Event/Reading models).

### 2. Test Data Validation Errors
- [ ] **Update test fixtures** to match current schema requirements
- [ ] **Issue**: Many tests failing due to Pydantic validation errors in test data
- [ ] **Examples**: DeviceCreate, UserCreate schemas need updated test data

### 3. Test Data Isolation
- [ ] **Implement proper test isolation** to prevent data conflicts
- [ ] **Issue**: "User already exists" errors due to test data persistence
- [ ] **Solution**: Clean up test data between tests or use unique data per test

### 4. Authorization Status Code Alignment
- [ ] **Align expected status codes** with actual API behavior
- [ ] **Issue**: Tests expect 401 but getting 403/404 for unauthorized access
- [ ] **Examples**: 
  - `test_get_alert_rules_unauthorized` expects 401, gets 403
  - `test_get_dashboard_data_unauthorized` expects 401, gets 404

### 5. Database Schema Issues
- [ ] **Add primary key defaults** where needed
- [ ] **Warning**: `Column 'users.id' is marked as a member of the primary key for table 'users', but has no Python-side or server-side default generator indicated`
- [ ] **Location**: User model primary key configuration


---

## 📚 Documentation & Process Implementation

### 8. Process Flow Implementation
- [ ] **Implement Process Flow 1**: User Registration (already partially done)
- [ ] **Implement Process Flow 2**: Organization Creation
- [ ] **Implement Process Flow 3**: User Authentication
- [ ] **Implement Process Flow 4**: User Permissions & Access Control
- [ ] **Implement Process Flow 5**: User-Organization Association

### 9. Security & Performance
- [ ] **Review password hashing** (ensure bcrypt is used)
- [ ] **Configure JWT token expiration** times appropriately
- [ ] **Add organization membership validation** on all resource access
- [ ] **Implement audit logging** for user and organization changes
- [ ] **Add database indexes** for performance:
  - Index on `entities.organization_id`
  - Index on `users.email`
  - Consider caching for permission checks

---

## 🔄 Database & Schema Improvements

### 10. Database Constraints & Validation
- [ ] **Verify foreign key constraints**:
  - `users.entity_id` must reference existing `entities.id`
  - `entities.organization_id` must reference existing `entities.id` when not NULL
- [ ] **Add database transactions** for multi-step operations
- [ ] **Consider recursive CTEs** for multi-hop traversals if supported by DB

### 11. Entity Relationship Management
- [ ] **Implement relationship table queries** for graph-style connections
- [ ] **Add relationship validation** to prevent invalid connections
- [ ] **Create relationship management** helper functions

---

## 📋 Implementation Examples (Reference)

### Example Queries to Implement:
```python
# All entities in an organization
entities = db.query(Entity).filter(Entity.organization_id == org_id).all()

# All entities directly connected to an entity
connected_ids = db.query(Relationship.to_entity).filter(Relationship.from_entity == entity_id).all()
connected_entities = db.query(Entity).filter(Entity.id.in_([row[0] for row in connected_ids])).all()

# All devices owned by an organization
owned_device_ids = db.query(Relationship.to_entity).filter(
    Relationship.from_entity == org_id,
    Relationship.relationship_type == "owns"
).all()
devices = db.query(Entity).filter(Entity.id.in_([row[0] for row in owned_device_ids]), Entity.entity_type == "device.esp32").all()
```

---

## 🎯 Success Criteria

### Phase 1 (Critical): Test Infrastructure
- [ ] All tests pass without data conflicts
- [ ] Test database setup creates all required tables
- [ ] Authorization status codes are consistent

### Phase 2 (High Priority): Entity Graph
- [ ] Helper functions implemented and tested
- [ ] ORM methods added to Entity model
- [ ] Query patterns documented

### Phase 3 (Medium Priority): Process Flows
- [ ] All 5 process flows implemented
- [ ] Security measures in place
- [ ] Performance optimizations added

### Phase 4 (Low Priority): Polish
- [ ] Comprehensive test coverage
- [ ] Documentation complete
- [ ] Audit logging implemented

---

## 📝 Notes
- Focus on Phase 1 first to establish stable testing foundation
- Entity graph implementation will unlock powerful querying capabilities
- Process flows provide the core business logic for user/org management
- All changes should maintain backward compatibility where possible 

---

# 📦 Additional Improvement Suggestions (from Code Reviews & Refactoring Docs)

## 🔥 Critical & High Priority

### Security
- [ ] Fix API key storage: move from plain text in JSONB to dedicated, hashed api_keys table
- [ ] Remove hard-coded secrets and insecure defaults from config
- [ ] Implement proper secret management and secret rotation
- [ ] Add input sanitization for all user inputs
- [ ] Implement audit logging for sensitive operations and user/org changes
- [ ] Add rate limiting per device/user
- [ ] Implement API key rotation mechanism
- [ ] Consider OAuth2 for user authentication
- [ ] Add security headers middleware

### Validation & Data Integrity
- [ ] Add Pydantic validators for email and MAC address fields
- [ ] Centralize validation logic for properties and business rules
- [ ] Add runtime type validation for JSONB properties (TypedDict)
- [ ] Implement data integrity checks and business rule validation

### Error Handling
- [ ] Standardize error handling patterns across all CRUD operations
- [ ] Create comprehensive error hierarchy and unified error handling
- [ ] Add error logging and monitoring
- [ ] Implement graceful degradation for service failures

### Testing
- [ ] Add unit tests for all CRUD operations and service layer
- [ ] Add integration tests for API endpoints and service interactions
- [ ] Add security tests for authentication and input validation
- [ ] Add performance/load tests for database and API
- [ ] Add end-to-end tests for complete workflows
- [ ] Add router and WebSocket tests
- [ ] Test migration layer (service/legacy delegation, fallback, performance)
- [ ] Test data isolation and cleanup between tests

### Service Layer & Integration
- [ ] Implement missing services: CommandService, AnalyticsService, AlertService, CacheService, BackgroundService, NotificationService, WebSocketService
- [ ] Move business logic from routers to service layer
- [ ] Update routers to use service layer via dependency injection
- [ ] Remove direct model/database calls from routers
- [ ] Add caching layer (e.g., Redis) for performance
- [ ] Implement background task processing (e.g., Celery)
- [ ] Add audit logging and performance monitoring in services

### API & Router Layer
- [ ] Update main.py to use new app structure and include all routers
- [ ] Remove legacy endpoints and imports
- [ ] Complete implementation of all planned endpoints (analytics, alerts, billing, org management, etc.)
- [ ] Implement real business logic for all endpoints (replace placeholders)
- [ ] Add pagination for all list endpoints
- [ ] Implement efficient query patterns and response caching
- [ ] Add request validation and error handling for all endpoints

### WebSocket & Real-Time
- [ ] Implement real-time data streaming for WebSocket endpoints
- [ ] Add WebSocket authentication and connection management
- [ ] Add error handling for WebSocket connections

### Database & Performance
- [ ] Add database indexes for common queries (entity_type, organization_id, JSONB fields)
- [ ] Implement connection pooling and query optimization
- [ ] Add transaction handling for multi-step operations
- [ ] Optimize JSONB queries and add pagination for large datasets
- [ ] Add database query monitoring and performance metrics

### Configuration
- [ ] Move all magic numbers and hardcoded values to configuration constants
- [ ] Provide clear .env template and configuration documentation
- [ ] Add environment-specific configuration validation

---

## 🟡 Medium Priority

### Code Quality & Maintainability
- [ ] Add comprehensive type hints throughout the codebase
- [ ] Reduce code duplication (base schemas, shared utilities, schema mixins)
- [ ] Extract validation logic to utility functions
- [ ] Add comprehensive docstrings and API documentation with examples
- [ ] Add usage and integration guides
- [ ] Implement error code system and localization support for error messages
- [ ] Add configuration injection and dependency injection patterns
- [ ] Implement event-driven architecture (event bus)

### Monitoring & Observability
- [ ] Add health checks, performance metrics, and distributed tracing
- [ ] Implement alert integration for error rates and service failures
- [ ] Add monitoring dashboards for service/legacy usage and migration progress

### Documentation
- [ ] Add OpenAPI/Swagger API documentation
- [ ] Document database schema and migration process
- [ ] Add security best practices, deployment, troubleshooting, and performance tuning guides
- [ ] Create migration guide and best practices documentation for teams

---

## 🟢 Low & Long-Term Priority

### Advanced Features & Enhancements
- [ ] Implement advanced analytics and reporting features
- [ ] Add machine learning capabilities for analytics
- [ ] Add real-time features and advanced notification channels (email, SMS, WebSocket)
- [ ] Implement horizontal scaling, microservice architecture, load balancing, and failover
- [ ] Add automatic migration progress tracking and rollback capabilities
- [ ] Add advanced caching strategies and background task processing
- [ ] Add security monitoring, audit log analysis, and access control enhancements
- [ ] Evaluate JSONB complexity vs. flexibility for future releases
- [ ] Consider event sourcing for audit and data changes

### Testing & Production Readiness
- [ ] Achieve >90% code coverage for all critical layers
- [ ] Add performance optimization recommendations and monitoring
- [ ] Implement deployment automation and production hardening
- [ ] Gradually remove deprecated endpoints and legacy code
- [ ] Add comprehensive monitoring and alerting for production

---

# 📝 Notes
- All items above are drawn from code review, refactoring, and QC documents and should be merged into sprint planning as appropriate.
- Prioritize security, validation, and error handling issues first for production readiness.
- Use this section as a reference for backlog grooming and technical debt tracking. 