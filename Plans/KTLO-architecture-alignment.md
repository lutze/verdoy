# VerdoyLab KTLO Analysis: Architecture Alignment & Data Model Consistency

## Context

VerdoyLab is a pre-alpha Laboratory Information Management System built on a FastAPI + PostgreSQL + TimescaleDB stack. The founding architecture documents (`.cursorrules`, `docs/ARCHITECTURE.md`, `docs/datamodel/README.md`) establish five core design principles:

1. **Entity-First Design** — all system objects stored in a single `entities` table (Single Table Inheritance)
2. **Event Sourcing** — all changes tracked as immutable events in the `events` table
3. **JSONB Flexibility** — type-specific data stored in `properties` JSONB column
4. **Graph Relationships** — entity connections managed through the `relationships` table
5. **Layered Architecture** — Routers → Services → Models → DB, with no layer bypassing another

The analysis below identifies where the current implementation diverges from these principles, creating technical debt and inconsistency that will compound as the codebase grows. Items are grouped by theme and ordered within each group by impact.

---

## KTLO Improvement List

### GROUP 1 — Data Access Layer: Three Competing Query Patterns

**Problem**: The codebase has three separate, overlapping patterns for querying data. All three coexist without a clear rule for when to use each.

| Pattern | Example Location | Description |
|---|---|---|
| Active Record on models | `User.get_by_email(db, email)` | Class methods on model classes directly query DB |
| Generic BaseService | `BaseService.get_by_id(id)` | Abstract service provides generic CRUD |
| Custom service methods | `DeviceService.register_device(...)` | Domain services with their own queries |

**Impact**: Routers are calling model classmethods directly in some places and service methods in others, making behavior unpredictable and testing harder.

**Recommendation**: Establish a single rule — all DB queries must go through the service layer. Remove query classmethods from model classes (keep only property accessors and business logic methods). The `BaseService` CRUD methods should be the canonical pattern.

**Files to modify**:
- `backend/app/models/user.py` — remove `get_by_email`, `get_active_users`, `get_by_entity_id`
- `backend/app/models/device.py` — remove `get_by_device_id`, `get_by_api_key`, `get_online_devices`, `get_user_devices`, `get_by_device_name`
- `backend/app/models/reading.py` — remove `get_device_readings`, `get_latest_readings`, `get_readings_statistics`, `create_batch_readings`
- `backend/app/models/base.py` — remove `get_by_id`, `get_all` classmethods (or keep as private/internal helpers only)
- Move all query logic into the corresponding service classes

---

### GROUP 2 — Python-Side Filtering of JSONB Fields (Critical Performance Bug)

**Problem**: Multiple model query methods load entire tables into Python and filter in memory to "avoid JSONB operator issues." This is a serious performance anti-pattern that will cause outages at scale.

```python
# In device.py — loads ALL devices to find one by API key
devices = db.query(cls).filter(cls.entity_type == "device.esp32").all()
for device in devices:
    if device.get_property('apiKey') == api_key:
        return device

# In user.py — loads ALL users to find one by email
users = db.query(cls).filter(cls.entity_type == "user").all()
for user in users:
    if user.email == email:
        return user
```

Meanwhile, the `Reading` model correctly uses JSONB SQL operators:
```python
query = query.filter(cls.data['sensorType'].astext == sensor_type)
```

**Root cause**: The comment says "avoid JSONB operator issues" — suggesting these were workarounds for early bugs rather than intentional design.

**Recommendation**: Fix each Python-filter query to use proper PostgreSQL JSONB operators. Use GIN indexes (already defined in `database/migrations/002_indexes.sql`) to make these fast. The JSONB operator pattern in `reading.py` is the correct model to follow.

**Files to modify**:
- `backend/app/models/device.py` — `get_by_device_id`, `get_by_api_key`, `get_online_devices`
- `backend/app/models/user.py` — `get_by_email`
- Verify GIN indexes exist on `entities.properties` for the key fields used in these queries

---

### GROUP 3 — Dead Service Files From Abandoned Migration

**Problem**: Three domains have both a legacy service file and a `_entity` variant. Inspection of the routers confirms the split is **not** an ambiguous choice — the `_entity` variants are the sole live implementations, and the originals are entirely dead code:

