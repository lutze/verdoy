# API Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the LMS Core API, covering all endpoints across all domains.

## Testing Pyramid

```
    /\
   /  \     E2E Tests (Few)
  /____\    Integration Tests (Some)
 /______\   Unit Tests (Many)
```

## Test Categories

### 1. Unit Tests (`test_core/`)
- **Purpose**: Test individual service functions and business logic
- **Scope**: Service layer, utilities, models
- **Speed**: Fast (< 100ms per test)
- **Coverage**: High (90%+)

### 2. API Tests (`test_api/`)
- **Purpose**: Test HTTP endpoints and request/response handling
- **Scope**: Router endpoints, authentication, validation
- **Speed**: Medium (100-500ms per test)
- **Coverage**: All endpoints

### 3. Integration Tests (`test_integration/`)
- **Purpose**: Test complete workflows and database interactions
- **Scope**: End-to-end scenarios, data persistence
- **Speed**: Slow (500ms-2s per test)
- **Coverage**: Critical user journeys

## Test Structure

### Current Test Files
```
backend/tests/
├── conftest.py              # ✅ Shared fixtures and setup
├── test_api/
│   ├── test_auth.py         # ✅ Authentication endpoints
│   ├── test_devices.py      # ✅ Device management endpoints
│   ├── test_readings.py     # ✅ Data ingestion endpoints
│   ├── test_commands.py     # ✅ Device control endpoints
│   ├── test_alerts.py       # ✅ Alert management endpoints
│   ├── test_analytics.py    # ✅ Analytics endpoints
│   ├── test_organizations.py # ⏳ Organization management
│   ├── test_billing.py      # ⏳ Billing and subscriptions
│   ├── test_admin.py        # ⏳ Admin functions
│   └── test_system.py       # ⏳ System endpoints
├── test_core/
│   ├── test_auth_service.py # ✅ Auth service logic
│   ├── test_device_service.py # ✅ Device service logic
│   └── test_reading_service.py # ✅ Reading service logic
└── test_integration/
    └── (to be implemented)
```

## Test Coverage Requirements

### Authentication & User Management
- [x] User registration (success/failure cases)
- [x] User login/logout
- [x] Token refresh
- [x] Password reset
- [x] Profile management
- [ ] User account deletion

### Device Management
- [x] Device registration
- [x] Device CRUD operations
- [x] Device status monitoring
- [x] Device configuration
- [x] Device provisioning
- [ ] Device logs
- [ ] Device reading stats

### Data Ingestion
- [x] Reading submission
- [x] Reading retrieval and filtering
- [x] Reading aggregation
- [x] Data export
- [x] Latest readings
- [ ] Reading validation

### Device Control
- [x] Command creation
- [x] Command execution
- [x] Command status tracking
- [x] Command cancellation
- [x] Command history
- [ ] Command validation

### Alerts & Monitoring
- [x] Alert rule creation
- [x] Alert rule management
- [x] Alert acknowledgment
- [x] Alert statistics
- [ ] Alert escalation
- [ ] Alert notifications

### Analytics
- [x] Dashboard data
- [x] Trend analysis
- [x] Performance metrics
- [x] Forecasting
- [x] Anomaly detection
- [x] Data comparison

### Organizations
- [ ] Organization CRUD
- [ ] User organization management
- [ ] Organization settings
- [ ] Multi-tenancy

### Billing
- [ ] Subscription management
- [ ] Usage tracking
- [ ] Payment processing
- [ ] Invoice generation

### Admin Functions
- [ ] User management
- [ ] System configuration
- [ ] Audit logs
- [ ] System health

### System
- [ ] Health checks
- [ ] System info
- [ ] Configuration
- [ ] Maintenance

## Test Patterns

### 1. Arrange-Act-Assert (AAA)
```python
def test_example(self, authenticated_client: TestClient):
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    response = authenticated_client.post("/api/v1/endpoint", json=test_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "value"
```

### 2. Happy Path + Edge Cases
- **Happy Path**: Normal successful operation
- **Validation Errors**: Invalid input data
- **Authentication Errors**: Unauthorized access
- **Authorization Errors**: Insufficient permissions
- **Not Found Errors**: Missing resources
- **Business Logic Errors**: Invalid state transitions

### 3. Fixture-Based Setup
```python
@pytest.fixture
def test_user(auth_service, test_user_data) -> User:
    """Create a test user."""
    user_create = UserCreate(**test_user_data)
    return auth_service.register_user(user_create)

@pytest.fixture
def authenticated_client(client, test_user, auth_service):
    """Create an authenticated test client."""
    # Login and set auth headers
    return client
```

