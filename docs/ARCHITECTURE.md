# LMS Core Platform - Architectural Documentation

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Database Architecture](#database-architecture)
4. [IoT Communication Architecture](#iot-communication-architecture)
5. [Security Architecture](#security-architecture)
6. [Deployment Architecture](#deployment-architecture)
7. [Performance & Scalability](#performance--scalability)
8. [Monitoring & Observability](#monitoring--observability)

---

## 🏗️ System Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Devices   │    │   Web Frontend  │    │   Mobile App    │
│   (ESP32)       │    │   (Next.js)     │    │   (Future)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     LMS Core API          │
                    │    (FastAPI Backend)      │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   PostgreSQL + TimescaleDB│
                    │   (Time-series Data)      │
                    └───────────────────────────┘
```

### Key Components

- **IoT Devices**: ESP32 microcontrollers with sensors
- **Web Frontend**: Next.js dashboard for data visualization
- **API Backend**: FastAPI application with REST and WebSocket endpoints
- **Database**: PostgreSQL with TimescaleDB extension for time-series data
- **Real-time Communication**: WebSocket connections for live data streaming

---

## 🔧 Backend Architecture

### Application Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection and session management
│   ├── dependencies.py         # Dependency injection setup
│   ├── exceptions.py           # Custom exception handlers
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── base.py            # Base model classes
│   │   ├── entity.py          # Entity model (single-table inheritance)
│   │   ├── user.py            # User model
│   │   ├── device.py          # Device model
│   │   ├── reading.py         # Sensor readings model
│   │   ├── alert.py           # Alerts and rules model
│   │   ├── organization.py    # Organization model
│   │   ├── billing.py         # Billing model
│   │   └── command.py         # Device commands model
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── base.py           # Base schema classes
│   │   ├── user.py           # User schemas
│   │   ├── device.py         # Device schemas
│   │   ├── reading.py        # Reading schemas
│   │   ├── alert.py          # Alert schemas
│   │   ├── organization.py   # Organization schemas
│   │   ├── billing.py        # Billing schemas
│   │   └── command.py        # Command schemas
│   ├── services/             # Business logic layer
│   │   ├── base.py          # Base service class
│   │   ├── auth_service.py  # Authentication service
│   │   ├── device_service.py # Device management service
│   │   ├── reading_service.py # Data processing service
│   │   ├── alert_service.py # Alert management service
│   │   ├── organization_service.py # Organization service
│   │   ├── billing_service.py # Billing service
│   │   ├── command_service.py # Command service
│   │   ├── analytics_service.py # Analytics service
│   │   ├── notification_service.py # Notification service
│   │   ├── websocket_service.py # WebSocket service
│   │   ├── cache_service.py # Caching service
│   │   └── background_service.py # Background tasks
│   ├── routers/              # API endpoint definitions
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── devices.py       # Device management endpoints
│   │   ├── readings.py      # Data ingestion/retrieval endpoints
│   │   ├── commands.py      # Device control endpoints
│   │   ├── analytics.py     # Analytics endpoints
│   │   ├── alerts.py        # Alert management endpoints
│   │   ├── organizations.py # Organization management endpoints
│   │   ├── billing.py       # Billing endpoints
│   │   ├── system.py        # System health endpoints
│   │   ├── admin.py         # Admin endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── websocket/       # WebSocket endpoints
│   │       ├── live_data.py # Live sensor data
│   │       ├── device_status.py # Device status events
│   │       └── alerts.py    # Real-time alerts
│   ├── middleware/          # Request/response middleware
│   │   ├── cors.py         # CORS configuration
│   │   ├── logging.py      # Request logging
│   │   └── websocket.py    # WebSocket middleware
│   └── utils/              # Utility functions
│       ├── helpers.py      # Common helper functions
│       ├── validators.py   # Custom validators
│       ├── exporters.py    # Data export utilities
│       └── auth_utils.py   # Authentication utilities
├── tests/                  # Test suite
│   ├── conftest.py        # Test configuration and fixtures
│   ├── test_api/          # API endpoint tests
│   ├── test_core/         # Core functionality tests
│   └── test_integration/  # Integration tests
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pytest.ini           # Test configuration
├── dockerfile           # Docker container definition
└── README.md           # Backend documentation
```

### Architecture Patterns

#### 1. **Layered Architecture**
```
┌─────────────────────────────────────┐
│           API Layer                 │  ← FastAPI Routers
├─────────────────────────────────────┤
│         Service Layer               │  ← Business Logic
├─────────────────────────────────────┤
│         Data Access Layer           │  ← SQLAlchemy Models
├─────────────────────────────────────┤
│         Database Layer              │  ← PostgreSQL/TimescaleDB
└─────────────────────────────────────┘
```

#### 2. **Dependency Injection**
- FastAPI dependency injection for database sessions
- Service layer injection for business logic
- Authentication and authorization dependencies

#### 3. **Single-Table Inheritance**
- All entities (users, devices, organizations) stored in `entities` table
- Entity type discrimination via `entity_type` field
- Polymorphic relationships and queries

---

## 🗄️ Database Architecture

### Database Structure

```
database/
├── setup_db.py              # Database initialization script
├── check_migrations.py      # Migration validation script
├── README.md               # Database documentation
└── migrations/             # Database migration files
    ├── 000_extensions.sql  # PostgreSQL extensions
    ├── 000_create_migrations_table.sql # Migration tracking
    ├── 001_initial_schema.sql # Core schema
    ├── 002_indexes.sql     # Performance indexes
    ├── 003_esp32_device_schema.sql # Device-specific schema
    ├── 003_timescale_config.sql # TimescaleDB configuration
    ├── 004_initial_data.sql # Seed data
    ├── 005_schema_validation.sql # Schema constraints
    └── 006_add_users_table.sql # User management
```

### Core Tables

#### 1. **Entities Table (Single-Table Inheritance)**
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES entities(id),
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. **Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. **Events Table (Time-series Data)**
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id),
    event_type VARCHAR(100) NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. **Relationships Table (Graph Relationships)**
```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity UUID NOT NULL REFERENCES entities(id),
    to_entity UUID NOT NULL REFERENCES entities(id),
    relationship_type VARCHAR(100) NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Data Model Relationships

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Entities   │    │    Users    │    │   Events    │
│             │    │             │    │             │
│ - id        │◄───┤ - entity_id │    │ - entity_id │
│ - type      │    │ - email     │    │ - type      │
│ - org_id    │    │ - password  │    │ - data      │
│ - props     │    │ - active    │    │ - timestamp │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌─────────────┐
                    │Relationships│
                    │             │
                    │ - from_ent  │
                    │ - to_ent    │
                    │ - type      │
                    │ - props     │
                    └─────────────┘
```

### TimescaleDB Configuration

- **Hypertables**: Events table partitioned by time
- **Compression**: Automatic data compression for historical data
- **Retention Policies**: Automatic data retention and cleanup
- **Continuous Aggregates**: Pre-computed aggregations for analytics

---

## 📡 IoT Communication Architecture

### Device Communication Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ESP32     │    │   LMS API   │    │  Database   │
│  Device     │    │  Backend    │    │             │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      │ 1. Register      │                  │
      │─────────────────►│                  │
      │                  │                  │
      │ 2. Get Config    │                  │
      │◄─────────────────│                  │
      │                  │                  │
      │ 3. Send Data     │                  │
      │─────────────────►│                  │
      │                  │ 4. Store Data    │
      │                  │─────────────────►│
      │                  │                  │
      │ 5. Poll Commands │                  │
      │─────────────────►│                  │
      │                  │                  │
      │ 6. Execute Cmd   │                  │
      │◄─────────────────│                  │
```

### Real-time Data Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ESP32     │    │   API       │    │  WebSocket  │    │   Frontend  │
│  Sensors    │    │  Backend    │    │   Service   │    │  Dashboard  │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │                  │
      │ 1. Sensor Data   │                  │                  │
      │─────────────────►│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Process Data  │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │                  │ 3. Store Data    │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │                  │ 4. Broadcast     │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │                  │ 5. Real-time     │                  │
      │                  │    Update       │                  │
      │                  │─────────────────►│                  │
```

### Command & Control Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   API       │    │  Database   │    │   ESP32     │
│  Dashboard  │    │  Backend    │    │             │    │  Device     │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │                  │
      │ 1. Send Command  │                  │                  │
      │─────────────────►│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Queue Command │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │                  │                  │ 3. Poll Commands │
      │                  │                  │◄─────────────────│
      │                  │                  │                  │
      │                  │                  │ 4. Return Cmd    │
      │                  │                  │─────────────────►│
      │                  │                  │                  │
      │                  │                  │ 5. Execute &     │
      │                  │                  │    Report       │
      │                  │                  │◄─────────────────│
      │                  │                  │                  │
      │                  │ 6. Update Status │                  │
      │                  │─────────────────►│                  │
```

---

## 🔒 Security Architecture

### Dual Authentication System

The LMS Core platform implements a sophisticated dual authentication system that supports both programmatic API clients and web browsers:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Web        │    │   API       │    │  JWT        │    │  Database   │
│  Browser    │    │  Backend    │    │  Service    │    │             │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │                  │
      │ 1. Login Form    │                  │                  │
      │─────────────────►│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Validate User │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │                  │ 3. Generate JWT  │                  │
      │                  │─────────────────►│                  │
      │                  │                  │                  │
      │ 4. Set Session   │                  │                  │
      │    Cookie +      │                  │                  │
      │    Redirect      │                  │                  │
      │◄─────────────────│                  │                  │
```

### Authentication Methods

#### 1. **Session-Based Authentication (Web Browsers)**
- **HTTP-Only Cookies**: Secure session tokens stored in HTTP-only cookies
- **Security Flags**: 
  - `httponly=True` (prevents XSS attacks)
  - `secure=True` for HTTPS (auto-detected)
  - `samesite="lax"` (CSRF protection)
- **Remember Me**: 1 hour vs 30 days expiration based on user preference
- **Automatic Renewal**: Session tokens are JWT tokens with automatic validation

#### 2. **Bearer Token Authentication (API Clients)**
- **JWT Tokens**: Standard Authorization: Bearer header format
- **Device API Keys**: Specialized authentication for IoT devices
- **Programmatic Access**: For scripts, mobile apps, and integrations

### Authentication Flow Implementation

```python
# Unified authentication dependency
def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
):
    """
    Supports both Bearer token authentication (API clients) and 
    session cookie authentication (web browsers).
    """
    token = None
    
    # Try Bearer token first (for API clients)
    if credentials and credentials.credentials:
        token = credentials.credentials
    # Fall back to session cookie (for web browsers)
    elif session_token:
        token = session_token
    
    if not token:
        raise CredentialsException()
    
    # Validate JWT token and return User object
    payload = decode_access_token(token)
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    return user
```

### Multi-Tenant Data Isolation

```
┌─────────────────────────────────────────────────────────────┐
│                    Organization A                          │
├─────────────────────────────────────────────────────────────┤
│  Users: [user1, user2, user3]                              │
│  Devices: [device1, device2, device3]                      │
│  Data: [readings1, readings2, readings3]                    │
│  Alerts: [alert1, alert2]                                   │
│  Session Access: HTTP-only cookies for web users           │
│  API Access: JWT tokens for programmatic clients           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Organization B                          │
├─────────────────────────────────────────────────────────────┤
│  Users: [user4, user5]                                     │
│  Devices: [device4, device5]                               │
│  Data: [readings4, readings5]                              │
│  Alerts: [alert3]                                          │
│  Session Access: Separate secure cookies                   │
│  API Access: Organization-scoped JWT tokens                │
└─────────────────────────────────────────────────────────────┘
```

### Security Layers

1. **API Gateway Security**
   - Rate limiting
   - Request validation
   - CORS configuration
   - Input sanitization

2. **Authentication Security**
   - **Dual JWT validation**: Both Bearer tokens and session cookies use same JWT system
   - **Password hashing**: bcrypt with 12 rounds via passlib
   - **Token expiration**: Configurable expiration with refresh capability
   - **Session security**: HTTP-only, secure, SameSite cookie protection

3. **Authorization Security**
   - **Role-based access control**: User roles and permissions
   - **Organization-based isolation**: Multi-tenant data access control
   - **Resource-level permissions**: Granular access to devices and data
   - **Cross-authentication support**: Same endpoints serve both web and API clients

4. **Data Security**
   - **Database connection encryption**: Secure PostgreSQL/TimescaleDB connections
   - **Sensitive data encryption**: Secure storage of credentials and keys
   - **Audit logging**: Security event tracking
   - **Backup and recovery**: Data protection and disaster recovery

### Template System Security

The platform implements a shared Jinja2 template system with security considerations:

```python
# Centralized template configuration with security filters
def get_templates():
    templates = Jinja2Templates(directory="app/templates")
    
    # Custom filters for safe data display
    def number_format(value):
        """Format numbers with commas for better readability."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return value
    
    templates.env.filters["number_format"] = number_format
    return templates
```

### Database Compatibility Layer

Cross-database JSON handling ensures security across different environments:

```python
class JSONType(TypeDecorator):
    """Secure JSON handling for PostgreSQL and SQLite."""
    
    def process_result_value(self, value, dialect):
        # PostgreSQL/TimescaleDB automatically parses JSONB to dict/list
        # SQLite returns JSON as string that needs parsing
        if isinstance(value, (dict, list)):
            return value  # Already parsed (PostgreSQL)
        elif isinstance(value, (str, bytes)):
            return json.loads(value)  # Parse string (SQLite)
        else:
            return value  # Safe fallback
```

---

## 🚀 Deployment Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Frontend  │  │   Backend   │  │  Database   │        │
│  │  (Next.js)  │  │  (FastAPI)  │  │(PostgreSQL) │        │
│  │   Port 3000 │  │   Port 8000 │  │   Port 5432 │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                           │
│                    (Nginx/Traefik)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
│   Frontend   │ │  API 1  │ │   API 2     │
│   (Static)   │ │(FastAPI)│ │ (FastAPI)   │
└──────────────┘ └─────────┘ └─────────────┘
                          │
                  ┌───────▼──────┐
                  │  Database    │
                  │(PostgreSQL + │
                  │ TimescaleDB) │
                  └──────────────┘
```

---

## ⚡ Performance & Scalability

### Performance Optimizations

1. **Database Optimizations**
   - TimescaleDB hypertables for time-series data
   - Proper indexing on frequently queried fields
   - Connection pooling
   - Query optimization and caching

2. **API Optimizations**
   - Response caching with Redis
   - Pagination for large datasets
   - Efficient JSON serialization
   - Background task processing

3. **Real-time Optimizations**
   - WebSocket connection pooling
   - Efficient data streaming
   - Message queuing for high-volume data

### Scalability Considerations

1. **Horizontal Scaling**
   - Stateless API design
   - Database read replicas
   - Load balancing across multiple API instances
   - Microservice architecture for future growth

2. **Data Scaling**
   - TimescaleDB partitioning
   - Data retention policies
   - Archival strategies for historical data
   - CDN for static assets

---

## 📊 Monitoring & Observability

### Monitoring Stack

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   API       │    │  Prometheus │    │   Grafana   │
│  Metrics    │    │  (Metrics)  │    │ (Dashboard) │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      │ 1. Collect       │                  │
      │    Metrics       │                  │
      │─────────────────►│                  │
      │                  │                  │
      │                  │ 2. Query Metrics │
      │                  │◄─────────────────│
      │                  │                  │
      │                  │ 3. Visualize     │
      │                  │    Data          │
      │                  │─────────────────►│
```

### Key Metrics

1. **Application Metrics**
   - Request/response times
   - Error rates
   - Throughput (requests/second)
   - Active connections

2. **Database Metrics**
   - Query performance
   - Connection pool usage
   - Storage utilization
   - Index usage

3. **IoT Metrics**
   - Device connectivity
   - Data ingestion rates
   - Command execution success
   - Alert frequency

4. **Infrastructure Metrics**
   - CPU and memory usage
   - Disk I/O
   - Network traffic
   - Container health

### Logging Strategy

1. **Structured Logging**
   - JSON-formatted logs
   - Correlation IDs for request tracing
   - Log levels (DEBUG, INFO, WARN, ERROR)
   - Contextual information

2. **Log Aggregation**
   - Centralized log collection
   - Log parsing and indexing
   - Search and filtering capabilities
   - Log retention policies

---

## Routing Conventions (as of 18 July 2025)

- **Web (HTML) pages:**
  - Use "pretty" URLs with no `/api/v1` prefix.
  - Example routes:
    - `/auth/login` (login page)
    - `/auth/register` (registration page)
    - `/dashboard` (user dashboard)
    - `/dashboard/activity` (activity feed partial)
    - `/dashboard/stats` (dashboard stats partial)
  - These endpoints return HTML (Jinja2 templates) and are intended for browser users.
  - They are registered in FastAPI with prefixes like `/auth` or `/dashboard`, or no prefix at all.

- **API (JSON) endpoints:**
  - Use the `/api/v1` prefix for all programmatic (JSON) endpoints.
  - Example routes:
    - `/api/v1/devices` (device management API)
    - `/api/v1/readings` (sensor data API)
    - `/api/v1/commands` (device command API)
  - These endpoints return JSON and are intended for programmatic clients (IoT devices, scripts, etc.).
  - They are registered in FastAPI with the prefix from `settings.api_prefix` (default `/api/v1`).

- **Rationale:**
  - This separation keeps browser-facing pages clean and user-friendly, while maintaining a clear, versioned API for programmatic access.
  - Web endpoints are hidden from API docs, while API endpoints are fully documented.

---

## 📋 Next Steps

### Documentation Priorities

1. **High Priority**
   - [ ] Create system architecture diagrams
   - [ ] Document API endpoint specifications
   - [ ] Create database schema diagrams
   - [ ] Document deployment procedures

2. **Medium Priority**
   - [ ] Create sequence diagrams for key flows
   - [ ] Document security procedures
   - [ ] Create monitoring dashboards
   - [ ] Document troubleshooting guides

3. **Low Priority**
   - [ ] Create user guides
   - [ ] Document API examples
   - [ ] Create performance benchmarks
   - [ ] Document scaling procedures

### Tools & Technologies

- **Diagram Creation**: Draw.io, Lucidchart, or Mermaid
- **API Documentation**: OpenAPI/Swagger
- **Database Documentation**: Schema visualization tools
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with correlation IDs

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/) 