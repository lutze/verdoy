# CRUD Operations Implementation

This document describes the CRUD (Create, Read, Update, Delete) operations implemented for the LMS Core API.

## Overview

The CRUD operations are built on top of the existing graph-based database structure, using the `entities` table as the primary data store. The implementation includes:

- **Authentication & Authorization**: JWT-based user authentication and API key-based device authentication
- **Multi-tenant Support**: Organization-based access control
- **Event Sourcing**: All changes are recorded as events in the `events` table
- **Flexible Schema**: Device properties are stored as JSONB for flexibility

## Database Structure

### Core Tables

1. **entities**: Main table storing all "things" (devices, users, organizations)
2. **users**: Authentication table linked to entities
3. **events**: Immutable event log for all changes
4. **relationships**: Graph relationships between entities

### Key Features

- **organization_id**: Added to entities table for multi-tenant support
- **properties**: JSONB field storing flexible device configurations
- **Event tracking**: All CRUD operations create corresponding events

## API Endpoints

### Authentication

```
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # User login
GET  /api/v1/auth/me          # Get current user info
POST /api/v1/auth/refresh     # Refresh access token
```

### Device Management

```
GET    /api/v1/devices                    # List devices
POST   /api/v1/devices                    # Create device
GET    /api/v1/devices/{device_id}        # Get device details
PUT    /api/v1/devices/{device_id}        # Update device
DELETE /api/v1/devices/{device_id}        # Delete device
GET    /api/v1/devices/{device_id}/status # Device health/status
```

### IoT Data Ingestion

```
POST /api/v1/devices/{device_id}/readings # Receive sensor data
POST /api/v1/devices/{device_id}/heartbeat # Device heartbeat
GET  /api/v1/devices/{device_id}/readings # Get historical readings
```

## Authentication

### User Authentication

- **JWT Tokens**: 60-minute expiration
- **Password Hashing**: bcrypt with salt
- **Organization Access**: Users can only access their organization's resources

### Device Authentication

- **API Keys**: Generated automatically for each device
- **Device ID Validation**: API key must match device ID
- **Simple Storage**: API keys stored in device properties (for MVP)

## Data Models

### Device Properties Structure

```json
{
  "name": "Device Name",
  "location": "Device Location",
  "status": "online|offline|maintenance|error",
  "firmware": {
    "version": "1.0.0",
    "lastUpdate": "2024-01-01T00:00:00Z"
  },
  "hardware": {
    "model": "ESP32-WROOM-32",
    "macAddress": "24:6F:28:XX:XX:XX",
    "sensors": [...]
  },
  "config": {
    "readingInterval": 300,
    "alertThresholds": {...}
  },
  "lastSeen": "2024-01-01T00:00:00Z",
  "batteryLevel": 85,
  "api_key": "device_abc123def456",
  "metadata": {...}
}
```

### Sensor Reading Structure

```json
{
  "sensor_type": "temperature",
  "value": 23.5,
  "unit": "celsius",
  "timestamp": "2024-01-01T00:00:00Z",
  "quality": "good",
  "battery_level": 85
}
```

## Usage Examples

### Creating a Device

```python
import requests

# Login to get token
login_response = requests.post("http://localhost:8000/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = login_response.json()["access_token"]

# Create device
device_data = {
    "name": "My ESP32 Device",
    "description": "Temperature sensor in lab",
    "location": "Lab A",
    "firmware_version": "1.0.0",
    "hardware_model": "ESP32-WROOM-32",
    "mac_address": "24:6F:28:XX:XX:XX",
    "sensors": [
        {
            "type": "temperature",
            "unit": "celsius",
            "range": {"min": -40, "max": 125}
        }
    ],
    "reading_interval": 300
}

response = requests.post(
    "http://localhost:8000/api/v1/devices",
    json=device_data,
    headers={"Authorization": f"Bearer {token}"}
)

device = response.json()
print(f"Device created: {device['id']}")
```

### Sending Sensor Readings (Device)

```python
import requests

device_id = "your-device-id"
api_key = "device_abc123def456"  # From device properties

readings_data = {
    "readings": [
        {
            "sensor_type": "temperature",
            "value": 23.5,
            "unit": "celsius",
            "quality": "good",
            "battery_level": 85
        }
    ]
}

response = requests.post(
    f"http://localhost:8000/api/v1/devices/{device_id}/readings",
    json=readings_data,
    headers={"Authorization": f"Bearer {api_key}"}
)

print(f"Readings stored: {response.json()}")
```

## Testing

Run the test script to verify CRUD operations:

```bash
cd backend
python test_crud.py
```

This will:
1. Test health endpoint
2. Register a test user
3. Login and get token
4. Create a test device
5. List devices
6. Update device
7. Check device status

## Security Considerations

### Current Implementation (MVP)

- **Simple API Keys**: Stored in device properties
- **Basic JWT**: 60-minute expiration
- **Organization Isolation**: Basic access control

### Production Recommendations

- **Secure API Key Storage**: Use dedicated table with hashed keys
- **Key Rotation**: Implement API key rotation mechanism
- **Rate Limiting**: Add rate limiting for device endpoints
- **Audit Logging**: Enhanced event logging
- **HTTPS**: Enforce HTTPS in production
- **Environment Variables**: Move secrets to environment variables

## Database Migrations

The implementation includes migration `006_add_users_table.sql` which:

1. Adds `organization_id` column to entities table
2. Creates users table for authentication
3. Adds necessary indexes
4. Creates default organization for existing entities
5. Sets up triggers for timestamp updates

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Invalid credentials
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server errors

All errors return consistent JSON responses with error details.

## Next Steps

1. **Real-time Features**: Implement WebSocket endpoints
2. **Advanced Analytics**: Add aggregation endpoints
3. **Alert System**: Implement alert rules and notifications
4. **Device Commands**: Add command queue system
5. **Bulk Operations**: Support bulk device operations
6. **Export Features**: Add data export functionality 