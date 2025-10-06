# Data Model Overview

This document provides a comprehensive overview of the data structures in the VerdoyLab system, including database schema, models, and data flow patterns.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Database Schema](#core-database-schema)
3. [Entity-Based Data Model](#entity-based-data-model)
4. [Event-Driven Data Flow](#event-driven-data-flow)
5. [Domain-Specific Models](#domain-specific-models)
6. [Data Validation Layer](#data-validation-layer)
7. [Migration Strategy](#migration-strategy)

## Architecture Overview

The VerdoyLab system uses a **pure entity approach** with an **event-driven architecture** for data management. This design provides:

- **Flexibility**: All entities stored in a single table with type-specific properties in JSONB
- **Auditability**: Complete event history for all system changes
- **Scalability**: Time-series optimized storage with TimescaleDB
- **Extensibility**: Schema evolution without breaking changes

### Key Design Principles

1. **Entity-First Design**: All system objects (users, devices, organizations, etc.) are stored as entities
2. **Event Sourcing**: All changes tracked as immutable events
3. **JSONB Flexibility**: Type-specific data stored in flexible JSONB columns
4. **Graph Relationships**: Entity connections managed through relationships table
5. **Schema Evolution**: Versioned schemas for data validation and evolution

## Core Database Schema

### Primary Tables

#### `entities` - Canonical Entity Storage
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    organization_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

**Purpose**: Stores all system entities (users, devices, organizations, projects, etc.)

**Key Features**:
- **Polymorphic Storage**: All entity types in single table
- **Flexible Properties**: Type-specific data in JSONB
- **Organization Hierarchy**: Self-referencing organization structure
- **Soft Deletes**: `is_active` flag for data retention

#### `events` - Immutable Event Log
```sql
CREATE TABLE events (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    event_metadata JSONB DEFAULT '{}',
    source_node VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, id)
);
```

**Purpose**: Tracks all system changes as immutable events

**Key Features**:
- **Time-Series Optimized**: TimescaleDB hypertable for efficient time-based queries
- **Complete Audit Trail**: All changes preserved forever
- **Rich Metadata**: Event-specific data and metadata
- **Distributed Ready**: Source node tracking for multi-node deployments

#### `relationships` - Graph Structure
```sql
CREATE TABLE relationships (
    id BIGSERIAL PRIMARY KEY,
    from_entity UUID NOT NULL REFERENCES entities(id),
    to_entity UUID NOT NULL REFERENCES entities(id),
    relationship_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    strength DECIMAL(3,2) DEFAULT 1.0,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);
```

**Purpose**: Manages connections between entities (device monitors equipment, user belongs to organization, etc.)

**Key Features**:
- **Directed Graph**: From/to entity relationships
- **Temporal Validity**: Time-bounded relationships
- **Relationship Strength**: Quantitative relationship metrics
- **Flexible Properties**: Relationship-specific data

### Supporting Tables

#### `schemas` - Schema Definitions
```sql
CREATE TABLE schemas (
    id VARCHAR(100) PRIMARY KEY,
    version INTEGER NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,
    description TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,
    created_by VARCHAR(100)
);
```

**Purpose**: Versioned schema definitions for data validation and evolution

#### `processes` & `process_instances` - Workflow Management
```sql
CREATE TABLE processes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    process_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE process_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_id UUID NOT NULL REFERENCES processes(id),
    batch_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    parameters JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}'
);
```

**Purpose**: Manages workflow definitions and execution instances

## Entity-Based Data Model

### Entity Types

The system supports multiple entity types, each with specific properties:

#### `user` - User Accounts
```json
{
  "email": "user@example.com",
  "hashed_password": "$2b$12$...",
  "is_superuser": false,
  "user_type": "standard",
  "role": "admin",
  "department": "Development"
}
```

#### `organization` - Organizations
```json
{
  "contact_email": "info@org.com",
  "contact_phone": "+1-555-1234",
  "website": "https://org.com",
  "address": "123 Main St",
  "city": "City",
  "state": "State",
  "country": "Country",
  "timezone": "UTC",
  "member_count": 25
}
```

#### `device.esp32` - IoT Devices
```json
{
  "name": "ESP32 Device",
  "location": "Lab A",
  "status": "online",
  "firmware": {
    "version": "1.0.0",
    "lastUpdate": "2024-03-20T10:00:00Z"
  },
  "hardware": {
    "model": "ESP32-WROOM-32",
    "macAddress": "24:6F:28:XX:XX:XX",
    "sensors": [
      {
        "type": "temperature",
        "unit": "celsius",
        "range": {"min": -40, "max": 125}
      }
    ]
  },
  "config": {
    "readingInterval": 300,
    "alertThresholds": {
      "temperature": {"min": 15, "max": 30}
    }
  }
}
```

#### `project` - Research Projects
```json
{
  "start_date": "2024-01-15",
  "end_date": "2024-06-15",
  "budget": "$50,000",
  "progress_percentage": 25,
  "priority": "high",
  "tags": ["optimization", "bioreactor"],
  "settings": {
    "data_retention_days": 365,
    "alert_thresholds": {
      "temperature": {"min": 20, "max": 30}
    }
  }
}
```

### Entity Relationships

Common relationship types:

- **`monitors`**: Device → Equipment (ESP32 monitors oven)
- **`belongs_to`**: User → Organization
- **`owns`**: Organization → Device
- **`manages`**: User → Project
- **`participates_in`**: User → Project

## Event-Driven Data Flow

### Event Types

#### System Events
- `user.created`, `user.updated`, `user.deleted`
- `device.created`, `device.updated`, `device.status_changed`
- `organization.created`, `organization.updated`

#### Data Events
- `sensor.reading`: Device sensor data
- `alert.triggered`: System alerts
- `command.sent`: Device commands
- `process.started`, `process.completed`

#### User Events
- `user.login`, `user.logout`
- `data.exported`, `data.imported`
- `settings.changed`

### Event Structure

```json
{
  "timestamp": "2024-03-20T10:00:00Z",
  "event_type": "sensor.reading",
  "entity_id": "uuid-of-device",
  "entity_type": "device.esp32",
  "data": {
    "sensorType": "temperature",
    "value": 25.5,
    "unit": "celsius",
    "quality": "good",
    "batteryLevel": 85
  },
  "event_metadata": {
    "source": "esp32-device-001",
    "sequence": 12345
  }
}
```

## Domain-Specific Models

### Backend Models

The system uses SQLAlchemy models that map to the entity structure:

#### `Entity` - Base Entity Model
- Maps to `entities` table
- Provides JSONB property access methods
- Supports polymorphic entity types

#### `User` - User Management
- Inherits from `Entity`
- Maps to `entities` table with `entity_type = 'user'`
- Stores authentication data in `properties` JSONB

#### `Device` - IoT Device Management
- Inherits from `Entity`
- Maps to `entities` table with `entity_type = 'device.esp32'`
- Provides device-specific property accessors

#### `Reading` - Sensor Data
- Inherits from `Event`
- Maps to `events` table with `event_type = 'sensor.reading'`
- Stores sensor readings with metadata

### Schema Validation

Pydantic schemas provide API-level validation:

#### Base Schemas
- `BaseResponse`: Standard API response format
- `PaginationParams`: Pagination controls
- `TimeRangeParams`: Time-based filtering
- `FilterParams`: Generic filtering

#### Domain Schemas
- `UserCreate`, `UserUpdate`, `UserResponse`
- `DeviceCreate`, `DeviceUpdate`, `DeviceResponse`
- `ReadingCreate`, `ReadingResponse`

## Data Validation Layer

### Schema Evolution

The system supports schema evolution through versioned schemas:

```sql
-- Example: ESP32 Device Schema v1
INSERT INTO schemas VALUES (
    'device.esp32.v1',
    1,
    'device.esp32',
    '{
        "name": {"type": "string", "required": true},
        "status": {
            "type": "string",
            "enum": ["online", "offline", "maintenance", "error"],
            "default": "offline"
        },
        "hardware": {
            "model": {"type": "string", "required": true},
            "sensors": {"type": "array", "items": {"type": "object"}}
        }
    }',
    'ESP32 device schema v1',
    NOW(),
    NULL,
    'system'
);
```

### Validation Features

- **Type Safety**: JSON schema validation
- **Required Fields**: Mandatory property enforcement
- **Enum Values**: Constrained value sets
- **Default Values**: Automatic property defaults
- **Version Compatibility**: Backward-compatible schema evolution

## Migration Strategy

### Database Migrations

The system uses sequential SQL migrations:

1. **`000_extensions.sql`**: PostgreSQL extensions (uuid-ossp, timescaledb)
2. **`001_initial_schema.sql`**: Core tables (entities, events, relationships)
3. **`002_indexes.sql`**: Performance optimization indexes
4. **`003_esp32_device_schema.sql`**: Device-specific schemas
5. **`004_initial_data.sql`**: Sample data and schemas
6. **`005_schema_validation.sql`**: Data integrity constraints
7. **`006_add_users_table.sql`**: User authentication support

### Migration Features

- **Idempotent**: Safe to run multiple times
- **Rollback Support**: Reverse migrations available
- **Data Preservation**: Soft deletes and audit trails
- **Schema Evolution**: Versioned schema definitions

### Sample Data

The system includes comprehensive sample data:

- **Organizations**: Acme Research Labs, BioTech Innovations
- **Projects**: Bioreactor Optimization, Fermentation Development
- **Devices**: ESP32 sensor nodes, Production equipment
- **Users**: Test user with authentication credentials
- **Processes**: Baking recipes and workflow definitions

## Performance Considerations

### Indexing Strategy

- **Primary Keys**: UUID-based with time-series optimization
- **Entity Queries**: Composite indexes on (entity_type, organization_id)
- **Time Queries**: TimescaleDB hypertable partitioning
- **JSONB Queries**: GIN indexes for property searches
- **Relationship Queries**: Indexes on (from_entity, to_entity)

### Query Optimization

- **Time-Series**: Efficient time-range queries via TimescaleDB
- **JSONB**: Indexed property access for complex queries
- **Graph Traversals**: Optimized relationship queries
- **Pagination**: Cursor-based pagination for large datasets

## Security Considerations

### Data Protection

- **Password Hashing**: bcrypt with configurable rounds
- **API Keys**: Secure device authentication
- **Soft Deletes**: Data retention and recovery
- **Audit Trails**: Complete change history

### Access Control

- **Organization Isolation**: Multi-tenant data separation
- **User Permissions**: Role-based access control
- **Device Authentication**: API key-based device access
- **Event Attribution**: User tracking for all changes

## Future Considerations

### Scalability

- **Horizontal Scaling**: Multi-node event sourcing
- **Data Partitioning**: Time-based and organization-based partitioning
- **Caching Strategy**: Redis-based caching layer
- **CDN Integration**: Static asset delivery

### Extensibility

- **Plugin Architecture**: Modular entity types
- **API Versioning**: Backward-compatible API evolution
- **Schema Migration**: Automated schema updates
- **Custom Workflows**: User-defined process templates

This data model provides a solid foundation for the VerdoyLab system, supporting current requirements while enabling future growth and evolution. 