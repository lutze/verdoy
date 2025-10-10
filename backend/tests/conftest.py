"""
Pytest configuration and fixtures for VerdoyLab API tests.

This module provides shared fixtures and configuration for all test modules.
"""

import asyncio
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Generator
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment variables BEFORE importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long-for-testing"

# Import your app dependencies
from backend.app.database import get_db
from backend.app.models.base import Base
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.entity import Entity
from backend.app.models.device import Device
from backend.app.models.organization import Organization
from backend.app.schemas.user import UserCreate
from backend.app.schemas.device import DeviceCreate
from backend.app.services.auth_service import AuthService
from backend.app.services.device_service import DeviceService
from backend.app.services.reading_service import ReadingService
from backend.app.services.project_service import ProjectService

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create only the tables we need for testing (exclude legacy models with JSONB)
    # Import Base directly to avoid importing legacy models
    from sqlalchemy.orm import declarative_base
    TestBase = declarative_base()
    
    # Import only the models we need for testing
    from app.models.entity import Entity
    from app.models.user import User
    from app.models.device import Device
    from app.models.reading import Reading
    from app.models.alert import Alert, AlertRule
    from app.models.organization import Organization
    from app.models.organization_member import OrganizationMember
    from app.models.organization_invitation import OrganizationInvitation
    from app.models.membership_removal_request import MembershipRemovalRequest
    from app.models.billing import Billing, Subscription
    from app.models.command import Command
    from app.models.event import Event
    from app.models.relationship import Relationship
    
    # Create tables for entity-based models only
    TestBase.metadata.create_all(bind=engine)
    
    yield engine
    TestBase.metadata.drop_all(bind=engine)
    # Clean up test database file
    try:
        os.remove("./test.db")
    except FileNotFoundError:
        pass

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function") 
def test_app():
    """Create a test FastAPI app without production lifespan."""
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        # No database initialization for tests
        yield
        
    app = FastAPI(
        title="VerdoyLab API - Test",
        version="1.0.0",
        lifespan=test_lifespan
    )
    
    # Import and include routers
    from app.routers.alerts import router as alerts_router
    from app.routers.analytics import router as analytics_router
    from app.routers.commands import router as commands_router
    from app.routers.devices import router as devices_router
    from app.routers.readings import router as readings_router
    from app.routers.processes import router as processes_router
    
    # Include routers for testing
    # Auth endpoints are now in app.routers.api.api_auth
    from app.routers.api.api_auth import router as api_auth_router
    app.include_router(api_auth_router)
    app.include_router(alerts_router, prefix="/api/v1/alerts")
    app.include_router(analytics_router, prefix="/api/v1/analytics")
    app.include_router(commands_router, prefix="/api/v1/commands")
    app.include_router(devices_router, prefix="/api/v1/devices")
    app.include_router(readings_router, prefix="/api/v1/readings")
    app.include_router(processes_router, prefix="/api/v1/processes")
    from app.routers.api.api_organizations import router as api_organizations_router
    from app.routers.api.api_projects import router as api_projects_router
    app.include_router(api_organizations_router)
    app.include_router(api_projects_router)
    
    return app

@pytest.fixture(scope="function")
def client(test_app, db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override database dependency
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client
    
    test_app.dependency_overrides.clear()

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
    """Sample user data for testing with unique email."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test-{unique_id}@example.com",
        "password": "TestPassword123!",
        "name": f"Test User {unique_id}",
        "organization_id": None
    }

@pytest.fixture
def test_device_data() -> Dict[str, Any]:
    """Sample device data for testing with unique identifiers."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test Device {unique_id}",
        "serial_number": f"TEST{unique_id.upper()}",
        "device_type": "esp32",
        "model": "ESP32-WROOM-32",
        "firmware_version": "1.0.0",
        "mac_address": f"AA:BB:CC:DD:{unique_id[:2].upper()}:{unique_id[2:4].upper()}",
        "location": f"Test Location {unique_id}",
        "description": f"Test device for unit testing {unique_id}"
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
    """Create a test user with unique data."""
    user_create = UserCreate(**test_user_data)
    return auth_service.register_user(user_create)

@pytest.fixture
def test_organization(db_session) -> Organization:
    """Create a test organization with unique data."""
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name=f"Test Organization {unique_id}",
        description=f"Test organization for unit testing {unique_id}",
        properties={
            'organization_type': 'business',
            'contact_email': f'test-{unique_id}@organization.com',
            'website': f'https://test-org-{unique_id}.com',
            'member_count': 0
        }
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture
def test_device(device_service, test_device_data, test_organization) -> Device:
    """Create a test device with unique data."""
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
    print("DEBUG login response:", response.json())
    token_data = response.json()
    access_token = token_data["data"]["access_token"]
    
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
        reading = reading_service.create_reading(reading_data)
        readings.append(reading)
    
    return readings

@pytest.fixture  
def project_service(db_session) -> ProjectService:
    """Create ProjectService instance for testing."""
    return ProjectService(db_session)

@pytest.fixture
def process_service(db_session):
    """Create ProcessServiceEntity instance for testing."""
    from app.services.process_service_entity import ProcessServiceEntity
    return ProcessServiceEntity(db_session) 