| Domain | Active (called by routers) | Dead (never imported) |
|---|---|---|
| Experiments | `experiment_service_entity.py` | `experiment_service.py` |
| Processes | `process_service_entity.py` | `process_service.py` |
| Organizations | `organization_service_entity.py` | `organization_service.py` |

The `_entity` variants are architecturally superior and consistent with the founding principles:
- Use the `Entity` model directly (entity-first principle)
- Emit events via `_log_event()` (event sourcing principle)
- Create `Relationship` records for entity linkage (graph relationships principle)
- Use domain-specific exception types instead of leaking `HTTPException` into the service layer
- Use SQL-side JSONB operators for filtering (no Python-side table scans)

The legacy originals do the opposite: they use dedicated model classes with their own tables, skip event emission, and throw `HTTPException` directly from service methods.

**Recommendation**: Delete the three dead service files. They are not called by anything and represent an earlier approach that was intentionally superseded.

Additionally, rename the `_entity` variants to drop the `_entity` suffix — `ExperimentServiceEntity` should become `ExperimentService`, etc. The suffix was a transitional name that no longer carries meaning now that the migration is effectively complete. Update all router imports after the rename.

**Files to delete**:
- `backend/app/services/experiment_service.py`
- `backend/app/services/process_service.py`
- `backend/app/services/organization_service.py`

**Files to rename**:
- `experiment_service_entity.py` → `experiment_service.py` (class: `ExperimentServiceEntity` → `ExperimentService`)
- `process_service_entity.py` → `process_service.py` (class: `ProcessServiceEntity` → `ProcessService`)
- `organization_service_entity.py` → `organization_service.py` (class: `OrganizationServiceEntity` → `OrganizationService`)

---

### GROUP 4 — OrganizationMember Table Violates Graph Relationships Principle

**Problem**: The founding architecture defines the `relationships` table as the canonical store for all entity connections ("device monitors equipment, user belongs to organization"). However, `OrganizationMember` uses a dedicated `organization_members` table — bypassing the graph entirely.

The Organization model's own comment acknowledges the conflict:
> "In pure entity approach, relationships are handled through properties JSONB. No direct relationships needed..."

Yet a separate `OrganizationMember` model with its own table exists.

**Recommendation**: Migrate `OrganizationMember` membership records to the `relationships` table, using `relationship_type = 'member_of'`. Store role, joined_at, and invited_by in the `properties` JSONB column of the relationship record. This aligns with the documented graph principle and reduces table sprawl.

**Files affected**:
- `backend/app/models/organization_member.py`
- `backend/app/models/organization_invitation.py`
- `backend/app/models/membership_removal_request.py`
- `backend/app/services/organization_service_entity.py`
- `database/migrations/` — new migration needed

---

### GROUP 5 — Timestamp Field Naming Conflict

**Problem**: `BaseModel` defines `updated_at`, but `Entity.set_property()` updates `self.last_updated`. Meanwhile `Entity.update_properties()` updates `self.updated_at`. The two field names coexist and update inconsistently.

```python
# In entity.py set_property():
self.last_updated = datetime.utcnow()   # <-- last_updated

# In entity.py update_properties():
self.updated_at = datetime.utcnow()     # <-- updated_at

# In base.py:
updated_at = Column(DateTime, ...)      # <-- only updated_at is a real column
```

`last_updated` is used in the SQL schema (`last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()`) but `updated_at` is used in `BaseModel`. The ORM and the DB schema are out of sync.

**Recommendation**: Audit the actual database column name. Standardize the Python attribute to match the DB column. Remove all references to the non-canonical name. Use only `updated_at` throughout (matching `BaseModel`).

**Files to modify**:
- `backend/app/models/entity.py`
- `backend/app/models/base.py`
- `database/migrations/001_initial_schema.sql` — verify column name

---

### GROUP 6 — Mixed UUID Type Usage Across Models

**Problem**: The codebase defines a `UUIDType` custom TypeDecorator (in `database.py`) to abstract UUID handling across PostgreSQL and SQLite. However, several models import and use `PostgresUUID` directly, bypassing the abstraction:

