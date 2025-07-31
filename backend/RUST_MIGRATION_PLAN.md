# Rust Migration Plan: FastAPI + Jinja2 to Rust Ecosystem

## Executive Summary

This document outlines a comprehensive migration strategy from the current FastAPI + Jinja2 Python stack to a Rust-based ecosystem. The migration targets improved performance, memory safety, and deployment simplicity while maintaining feature parity and API compatibility.

**Current Stack Analysis:**
- **Backend**: FastAPI with SQLAlchemy, PostgreSQL/TimescaleDB
- **Templates**: Jinja2 with HTML-first approach
- **Authentication**: JWT tokens + session cookies (dual auth)
- **Real-time**: WebSocket support
- **Architecture**: Clean architecture with service layer, event sourcing, multi-tenant support

**Recommended Rust Stack:**
- **Web Framework**: Axum (FastAPI equivalent)
- **Templating**: Tera (Jinja2 equivalent)
- **Database**: SQLx (SQLAlchemy equivalent)
- **Serialization**: Serde (Pydantic equivalent)
- **Async Runtime**: Tokio

---

## 1. Current Architecture Analysis

### 1.1 Core Components

**Database Layer:**
- PostgreSQL/TimescaleDB with TimescaleDB extensions
- Single-table inheritance model (`entities` table)
- Event sourcing with `events` table
- Multi-tenant support via `organization_id`

**Authentication System:**
- Dual authentication: JWT for API clients, session cookies for web browsers
- bcrypt password hashing (12 rounds)
- Role-based access control with organization isolation

**Template System:**
- Jinja2 templates with inheritance (`base.html`)
- HTMX integration for dynamic updates
- Component-based structure (`components/`, `partials/`, `pages/`)

**API Structure:**
- RESTful API endpoints (`/api/v1/`)
- Web endpoints (`/app/`) for HTML responses
- WebSocket endpoints (`/ws/`) for real-time data
- Comprehensive CRUD operations with event tracking

### 1.2 Key Features to Migrate

1. **User & Organization Management**
   - User registration/login with dual auth
   - Organization creation and membership
   - Role-based permissions

2. **Device Management**
   - Bioreactor enrollment (4-step process)
   - Device CRUD operations
   - Real-time status monitoring

3. **Data Ingestion & Analytics**
   - Sensor data ingestion from IoT devices
   - Historical data queries
   - Analytics and reporting

4. **Real-time Features**
   - WebSocket connections for live data
   - Device status monitoring
   - Alert notifications

5. **Template System**
   - Jinja2 template inheritance
   - HTMX integration
   - Component-based UI

---

## 2. Recommended Rust Stack

### 2.1 Core Framework: Axum

**Why Axum:**
- FastAPI's closest Rust equivalent
- Async/await support with Tokio
- Middleware system
- Dependency injection
- Type-safe routing
- Excellent performance

**Key Features:**
```rust
use axum::{
    routing::{get, post},
    Router, Json, State,
    extract::{Path, Query},
    response::Html,
    http::StatusCode,
};

// Example route structure
async fn dashboard_handler(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<Html<String>, AppError> {
    // Implementation
}
```

### 2.2 Template Engine: Tera

**Why Tera:**
- Jinja2's closest Rust equivalent
- Template inheritance
- Custom filters and functions
- Security features (auto-escaping)
- Familiar syntax

**Template Structure:**
```html
<!-- base.html equivalent -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}LMS evo Platform{% endblock %}</title>
</head>
<body>
    {% include "components/navbar.html" %}
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### 2.3 Database Layer: SQLx

**Why SQLx:**
- SQLAlchemy's closest equivalent
- Async database operations
- Type-safe queries
- Migration support
- PostgreSQL support

**Example Implementation:**
```rust
use sqlx::{PgPool, FromRow};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub name: Option<String>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub organization_id: Option<Uuid>,
}

