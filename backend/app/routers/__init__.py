"""
Router package for the VerdoyLab API.

This package contains all API route handlers organized by domain:
- devices: Device management and IoT operations
- readings: Sensor data ingestion and retrieval
- commands: Device command and control
- analytics: Data analysis and reporting
- alerts: Alert management and notifications
- billing: Subscription and billing management
- system: System health and metrics
- admin: Administrative operations
- health: Health check endpoints
- websocket: Real-time WebSocket endpoints
"""

from .devices import router as devices_router
from .readings import router as readings_router
from .commands import router as commands_router
from .analytics import router as analytics_router
from .alerts import router as alerts_router
from .billing import router as billing_router
from .system import router as system_router
from .admin import router as admin_router
from .health import router as health_router
from .processes import router as processes_router

# WebSocket routers
from .websocket.live_data import router as live_data_ws_router
from .websocket.device_status import router as device_status_ws_router
from .websocket.alerts import router as alerts_ws_router

__all__ = [
    "devices_router",
    "readings_router",
    "commands_router",
    "analytics_router",
    "alerts_router",
    "billing_router",
    "system_router",
    "admin_router",
    "health_router",
    "processes_router",
    "live_data_ws_router",
    "device_status_ws_router",
    "alerts_ws_router",
] 