```python
# Correct — uses the abstraction
from ..database import UUIDType
id = Column(UUIDType, primary_key=True)

# Inconsistent — imports dialect-specific type directly
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
```

Seen in: `process.py`, `relationship.py`, `organization_member.py`, `organization_invitation.py`.

**Recommendation**: Standardize all models to use `UUIDType` from `database.py`. Remove direct `PostgresUUID` imports from model files.

**Files to modify**:
- `backend/app/models/process.py`
- `backend/app/models/relationship.py`
- `backend/app/models/organization_member.py`
- `backend/app/models/organization_invitation.py`
- Any other model files importing `PostgresUUID` directly

---

### GROUP 7 — Inconsistent Primary Key Types in Event Model

**Problem**: The founding architecture states all entities use UUID primary keys. The `events` table in the datamodel README defines its PK as `BIGINT GENERATED ALWAYS AS IDENTITY`, but the ARCHITECTURE.md shows `UUID PRIMARY KEY`. The `Event` ORM model uses `Integer` with autoincrement. This inconsistency creates confusion and breaks uniformity.

Additionally, `Reading` inherits from `Event` rather than having its own table definition, but doesn't declare `__mapper_args__` polymorphic_identity, which can cause SQLAlchemy inheritance issues.

**Recommendation**: Clarify and standardize the `events` table primary key. The datamodel README approach (BIGINT identity + composite PK with timestamp) is actually correct for TimescaleDB time-series hypertables — document this exception explicitly so it doesn't look like an error. Ensure `Reading` model properly declares its polymorphic identity or remove the inheritance if it's not needed.

**Files to review**:
- `backend/app/models/event.py`
- `backend/app/models/reading.py`
- `docs/ARCHITECTURE.md` — update the events table definition to match reality
- `docs/datamodel/README.md`

---

### GROUP 8 — JSONB Property Key Naming: camelCase vs snake_case

**Problem**: The `properties` JSONB column stores data with inconsistent key naming conventions. Device properties use camelCase (`apiKey`, `lastSeen`, `batteryLevel`, `macAddress`, `readingInterval`), while Python models use snake_case accessors and Pydantic schemas use snake_case field names.

```python
# Model stores camelCase in JSON
self.set_property('lastSeen', datetime.utcnow().isoformat())
self.get_property('apiKey')
self.get_property('batteryLevel')

# But Python/API schema uses snake_case
battery_level: Optional[float]
last_seen: Optional[str]
```

This means queries filtering on JSONB keys must use camelCase strings, but developers will naturally type snake_case and get silent misses.

**Recommendation**: Standardize all JSONB property keys to snake_case to match Python and Pydantic conventions. Write a data migration to rename existing keys. Update all `get_property` / `set_property` calls.

**Files to modify**:
- `backend/app/models/device.py` — all property accessors
- `backend/app/models/reading.py`
- `backend/app/models/bioreactor.py`
- `database/migrations/` — data migration for existing records

---

### GROUP 9 — Duplicate `users` Table Contradicts Entity-First Principle

**Problem**: Migration `006_add_users_table.sql` creates a separate `users` table with its own `id`, `entity_id` FK, `email`, `hashed_password`, `is_active`, and `created_at` columns — alongside the entity-based `User` model that stores user data in `entities.properties`. This creates two competing storage locations for user data.

The ARCHITECTURE.md diagrams show `users` as a linked table with an `entity_id` FK, but the `User` ORM model stores everything in `entities`. The SQL migration and the ORM model contradict each other.

**Recommendation**: Determine the authoritative storage location (the pure entity approach is the stated architectural intent) and remove the redundant table or migration. If the separate `users` table is kept for performance/indexing (e.g., unique constraint on email), document this explicitly as a deliberate exception to the entity-first principle.

**Files to review**:
- `database/migrations/006_add_users_table.sql`
- `backend/app/models/user.py`
- `docs/ARCHITECTURE.md`

---

### GROUP 10 — Soft Delete vs Status Field: Dual State Concept

**Problem**: The system has two overlapping ways to represent entity lifecycle:
- `is_active` (Boolean) — from `BaseModel`, used for soft deletes
- `status` (String) — from `Entity`, with values like `"active"`, `"offline"`, `"maintenance"`, `"error"`