// Database operations
impl User {
    pub async fn find_by_email(pool: &PgPool, email: &str) -> Result<Option<Self>, sqlx::Error> {
        sqlx::query_as!(
            User,
            "SELECT * FROM users WHERE email = $1",
            email
        )
        .fetch_optional(pool)
        .await
    }
}
```

### 2.4 Serialization: Serde

**Why Serde:**
- Pydantic's equivalent for serialization
- Type-safe JSON handling
- Custom serialization rules
- Validation support

---

## 3. Migration Strategy

### 3.1 Phase 1: Foundation & Infrastructure (2-3 weeks)

**Goals:**
- Set up Rust project structure
- Implement configuration management
- Set up database connections and migrations
- Create base models and traits

**Tasks:**

1. **Project Setup**
   ```toml
   # Cargo.toml
   [dependencies]
   axum = "0.7"
   tokio = { version = "1.0", features = ["full"] }
   serde = { version = "1.0", features = ["derive"] }
   serde_json = "1.0"
   tera = "1.19"
   sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres", "uuid", "chrono"] }
   tower = "0.4"
   tower-http = { version = "0.5", features = ["cors", "trace"] }
   tracing = "0.1"
   uuid = { version = "1.0", features = ["v4", "serde"] }
   chrono = { version = "0.4", features = ["serde"] }
   jsonwebtoken = "9.0"
   bcrypt = "0.15"
   ```

2. **Configuration Management**
   ```rust
   use serde::Deserialize;
   use std::env;

   #[derive(Debug, Clone, Deserialize)]
   pub struct Config {
       pub database_url: String,
       pub secret_key: String,
       pub jwt_expiration: i64,
       pub cors_origins: Vec<String>,
   }

   impl Config {
       pub fn from_env() -> Result<Self, config::ConfigError> {
           config::Config::builder()
               .add_source(config::Environment::default())
               .build()?
               .try_deserialize()
       }
   }
   ```

3. **Database Models**
   ```rust
   // Base model trait (equivalent to BaseModel)
   pub trait BaseModel {
       fn id(&self) -> Uuid;
       fn created_at(&self) -> DateTime<Utc>;
       fn updated_at(&self) -> DateTime<Utc>;
       fn is_active(&self) -> bool;
   }

   // Entity model (equivalent to your Entity)
   #[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
   pub struct Entity {
       pub id: Uuid,
       pub entity_type: String,
       pub name: String,
       pub description: Option<String>,
       pub organization_id: Option<Uuid>,
       pub properties: serde_json::Value,
       pub created_at: DateTime<Utc>,
       pub updated_at: DateTime<Utc>,
       pub is_active: bool,
   }
   ```

### 3.2 Phase 2: Core Models & Services (3-4 weeks)

**Goals:**
- Migrate all database models
- Implement service layer
- Create authentication system
- Set up error handling

**Tasks:**

1. **Authentication Service**
   ```rust
   pub struct AuthService {
       db: PgPool,
       jwt_secret: String,
   }

   impl AuthService {
       pub async fn authenticate_user(
           &self,
           email: &str,
           password: &str,
       ) -> Result<User, AuthError> {
           // Implementation
       }

       pub fn create_jwt_token(&self, user: &User) -> Result<String, JwtError> {
           // Implementation
       }
   }
   ```

2. **Service Layer**
   ```rust
   pub struct OrganizationService {
       db: PgPool,
   }

   impl OrganizationService {
       pub async fn create_organization(
           &self,
           user_id: Uuid,
           org_data: CreateOrganizationRequest,
       ) -> Result<Organization, ServiceError> {
           // Implementation
       }
   }
   ```

### 3.3 Phase 3: Template System Migration (2-3 weeks)

**Goals:**
- Migrate Jinja2 templates to Tera
- Implement template inheritance
- Set up HTMX integration
- Create component system

**Tasks:**

1. **Template Structure**
   ```
   templates/
   ├── base.html
   ├── components/
   │   └── navbar.html
   ├── pages/
   │   ├── auth/
   │   ├── dashboard/
   │   └── organizations/
   └── partials/
       ├── activity_feed.html
       └── dashboard_stats.html
   ```

2. **Template Rendering**
   ```rust
   use tera::{Tera, Context};

   pub struct TemplateEngine {
       tera: Tera,
   }

   impl TemplateEngine {
       pub fn new() -> Result<Self, tera::Error> {
           let tera = Tera::new("templates/**/*")?;
           Ok(Self { tera })
       }

       pub fn render_template(
           &self,
           template_name: &str,
           context: Context,
       ) -> Result<String, tera::Error> {
           self.tera.render(template_name, &context)
       }
   }
   ```

### 3.4 Phase 4: Router Migration (2-3 weeks)

**Goals:**
- Migrate all API routes to Axum
- Implement web routes with template rendering
- Set up middleware and authentication
- Create WebSocket handlers

**Tasks:**

1. **API Routes**
   ```rust
   pub fn api_routes() -> Router {
       Router::new()
           .route("/auth/login", post(api_login))
           .route("/auth/register", post(api_register))
           .route("/organizations", get(list_organizations))
           .route("/organizations", post(create_organization))
           .nest("/api/v1", api_v1_routes())
   }
   ```

2. **Web Routes**
   ```rust
   pub fn web_routes() -> Router {
       Router::new()
           .route("/login", get(login_page))
           .route("/login", post(login_user))
           .route("/dashboard", get(dashboard_page))
           .route("/organizations", get(organizations_page))
   }
   ```

3. **WebSocket Routes**
   ```rust
   pub fn websocket_routes() -> Router {
       Router::new()
           .route("/ws/live-data", get(live_data_handler))
           .route("/ws/device-status", get(device_status_handler))
           .route("/ws/alerts", get(alerts_handler))
   }
   ```

### 3.5 Phase 5: API Endpoints Migration (2-3 weeks)

**Goals:**
- Migrate all REST API endpoints
- Implement data validation
- Set up error handling
- Create response models

**Tasks:**

1. **Request/Response Models**
   ```rust
   #[derive(Debug, Serialize, Deserialize)]
   pub struct LoginRequest {
       pub email: String,
       pub password: String,
       pub remember_me: Option<bool>,
   }

   #[derive(Debug, Serialize, Deserialize)]
   pub struct LoginResponse {
       pub access_token: String,
       pub token_type: String,
       pub expires_in: i64,
       pub user: UserResponse,
   }
   ```

2. **Validation**
   ```rust
   use validator::{Validate, ValidationError};

   #[derive(Debug, Serialize, Deserialize, Validate)]
   pub struct CreateOrganizationRequest {
       #[validate(length(min = 1, max = 100))]
       pub name: String,
       #[validate(length(max = 500))]
       pub description: Option<String>,
   }
   ```

### 3.6 Phase 6: WebSocket Migration (1-2 weeks)

**Goals:**
- Migrate WebSocket endpoints
- Implement real-time data streaming
- Set up connection management
- Create event broadcasting

**Tasks:**

1. **WebSocket Handlers**
   ```rust
   use axum::extract::ws::{WebSocket, WebSocketUpgrade};
   use axum::response::IntoResponse;

   async fn live_data_handler(
       ws: WebSocketUpgrade,
       State(state): State<AppState>,
   ) -> impl IntoResponse {
       ws.on_upgrade(|socket| handle_live_data_socket(socket, state))
   }

   async fn handle_live_data_socket(socket: WebSocket, state: AppState) {
       // Implementation
   }
   ```

---

## 4. Migration Challenges & Solutions

### 4.1 Key Challenges

1. **Async/Await Patterns**
   - **Challenge**: Rust's async is more explicit than Python's
   - **Solution**: Use Tokio runtime and async/await consistently

2. **Error Handling**
   - **Challenge**: Rust's `Result<T, E>` vs Python exceptions
   - **Solution**: Implement custom error types and use `?` operator

3. **Type Safety**
   - **Challenge**: More compile-time guarantees but requires more upfront work
   - **Solution**: Leverage Rust's type system for better code quality

4. **Template Syntax**
   - **Challenge**: Tera vs Jinja2 syntax differences
   - **Solution**: Create Jinja2-to-Tera converter for templates

5. **Database Migrations**
   - **Challenge**: SQLx vs Alembic approach differences
   - **Solution**: Use SQLx migrations with version control

### 4.2 Solutions

1. **Gradual Migration**
   - Start with new features in Rust
   - Migrate existing ones incrementally
   - Use feature flags to switch between implementations

2. **Shared Database**
   - Keep PostgreSQL database
   - Migrate one service at a time
   - Maintain API compatibility

3. **Template Compatibility**
   - Create Jinja2-to-Tera converter
   - Maintain same template structure
   - Test template rendering thoroughly

4. **API Compatibility**
   - Maintain same REST API contracts
   - Use same request/response formats
   - Keep authentication mechanisms compatible

---

## 5. Estimated Timeline & Effort

### 5.1 Timeline Breakdown

**Total Migration Time: 12-16 weeks**

- **Phase 1 (Foundation)**: 2-3 weeks
- **Phase 2 (Core Services)**: 3-4 weeks
- **Phase 3 (Templates)**: 2-3 weeks
- **Phase 4 (Routers)**: 2-3 weeks
- **Phase 5 (APIs)**: 2-3 weeks
- **Phase 6 (WebSockets)**: 1-2 weeks
- **Testing & Polish**: 2-3 weeks

### 5.2 Resource Requirements

**Development Team:**
- 1-2 Rust developers (primary)
- 1 Python developer (knowledge transfer)
- 1 DevOps engineer (deployment)

**Infrastructure:**
- Development environment setup
- CI/CD pipeline updates
- Database migration tools

---

## 6. Benefits of Migration

### 6.1 Performance Improvements

1. **CPU Performance**: 10-100x faster than Python for CPU-intensive tasks
2. **Memory Usage**: More efficient memory management
3. **Concurrency**: Better async performance with Tokio
4. **Startup Time**: Faster application startup

### 6.2 Safety & Reliability

1. **Memory Safety**: Zero-cost abstractions with compile-time guarantees
2. **Thread Safety**: Rust's ownership system prevents data races
3. **Error Handling**: Compile-time error checking
4. **Type Safety**: Catch errors at compile time vs runtime

### 6.3 Deployment Benefits

1. **Single Binary**: Deploy single executable vs Python dependencies
2. **Container Efficiency**: Smaller Docker images
3. **Resource Usage**: Lower memory and CPU requirements
4. **Security**: Reduced attack surface

---

## 7. Recommended Approach

### 7.1 Migration Strategy

1. **Start with a small, isolated service**
   - Health checks
   - Simple CRUD operations
   - Non-critical features

2. **Create parallel Rust implementation**
   - Build alongside existing Python code
   - Use feature flags for switching
   - Maintain API compatibility

3. **Migrate incrementally**
   - One router/service at a time
   - Thorough testing at each step
   - Rollback capability

4. **Maintain API compatibility**
   - Same REST endpoints
   - Same request/response formats
   - Same authentication mechanisms

### 7.2 Risk Mitigation

1. **Comprehensive Testing**
   - Unit tests for all components
   - Integration tests for API endpoints
   - End-to-end tests for critical flows

2. **Feature Flags**
   - Gradual rollout capability
   - Easy rollback mechanism
   - A/B testing support

3. **Monitoring & Observability**
   - Performance metrics
   - Error tracking
   - User experience monitoring

---

## 8. Implementation Checklist

### 8.1 Pre-Migration

- [ ] Set up Rust development environment
- [ ] Create project structure and Cargo workspace
- [ ] Set up CI/CD pipeline for Rust
- [ ] Create database migration strategy
- [ ] Plan template migration approach

### 8.2 Phase 1: Foundation

- [ ] Implement configuration management
- [ ] Set up database connections
- [ ] Create base models and traits
- [ ] Implement authentication middleware
- [ ] Set up logging and error handling

### 8.3 Phase 2: Core Services

- [ ] Migrate all database models
- [ ] Implement service layer
- [ ] Create authentication system
- [ ] Set up dependency injection

### 8.4 Phase 3: Templates

- [ ] Migrate Jinja2 templates to Tera
- [ ] Implement template inheritance
- [ ] Set up HTMX integration
- [ ] Create component system

### 8.5 Phase 4: Routers

- [ ] Migrate all API routes to Axum
- [ ] Implement web routes with template rendering
- [ ] Set up middleware and authentication
- [ ] Create WebSocket handlers

### 8.6 Phase 5: APIs

- [ ] Migrate all REST API endpoints
- [ ] Implement data validation
- [ ] Set up error handling
- [ ] Create response models

### 8.7 Phase 6: WebSockets

- [ ] Migrate WebSocket endpoints
- [ ] Implement real-time data streaming
- [ ] Set up connection management
- [ ] Create event broadcasting

### 8.8 Post-Migration

- [ ] Comprehensive testing
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Documentation updates
- [ ] Team training

---

## 9. Conclusion

The migration from FastAPI + Jinja2 to a Rust-based stack using Axum + Tera + SQLx offers significant benefits in terms of performance, safety, and deployment simplicity. The recommended approach of gradual migration with parallel implementations minimizes risk while maximizing the benefits of Rust's type safety and performance characteristics.

The estimated timeline of 12-16 weeks provides a realistic assessment of the effort required, with the ability to deliver value incrementally throughout the migration process. The comprehensive testing strategy and feature flag approach ensure that the migration can be executed safely with minimal disruption to existing functionality.

By following this plan, the team can successfully migrate to a modern, performant Rust-based stack while maintaining all existing functionality and improving the overall system architecture. 