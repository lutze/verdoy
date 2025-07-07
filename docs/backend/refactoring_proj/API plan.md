# API implementation plan

## MVP Priority Order

**Phase 1 (Essential)**:

- Basic device CRUD
- Reading ingestion (`POST /devices/{id}/readings`)
- Basic data retrieval (`GET /devices/{id}/readings`)

**Phase 2 (Core Features)**:

- Real-time WebSocket
- Device commands
- Alert rules
- Analytics endpoints

**Phase 3 (Auth)**:

- Authentication routes

**Phase 4 (Enhanced)**:

- Organization management
- Advanced analytics
- Billing integration
- Admin features


## Authentication & User Management

```python
# User registration/authentication
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
POST   /api/v1/auth/reset-password
GET    /api/v1/auth/me

# User profile management
GET    /api/v1/users/profile
PUT    /api/v1/users/profile
DELETE /api/v1/users/account
```

## Device Management (Web Interface)

```python
# Device CRUD operations
GET    /api/v1/devices                    # List user's devices
POST   /api/v1/devices                    # Register new device
GET    /api/v1/devices/{device_id}        # Get device details
PUT    /api/v1/devices/{device_id}        # Update device (name, location, etc.)
DELETE /api/v1/devices/{device_id}        # Remove device

# Device status and health
GET    /api/v1/devices/{device_id}/status # Current status, last seen, etc.
GET    /api/v1/devices/{device_id}/health # Health metrics, diagnostics
POST   /api/v1/devices/{device_id}/reboot # Trigger device reboot

# Device configuration
GET    /api/v1/devices/{device_id}/config # Get device configuration
PUT    /api/v1/devices/{device_id}/config # Update device settings
```

## IoT Data Ingestion (Device → Server)

```python
# Sensor data ingestion (called by ESP32 devices)
POST   /api/v1/devices/{device_id}/readings        # Batch sensor readings
POST   /api/v1/devices/{device_id}/heartbeat       # Device keep-alive
POST   /api/v1/devices/{device_id}/status          # Device status updates
POST   /api/v1/devices/{device_id}/logs            # Device error/debug logs

# Device registration/provisioning
POST   /api/v1/devices/provision                   # Initial device setup
GET    /api/v1/devices/{device_id}/provision-status # Check provisioning
```

## IoT Commands & Control (Server → Device)

```python
# Command queue for devices
GET    /api/v1/devices/{device_id}/commands        # Device polls for commands
POST   /api/v1/devices/{device_id}/commands        # Queue command for device
PUT    /api/v1/devices/{device_id}/commands/{cmd_id} # Mark command as executed

# Direct device control (web interface)
POST   /api/v1/devices/{device_id}/control/restart
POST   /api/v1/devices/{device_id}/control/update-firmware
POST   /api/v1/devices/{device_id}/control/calibrate
POST   /api/v1/devices/{device_id}/control/set-reading-interval
```

## Data Retrieval & Analytics (Web Dashboard)

```python
# Historical data queries
GET    /api/v1/readings                            # Query readings across devices
GET    /api/v1/readings/latest                     # Latest readings from all devices
GET    /api/v1/readings/export                     # Export data (CSV/JSON)

# Device-specific data
GET    /api/v1/devices/{device_id}/readings        # Historical readings
GET    /api/v1/devices/{device_id}/readings/latest # Latest readings
GET    /api/v1/devices/{device_id}/readings/stats  # Statistical summaries

# Analytics and aggregations
GET    /api/v1/analytics/summary                   # Dashboard summary
GET    /api/v1/analytics/trends                    # Time-based trends
GET    /api/v1/analytics/alerts                    # Active alerts/notifications
GET    /api/v1/analytics/reports                   # Predefined reports
```

## Real-time & WebSocket

```python
# WebSocket endpoints for real-time data
WS     /ws/live-data                               # Live sensor readings
WS     /ws/device-status                          # Device online/offline events
WS     /ws/alerts                                 # Real-time alerts

# Server-Sent Events alternative
GET    /api/v1/stream/readings                    # SSE for live readings
GET    /api/v1/stream/device-events              # SSE for device events
```

## Alerts & Notifications

```python
# Alert rules management
GET    /api/v1/alerts/rules                       # List alert rules
POST   /api/v1/alerts/rules                       # Create alert rule
PUT    /api/v1/alerts/rules/{rule_id}            # Update alert rule
DELETE /api/v1/alerts/rules/{rule_id}            # Delete alert rule

# Alert history and management
GET    /api/v1/alerts                             # Alert history
PUT    /api/v1/alerts/{alert_id}/acknowledge      # Mark alert as seen
GET    /api/v1/alerts/active                      # Currently active alerts
```

## Organization & Account Management

```python
# Organization management (for multi-tenant)
GET    /api/v1/organizations                      # User's organizations
POST   /api/v1/organizations                      # Create organization
GET    /api/v1/organizations/{org_id}            # Organization details
PUT    /api/v1/organizations/{org_id}            # Update organization

# Team management
GET    /api/v1/organizations/{org_id}/members     # Team members
POST   /api/v1/organizations/{org_id}/invite      # Invite team member
DELETE /api/v1/organizations/{org_id}/members/{user_id} # Remove member

# Billing and subscriptions
GET    /api/v1/billing/subscription               # Current plan
POST   /api/v1/billing/subscription               # Update subscription
GET    /api/v1/billing/usage                      # Usage statistics
```

## System & Admin

```python
# System status
GET    /api/v1/system/health                      # API health check
GET    /api/v1/system/metrics                     # System metrics
GET    /api/v1/system/version                     # API version info

# Admin endpoints (for platform management)
GET    /api/v1/admin/users                        # All users (admin only)
GET    /api/v1/admin/devices                      # All devices (admin only)
GET    /api/v1/admin/stats                        # Platform statistics
```

## Sample FastAPI Implementation Structure

```python
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer
import asyncio

app = FastAPI(title="IoT SaaS API", version="1.0.0")

# Example route implementations
@app.post("/api/v1/devices/{device_id}/readings")
async def receive_readings(
    device_id: str,
    readings: List[SensorReading],
    api_key: str = Depends(get_device_api_key)
):
    """Receive batch sensor readings from ESP32 device"""
    device = await get_device_by_id_and_key(device_id, api_key)
    if not device:
        raise HTTPException(401, "Invalid device credentials")
    
    await store_readings_batch(device_id, readings)
    await update_device_last_seen(device_id)
    
    return {"status": "ok", "readings_stored": len(readings)}

@app.get("/api/v1/devices")
async def list_devices(user: User = Depends(get_current_user)):
    """List all devices for the authenticated user"""
    devices = await get_user_devices(user.id)
    return {"devices": devices}

@app.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time sensor data"""
    user = await authenticate_websocket(token)
    await websocket.accept()
    
    try:
        while True:
            # Send live data to client
            data = await get_latest_readings(user.id)
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
```