Some code checks `is_active`, other code checks `status == "active"`. For devices specifically, `status` represents connectivity (`"online"`, `"offline"`), not the soft-delete state, but the same column name is used.

**Recommendation**: Separate concerns clearly. Use `is_active` exclusively for soft delete (record exists but is logically deleted). Use `status` exclusively for domain-specific operational state (e.g., device connectivity). Document what values are valid for `status` per entity type. Audit all queries to ensure they filter on the correct field.

**Files to review**:
- `backend/app/models/base.py`
- `backend/app/models/entity.py`
- `backend/app/models/device.py`
- `backend/app/routers/` — all query filters

---

### GROUP 11 — `schemas` Table Is Defined But Never Used

**Problem**: The founding architecture defines a `schemas` table for versioned schema validation and evolution. Migration `004_initial_data.sql` populates it with ESP32 device schemas. However, the application code does not appear to query or enforce these schemas at runtime — all validation is done via Pydantic schemas at the API layer only.

The `schemas` table is defined as a core part of the architecture (supporting "Schema Evolution" and "Type Safety" principles) but is effectively dead code.

**Recommendation**: Either (a) implement runtime property validation using the `schemas` table for entity creation/updates, or (b) explicitly decide to deprecate it in favor of Pydantic-only validation and document that decision. The current state (defined but unused) creates confusion about what validation is actually happening.

**Files to review**:
- `database/migrations/003_esp32_device_schema.sql`
- `database/migrations/004_initial_data.sql`
- `backend/app/services/` — add schema validation hook
- `docs/datamodel/README.md` — update "Validation Features" section

---

### GROUP 12 — Event Sourcing Not Applied to Entity Mutations

**Problem**: The founding architecture states "all changes tracked as immutable events" and defines event types like `user.created`, `user.updated`, `device.status_changed`, etc. However, the service layer does not systematically emit events when entities are mutated. Only sensor readings (`sensor.reading`) consistently go into the events table.

**Recommendation**: Add event emission to `BaseService.create()`, `BaseService.update()`, and `BaseService.delete()` to emit the corresponding `<entity_type>.created`, `.updated`, `.deleted` events. This is the minimum to fulfill the event sourcing audit trail principle.

**Files to modify**:
- `backend/app/services/base.py` — add `_emit_event()` helper called from create/update/delete
- `backend/app/models/event.py` — ensure event creation is efficient (bulk-friendly)

---

### GROUP 13 — Architecture Documentation Inconsistency: Next.js vs Jinja2

**Problem**: The ARCHITECTURE.md and `.cursorrules` both mention "Next.js dashboard" in the high-level architecture diagram, but the actual implementation uses Jinja2 server-rendered templates (no Next.js anywhere in the codebase). This creates confusion for new contributors.

**Recommendation**: Update `docs/ARCHITECTURE.md` and `.cursorrules` to accurately reflect the Jinja2/HTML-first frontend. Update all architecture diagrams.

**Files to modify**:
- `docs/ARCHITECTURE.md`
- `.cursorrules`

---

### GROUP 14 — Stub Endpoints Shipped in Production Routes

**Problem**: Multiple registered API endpoints return hardcoded stub responses:

```python
# analytics.py
return {"summary": "Not implemented"}

# alerts.py
return {"rules": "Not implemented"}

# websocket endpoints
return "Live data WebSocket not implemented."
```

WebSocket, Analytics, Alerts, Billing, System, and Admin endpoints are all partially or fully stubbed. These endpoints exist in the router and are discoverable via the OpenAPI docs, misleading API consumers.

**Recommendation**: Either implement the stubs or mark them with HTTP `501 Not Implemented` status codes and remove them from the public OpenAPI documentation until ready. Do not ship routes that return misleading 200 OK responses with stub data.

**Files to modify**:
- `backend/app/routers/analytics.py`
- `backend/app/routers/alerts.py`
- `backend/app/routers/websocket/live_data.py`
- `backend/app/routers/websocket/device_status.py`
- `backend/app/routers/websocket/alerts.py`
- `backend/app/routers/billing.py`
- `backend/app/routers/system.py`
- `backend/app/routers/admin.py`

---

