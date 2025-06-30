"""
Pytest configuration and fixtures for LMS Core API tests.

This module provides:
- Test database setup and teardown
- Common test fixtures
- Authentication helpers
- Service layer fixtures
"""

import pytest
import asyncio
import os
import tempfile
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

# Set test environment variables before importing app modules
os.environ["ENVIRONMENT"] = "test"
# Note: DATABASE_URL will be loaded from .env.test file
# SECRET_KEY will also be loaded from .env.test file

# Import from the correct module structure
from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.device import Device
from app.models.reading import Reading
from app.models.organization import Organization
from app.services.auth_service import AuthService
from app.services.device_service import DeviceService
from app.services.reading_service import ReadingService
from app.schemas.user import UserCreate
from app.schemas.device import DeviceCreate
from app.schemas.reading import ReadingCreate

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def test_db_setup(test_engine):
    """Set up test database tables."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up test database file
    try:
        os.remove("./test.db")
    except FileNotFoundError:
        pass

@pytest.fixture
def db_session(test_engine, test_db_setup):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """Create a test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_service(db_session):
    """Create AuthService instance for testing."""
    return AuthService(db_session)

@pytest.fixture
def device_service(db_session):
    """Create DeviceService instance for testing."""
    return DeviceService(db_session)

@pytest.fixture
def reading_service(db_session):
    """Create ReadingService instance for testing."""
    return ReadingService(db_session)

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User",
        "organization_id": None
    }

@pytest.fixture
def test_device_data() -> Dict[str, Any]:
    """Sample device data for testing."""
    return {
        "name": "Test Device",
        "serial_number": "TEST123456789",
        "device_type": "esp32",
        "model": "ESP32-WROOM-32",
        "firmware_version": "1.0.0",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "location": "Test Location",
        "description": "Test device for unit testing"
    }

@pytest.fixture
def test_reading_data() -> Dict[str, Any]:
    """Sample reading data for testing."""
    return {
        "device_id": None,  # Will be set in tests
        "sensor_type": "temperature",
        "value": 25.5,
        "unit": "celsius",
        "timestamp": "2024-01-01T12:00:00Z",
        "metadata": {
            "accuracy": 0.1,
            "location": "indoor"
        }
    }

@pytest.fixture
def test_user(auth_service, test_user_data) -> User:
    """Create a test user."""
    user_create = UserCreate(**test_user_data)
    return auth_service.register_user(user_create)

@pytest.fixture
def test_organization(db_session) -> Organization:
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        organization_type="business",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture
def test_device(device_service, test_device_data, test_organization) -> Device:
    """Create a test device."""
    device_create = DeviceCreate(**test_device_data)
    return device_service.register_device(device_create, test_organization.id)

@pytest.fixture
def authenticated_client(client, test_user, auth_service):
    """Create an authenticated test client."""
    # Login to get access token
    login_data = {
        "email": test_user.email,
        "password": "TestPassword123!"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    return client

@pytest.fixture
def sample_readings(reading_service, test_device) -> list:
    """Create sample readings for testing."""
    readings = []
    for i in range(5):
        reading_data = {
            "device_id": test_device.id,
            "sensor_type": "temperature",
            "value": 20.0 + i,
            "unit": "celsius",
            "timestamp": f"2024-01-01T12:0{i}:00Z",
            "metadata": {"test": True}
        }
        reading_create = ReadingCreate(**reading_data)
        reading = reading_service.create_reading(reading_create)
        readings.append(reading)
    
    return readings 