## Test Data Management

### Test Database
- **SQLite in-memory** for unit tests and API tests
- **PostgreSQL test instance** for integration tests
- **Automatic cleanup** after each test
- **Cross-database JSON compatibility** using custom `JSONType` for PostgreSQL (`JSONB`) and SQLite support

### Test Data Fixtures
```python
@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }

@pytest.fixture
def sample_readings(reading_service, test_device) -> list:
    """Create sample readings for testing."""
    readings = []
    for i in range(5):
        # Create test readings
    return readings
```

## Running Tests

### Individual Test Files
```bash
# Run specific test file
pytest backend/tests/test_api/test_auth.py -v

# Run specific test class
pytest backend/tests/test_api/test_auth.py::TestAuthEndpoints -v

# Run specific test method
pytest backend/tests/test_api/test_auth.py::TestAuthEndpoints::test_register_user_success -v
```

### Test Categories
```bash
# Run all API tests
pytest backend/tests/test_api/ -v

# Run all unit tests
pytest backend/tests/test_core/ -v

# Run all tests with coverage
pytest --cov=app --cov-report=html
```

### Test Markers
```bash
# Run fast tests only
pytest -m "not slow" -v

# Run integration tests only
pytest -m integration -v

# Run API tests only
pytest -m api -v
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Quality Metrics

### Coverage Targets
- **Overall Coverage**: 90%+
- **API Endpoints**: 100%
- **Service Layer**: 95%+
- **Models**: 80%+

### Performance Targets
- **Unit Tests**: < 100ms per test
- **API Tests**: < 500ms per test
- **Integration Tests**: < 2s per test
- **Full Test Suite**: < 5 minutes

### Quality Gates
- All tests must pass
- Coverage must meet targets
- No critical security vulnerabilities
- Performance benchmarks met

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fresh database state
- Clean up test data

### 2. Descriptive Names
```python
def test_register_user_with_duplicate_email_fails(self):
    """Test that registration with duplicate email returns 400 error."""
```

### 3. Comprehensive Assertions
```python
# Good
assert response.status_code == 201
data = response.json()
assert "id" in data
assert data["email"] == test_user_data["email"]
assert "password" not in data  # Security check

# Avoid
assert response.status_code == 201  # Too minimal
```

### 4. Error Testing
```python
def test_invalid_input_returns_422(self):
    """Test that invalid input returns validation error."""
    response = client.post("/api/v1/endpoint", json={"invalid": "data"})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
```

### 5. Authentication Testing
```python
def test_unauthorized_access_returns_401(self):
    """Test that unauthorized access returns 401."""
    response = client.get("/api/v1/protected-endpoint")
    assert response.status_code == 401
```

## Implementation Plan

### Phase 1: Core API Tests (Complete)
- [x] Authentication endpoints
- [x] Device management endpoints
- [x] Data ingestion endpoints

### Phase 2: Extended API Tests (Complete)
- [x] Device control endpoints
- [x] Alert management endpoints
- [x] Analytics endpoints
- [ ] Organization management

### Phase 3: Advanced Features (In Progress)
- [ ] Billing and subscriptions
- [ ] Admin functions
- [ ] System endpoints
- [ ] WebSocket endpoints

### Phase 4: Integration Tests (Planned)
- [ ] End-to-end user workflows
- [ ] Database integration tests
- [ ] External service integration
- [ ] Performance tests

## Recent Achievements

### Database Model Improvements
- **Single-table inheritance** implemented for entities with proper polymorphic identities
- **Bi-directional relationships** established between User and Entity models
- **JSON compatibility layer** created for cross-database support
- **Foreign key constraints** resolved for polymorphic entity relationships

### Test Infrastructure Enhancements
- **Environment variable overrides** for SQLite testing
- **Comprehensive fixture setup** with proper authentication and data seeding
- **Cross-database compatibility** ensuring tests run consistently
- **Model inheritance testing** with proper polymorphic identity handling

## Monitoring and Maintenance

### Regular Tasks
- **Weekly**: Review test failures and flaky tests
- **Monthly**: Update test data and fixtures
- **Quarterly**: Review and update test strategy
- **Annually**: Comprehensive test suite audit

### Metrics to Track
- Test execution time
- Test coverage trends
- Flaky test frequency
- Test maintenance effort
- Bug detection rate

This testing strategy ensures comprehensive coverage of all API endpoints while maintaining high code quality and reliability. 