### GROUP 15 — Inconsistent API Response Format

**Problem**: Some routers return `BaseResponse(data=...)` (the intended standard format), while others return raw dictionaries or inconsistently structured payloads.

```python
# Correct — standardized pattern
return BaseResponse(success=True, data={"projects": projects})

# Inconsistent — raw dict
return {"data": ..., "count": len(items)}

# Inconsistent — raw value
return device.to_dict()
```

**Recommendation**: Audit all router return values. Enforce `BaseResponse` as the single response envelope for all JSON API endpoints. Add a linting rule or test that verifies endpoint response schemas match declared `response_model`.

**Files to audit**: All files in `backend/app/routers/api/` and `backend/app/routers/`

---

### GROUP 16 — CacheService Uses In-Memory Dict Instead of Redis

**Problem**: `CacheService` stores data in `self._cache: Dict[str, Dict[str, Any]] = {}` — a plain Python dictionary. Configuration and infrastructure for Redis exists in `config.py`, but is never connected to the service.

This means:
- Cache is process-local and lost on restart
- Cache does not scale horizontally (multiple API workers don't share state)
- No TTL enforcement, no eviction policy

**Recommendation**: Implement `CacheService` to use Redis (already configured). If Redis is unavailable in development, fall back to the in-memory dict with a warning.

**Files to modify**:
- `backend/app/services/cache_service.py`
- `backend/app/config.py` — verify Redis config fields
- `docker-compose.yml` — ensure Redis service is included

---

## Goal 2: Unified Access Layer

### Analysis: What Is Actually Duplicated

The codebase currently has **two parallel request-handling trees** for the same resources:

| Resource | Web Route (HTML, `/app/`) | API Route (JSON, `/api/v1/`) | Service Called |
|---|---|---|---|
| Authentication | `POST /app/login` | `POST /api/v1/auth/login` | `AuthService` |
| Dashboard | `GET /app/dashboard` | `GET /api/v1/dashboard` | `OrganizationServiceEntity` |
| Organizations | `GET/POST /app/admin/organization/` | `GET/POST /api/v1/organizations` | `OrganizationServiceEntity` |
| Projects | `GET /app/admin/project/` | `GET /api/v1/projects` | `ProjectService` |
| Org Members | `GET/POST /app/admin/organization-members/` | `POST /api/organizations/{id}/invite` | `OrganizationMemberService` |
| Processes | `GET/POST /app/admin/process/` | `GET /api/v1/processes` | `ProcessServiceEntity` |
| Experiments | `GET/POST /app/admin/experiment/` | _(no API equivalent yet)_ | `ExperimentServiceEntity` |

**The service layer is already unified.** `web_organizations.py` and `api_organizations.py` both call `OrganizationServiceEntity.get_all_organizations()`. The split is entirely in the HTTP layer:

| Dimension | Web routes (`/app/`) | API routes (`/api/v1/`) | IoT/AI clients |
|---|---|---|---|
| Auth method | Session cookie via `get_web_user` | Bearer token via `get_api_user` | Bearer token |
| Response format | Jinja2 HTML | JSON (`BaseResponse`) | JSON |
| Token format | JWT (identical payload) | JWT (identical payload) | API key or JWT |

There is also a **third `get_current_user` dependency** that already accepts both Bearer tokens AND session cookies, used by the shared IoT routes (`/api/v1/devices`, `/api/v1/readings`, etc.).

The split is artificial. The JWT token format is identical between web and API paths. The service layer is shared. The only real distinction is presentation (HTML vs JSON) — but that does not require separate URL trees, separate auth dependencies, or separate router files.

---

### GROUP 17 — Three Auth Dependencies for One Identity System

**Problem**: Three competing auth dependencies exist for what is a single identity concept:

```python
# get_api_user — Bearer token only, rejects session cookies
# Used by: api/api_auth.py, api/api_dashboard.py, api/api_organizations.py, api/api_projects.py

# get_web_user — Session cookie only, rejects Bearer tokens
# Used by: web/web_auth.py, web/web_dashboard.py, all web/*.py routes

# get_current_user — Accepts BOTH (tries Bearer first, falls back to cookie)
# Used by: devices.py, readings.py, commands.py (shared IoT routes)
```

`get_web_user` actively rejects Bearer tokens; `get_api_user` actively rejects session cookies. This means an MCP-based AI client with a valid Bearer token cannot call `/app/admin/organization/` even though the data operation is identical to `/api/v1/organizations`. Which URL you can reach depends on how you authenticate — the opposite of good API design.

**Root cause**: These were written as separate concerns (web UI security vs API security) but the underlying JWT format and user identity are identical.

**Recommendation**: Delete `get_api_user` and `get_web_user`. Use `get_current_user` everywhere. It already implements the correct logic: try Bearer token first, fall back to session cookie. This single change unifies authentication across all three client types (browser, IoT device, AI agent) without breaking any existing client.

**Files to modify**:
- `backend/app/dependencies.py` — delete `get_api_user` and `get_web_user`
- `backend/app/routers/api/api_auth.py` — replace `get_api_user` with `get_current_user`
- `backend/app/routers/api/api_dashboard.py` — replace `get_api_user` with `get_current_user`
- `backend/app/routers/api/api_organizations.py` — replace `get_api_user` with `get_current_user`
- `backend/app/routers/api/api_projects.py` — replace `get_api_user` with `get_current_user`
- `backend/app/routers/web/web_auth.py` — replace `get_web_user` with `get_current_user`
- `backend/app/routers/web/web_dashboard.py` — replace `get_web_user` with `get_current_user`
- All other `web/*.py` router files — same replacement

---

### GROUP 18 — Duplicate Route Trees for the Same Resources

**Problem**: After unifying auth (Group 17), the parallel `/app/` and `/api/v1/` route trees for the same resources remain. Both trees call identical service methods and return the same data — just formatted differently. Every future field addition requires updating two files.

**Recommendation**: Collapse to a two-layer model:

**Layer 1 — Data API** (`/api/v1/*`): Pure JSON endpoints. Canonical data access for all clients: browsers (HTMX/fetch), IoT devices, AI agents, external integrations. Response format: `BaseResponse` JSON. Auth: `get_current_user`. These already exist.

**Layer 2 — View Layer** (`/app/*`): HTML pages that serve as thin shells. Jinja2 templates with HTMX directives pointing at the Layer 1 API. No service layer calls — all data fetched from `/api/v1/*`. Only handles initial page load.

Result:
- `POST /app/login` → sets cookie, redirects (keeps browser form UX)
- `GET /app/dashboard` → renders HTML shell with HTMX directives
- HTMX `hx-get="/api/v1/dashboard"` → fetches data from unified JSON API
- `POST /api/v1/organizations` → used by browser, IoT device, and AI agent identically

**Migration path** (incremental, resource by resource):
1. Verify each web route's service calls are fully covered by the equivalent API route
2. Rewrite the web route to render an HTML shell template with HTMX pointing at the API
3. Delete the duplicate service calls from the web route
4. Repeat per resource

**Files to modify** (iteratively):
- `backend/app/routers/web/web_dashboard.py` → thin shell
- `backend/app/routers/web/web_organizations.py` → thin shell
- `backend/app/routers/web/web_projects.py` → thin shell
- `backend/app/routers/web/web_processes.py` → thin shell
- `backend/app/routers/web/web_experiments.py` → thin shell
- `backend/app/routers/web/web_organization_members.py` → thin shell

Also add the missing API route that currently has a web-only equivalent:
- `GET/POST /api/v1/experiments` — currently only accessible via web routes

---

### GROUP 19 — Login Produces Two Different Token Delivery Formats

**Problem**: The two login endpoints produce tokens in different ways:

```python
# /app/login — sets an HTTP-only session cookie only
response.set_cookie(key="session_token", value=access_token, httponly=True)

# /api/v1/auth/login — returns token in JSON body only
return BaseResponse(data={"access_token": access_token, "token_type": "bearer"})
```

Both use identical `create_access_token()` with the same JWT payload. A browser session cookie cannot reach API routes; a Bearer token cannot reach web routes. Client type determines which URL tree is accessible.

**Recommendation**: After implementing Groups 17 and 18, make both login endpoints deliver the token via both mechanisms:
- `POST /app/login` → set HTTP-only cookie AND return token in JSON body
- `POST /api/v1/auth/login` → set HTTP-only cookie AND return token in JSON body

Any client then uses whichever transmission method suits it (Authorization header or cookie). The auth dependency (`get_current_user`) already handles both.

**Files to modify**:
- `backend/app/routers/web/web_auth.py` — also return token in response body
- `backend/app/routers/api/api_auth.py` — also set session cookie in response

---

## Priority Table

| # | Item | Theme | Priority | Effort |
|---|------|--------|----------|--------|
| 2 | Python-side JSONB filtering | Performance / Correctness | **P0** | Medium |
| 5 | Timestamp naming conflict (`updated_at` vs `last_updated`) | Data Integrity | **P0** | Small |
| 17 | Three auth dependencies for one identity | Access Layer Unification | **P1** | Small |
| 1 | Three competing query patterns | Architecture Alignment | **P1** | Large |
| 3 | Dead non-entity service files + `_entity` rename | Code Hygiene | **P1** | Small |
| 8 | JSONB key naming (camelCase vs snake_case) | Data Consistency | **P1** | Medium |
| 6 | Mixed UUID type usage | Architecture Alignment | **P1** | Small |
| 18 | Duplicate route trees (web + API for same resources) | Access Layer Unification | **P2** | Large |
| 4 | OrganizationMember violates graph principle | Architecture Alignment | **P2** | Large |
| 9 | Duplicate `users` table | Architecture Alignment | **P2** | Medium |
| 10 | Soft delete vs status dual-concept | Data Consistency | **P2** | Medium |
| 7 | Event model PK type inconsistency | Data Integrity | **P2** | Small |
| 12 | Event sourcing not applied to mutations | Architecture Alignment | **P2** | Large |
| 19 | Login produces two token delivery formats | Access Layer Unification | **P2** | Small |
| 11 | `schemas` table unused | Architecture Alignment | **P3** | Medium |
| 14 | Stub endpoints return 200 OK | API Hygiene | **P3** | Small |
| 15 | Inconsistent API response format | API Hygiene | **P3** | Small |
| 16 | CacheService uses in-memory dict, not Redis | Infrastructure | **P3** | Small |
| 13 | Docs say Next.js, code uses Jinja2 | Documentation | **P3** | Small |

---

## Verification

To confirm each fix:
- **Groups 1, 2**: Run existing backend tests in `backend/tests/`. Add targeted unit tests for each query method moved/fixed. Confirm no full-table scans with `EXPLAIN ANALYZE` on key queries.
- **Group 3**: After deleting dead files and renaming `_entity` classes, run the full test suite and verify all routers still import correctly. `grep` for `ExperimentServiceEntity`, `ProcessServiceEntity`, `OrganizationServiceEntity` should return zero results after rename.
- **Group 4**: Verify org membership queries still return correct results after migrating to `relationships` table.
- **Groups 5, 6, 7**: Run the full test suite. Verify ORM field mappings with a DB introspection check.
- **Group 8**: Write a data migration, verify with a before/after count of records with camelCase vs snake_case keys in `entities.properties`.
- **Group 9**: Confirm user authentication flow still works end-to-end after resolving the table conflict.
- **Group 10**: Audit all `filter(is_active == True)` and `filter(status == "active")` calls — confirm no confusion between the two.
- **Group 12**: Run the app and verify entity creation/update emits events.
- **Group 11**: Review `schemas` table usage — confirm it's either populated and read or empty and acknowledged as deprecated.
- **Groups 13, 14**: Manual review of updated docs and OpenAPI spec.
- **Group 17**: After replacing `get_api_user` and `get_web_user` with `get_current_user`, verify that (a) a browser session cookie can reach `/api/v1/organizations`, (b) a Bearer token can reach `/app/admin/organization/`, and (c) an invalid/missing token on any route returns 401.
- **Group 18**: For each converted web route, verify that the HTML shell loads, HTMX fires the correct API call, data appears on screen, and form submissions go to the JSON API endpoint and update the UI correctly.
- **Group 19**: Verify that `POST /api/v1/auth/login` both returns the token in the JSON body AND sets the `session_token` cookie; verify `POST /app/login` does the same.
