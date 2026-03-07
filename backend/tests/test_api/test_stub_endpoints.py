"""
Tests for stub endpoints that return 501 Not Implemented.

These endpoints were changed from returning HTTP 200 with
{"summary": "Not implemented"} to proper 501 status codes.
This test file ensures they don't regress back to 200.
"""

import pytest
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def stub_app():
    """Create a minimal FastAPI app with stub routers for testing."""
    from app.routers.admin import router as admin_router
    from app.routers.billing import router as billing_router
    from app.routers.system import router as system_router

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1/admin")
    app.include_router(billing_router, prefix="/api/v1/billing")
    app.include_router(system_router, prefix="/api/v1/system")
    return app


@pytest.fixture(scope="module")
def stub_client(stub_app):
    """Create a test client for stub endpoints, with auth/db deps overridden."""
    from app.dependencies import get_db, get_current_user
    from app.models.user import User

    fake_user = User.__new__(User)
    object.__setattr__(fake_user, 'id', uuid4())
    object.__setattr__(fake_user, 'email', 'stub@test.com')

    def override_get_current_user():
        return fake_user

    def override_get_db():
        yield None

    stub_app.dependency_overrides[get_current_user] = override_get_current_user
    stub_app.dependency_overrides[get_db] = override_get_db

    with TestClient(stub_app) as client:
        yield client

    stub_app.dependency_overrides.clear()


class TestAdminStubEndpoints:
    """Admin endpoints should return 501."""

    def test_list_all_users_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/admin/users")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"

    def test_list_all_devices_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/admin/devices")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"

    def test_get_platform_stats_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/admin/stats")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"


class TestBillingStubEndpoints:
    """Billing endpoints should return 501."""

    def test_get_subscription_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/billing/subscription")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"

    def test_update_subscription_returns_501(self, stub_client):
        response = stub_client.post("/api/v1/billing/subscription")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"

    def test_get_usage_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/billing/usage")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"


class TestSystemEndpoints:
    """System endpoints: health returns 200, stubs return 501."""

    def test_health_check_returns_200(self, stub_client):
        response = stub_client.get("/api/v1/system/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_get_metrics_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/system/metrics")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"

    def test_get_version_returns_501(self, stub_client):
        response = stub_client.get("/api/v1/system/version")
        assert response.status_code == 501
        assert response.json()["detail"] == "Not implemented"
