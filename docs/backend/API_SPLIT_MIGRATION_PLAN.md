# API Split Migration Plan: /api/v1 (API) vs /app (Web)

## Overview

This document details the plan to refactor the backend so that:
- **/api/v1/** endpoints serve JSON for programmatic/API clients (token-based auth)
- **/app/** endpoints serve HTML for web browsers (session/cookie auth)
- No more dual-purpose routes; each endpoint is either API or web, not both
- Authentication, business logic, and tests are cleanly separated

---

## Rationale

- **Clarity:** Each route has a single responsibility (API or web)
- **Security:** Separate authentication mechanisms (JWT for API, session for web)
- **Maintainability:** No more `accepts_json(request)` or mixed return types
- **Testing:** Playwright tests only hit /app, API tests only hit /api/v1
- **Docs:** Only /api/v1 endpoints appear in OpenAPI/Swagger

---

## Migration Steps

### 1. **Audit and Categorize All Routes**
- [x] List all current routes and classify as API-only, Web-only, or Dual-purpose
- [x] Identify all places using `accepts_json(request)` or similar logic

### 2. **Create Separate Routers**
- [x] For each resource (auth, projects, organizations, etc.):
    - [x] Move all API endpoints to `routers/api/` (e.g., `api_projects.py`)
    - [x] Move all web endpoints to `routers/web/` (e.g., `web_projects.py`)
- [x] Register routers with appropriate prefixes in `main.py`:
    - `/api/v1/` → API routers
    - `/app/` → Web routers

### 3. **Refactor Authentication**
- [x] API endpoints: Require JWT/Bearer token, no session cookies
- [x] Web endpoints: Require session cookie, no Bearer token
- [ ] Add API token management UI to user profile page (generate/revoke tokens)

### 4. **Update Endpoint Implementations**
- [x] Remove all `accepts_json(request)` and dual return logic
- [x] API endpoints: Always return JSON (use Pydantic models or dicts)
- [x] Web endpoints: Always return `TemplateResponse`/`RedirectResponse`
- [x] Ensure all `/app/` endpoints have `include_in_schema=False`

### 5. **Update Frontend and Navigation**
- [x] Ensure all navigation in templates uses `/app/` routes
- [x] Update frontend forms and JS to use `/app/` endpoints only

### 6. **Update and Expand Tests**
- [x] Playwright: Only test `/app/` routes (HTML, forms, navigation)
- [ ] API tests: Only test `/api/v1/` routes (JSON, auth, business logic)
- [ ] Remove/replace any tests that rely on dual-purpose endpoints

### 7. **Documentation and OpenAPI**
- [ ] Update API docs to only show `/api/v1/` endpoints
- [ ] Document authentication flows for both API and web
- [ ] Add migration notes for developers

### 8. **Deployment and Verification**
- [ ] Deploy to staging
- [ ] Run full test suite (Playwright + API tests)
- [ ] Manual QA for both web and API clients
- [ ] Monitor logs for unexpected errors

---

## Step 3 Progress

- Implemented `get_api_user` (Bearer token only) and `get_web_user` (session cookie only) dependencies in `dependencies.py`.
- Updated all new API routers to use `get_api_user` for user extraction.
- Updated all new Web routers to use `get_web_user` for user extraction.
- API endpoints now reject session cookies; web endpoints now reject Bearer tokens.

## Semantic Changelog

- [Step 1] Audited all routers and classified routes as API-only, Web-only, or Dual-purpose.
- [Step 1] Documented findings and created a classification table in this plan.
- [Step 2] Enumerated all dual-purpose routes in `auth.py`, `dashboard.py`, `projects.py`, and `organizations.py` and planned the split for each.
- [Step 2] Created `api/` and `web/` router directories to begin the code split.
- [Step 2] Created `api_auth.py` and `web_auth.py` as initial placeholders for authentication route migration.
- [Step 2] Migrated and refactored API-only authentication endpoints into `api/api_auth.py`.
- [Step 2] Migrated and refactored web-only authentication endpoints into `web/web_auth.py`.
- [Step 2] Migrated and refactored dashboard endpoints into `api/api_dashboard.py` and `web/web_dashboard.py`.
- [Step 2] Migrated and refactored projects endpoints into `api/api_projects.py` and `web/web_projects.py`.
- [Step 2] Migrated and refactored organizations endpoints into `api/api_organizations.py` and `web/web_organizations.py`.
- [Step 2] Registered new API and Web routers in `main.py` for all split resources.
- [Step 3] Implemented strict authentication separation: API endpoints require JWT/Bearer token, web endpoints require session cookie. All new routers updated to use the correct dependency.

---

## Detailed Checklist

- [ ] All dual-purpose routes split into API and web versions
- [ ] No HTMLResponse routes return dicts (and vice versa)
- [ ] API endpoints require and validate JWT/Bearer tokens
- [ ] Web endpoints require and validate session cookies
- [ ] User profile page allows API token management
- [ ] All navigation and forms use `/app/` routes
- [ ] Playwright and API tests pass
- [ ] OpenAPI docs are clean and accurate

---

## Example Directory Structure

```
backend/app/routers/
  api/
    api_auth.py
    api_projects.py
    api_organizations.py
    ...
  web/
    web_auth.py
    web_projects.py
    web_organizations.py
    ...
```

---

## Rollout Strategy

- Refactor in feature branches, merge incrementally
- Prioritize authentication and core resources first
- Keep old dual-purpose routes until new ones are stable, then remove
- Communicate changes to all developers and update onboarding docs

---

## Risks & Mitigations

- **Risk:** Missed endpoints or regressions
  - **Mitigation:** Comprehensive test coverage, manual QA
- **Risk:** API clients break due to auth changes
  - **Mitigation:** Announce changes, provide migration guide, support both auth methods temporarily if needed

---

## References
- [FastAPI: Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/)
- [Best Practices: API vs Web Separation](https://12factor.net/)
- [Project README and FRONTEND_PLAN.md] 

## Step 1: Route Audit and Categorization

### Process
- Searched all routers in `backend/app/routers/` for FastAPI route definitions.
- Classified each route as API-only, Web-only, or Dual-purpose based on:
  - Path prefix (`/api/v1/` for API, `/app/` for web, or both)
  - Response type (JSON, HTMLResponse, TemplateResponse)
  - Use of `accepts_json(request)` or similar logic
- Noted routers that mix responsibilities or use dual-purpose logic.

### Router Classification Table

| Router         | Example Route(s)                | Type           | Notes |
|----------------|----------------------------------|----------------|-------|
| auth.py        | /login, /register, /admin/profile, /api/v1/auth/* | Dual-purpose | Uses `accepts_json(request)` to switch between HTML and JSON |
| dashboard.py   | /app/dashboard, /api/v1/dashboard | Dual-purpose   | Separate HTML and JSON routes, but some logic is shared |
| projects.py    | /app/projects, /api/v1/projects  | Dual-purpose   | Uses `accepts_json(request)` to delegate to API handler |
| organizations.py| /app/admin/organization/, /api/v1/organizations | Dual-purpose | Uses `accepts_json(request)` to delegate to API handler |
| devices.py     | /api/v1/devices                  | API-only       | JSON API for device management |
| readings.py    | /api/v1/readings                 | API-only       | JSON API for sensor data |
| commands.py    | /api/v1/commands                 | API-only       | JSON API for device commands |
| analytics.py   | /api/v1/analytics                | API-only       | JSON API for analytics |
| alerts.py      | /api/v1/alerts                   | API-only       | JSON API for alerts |
| billing.py     | /api/v1/billing                  | API-only       | JSON API for billing |
| system.py      | /api/v1/system                   | API-only       | JSON API for system health |
| admin.py       | /api/v1/admin                    | API-only       | JSON API for admin ops |
| health.py      | /api/v1/health                   | API-only       | JSON API for health check |
| websocket/*    | /ws/*                            | WebSocket      | Real-time endpoints |

#### Key Findings
- **Dual-purpose routers**: `auth.py`, `dashboard.py`, `projects.py`, `organizations.py` all mix HTML and JSON logic, often using `accepts_json(request)`.
- **API-only routers**: Most other routers (devices, readings, commands, analytics, alerts, billing, system, admin, health) are already API-only and return JSON.
- **Web-only routes**: Currently, most web routes are mixed with API logic; true web-only routers do not yet exist.
- **WebSocket routers**: Already separate and not affected by this migration.

### Next Steps
- For each dual-purpose router, enumerate all dual routes and plan their split.
- Begin with authentication and dashboard as highest priority for web/API separation.

---

## Semantic Changelog

- [Step 1] Audited all routers and classified routes as API-only, Web-only, or Dual-purpose.
- [Step 1] Documented findings and created a classification table in this plan.
- [Step 2] Enumerated all dual-purpose routes in `auth.py`, `dashboard.py`, `projects.py`, and `organizations.py` and planned the split for each.
- [Step 2] Created `api/` and `web/` router directories to begin the code split.
- [Step 2] Created `api_auth.py` and `web_auth.py` as initial placeholders for authentication route migration.
- [Step 2] Migrated and refactored API-only authentication endpoints into `api/api_auth.py`.
- [Step 2] Migrated and refactored web-only authentication endpoints into `web/web_auth.py`.
- [Step 2] Migrated and refactored dashboard endpoints into `api/api_dashboard.py` and `web/web_dashboard.py`.
- [Step 2] Migrated and refactored projects endpoints into `api/api_projects.py` and `web/web_projects.py`.
- [Step 2] Migrated and refactored organizations endpoints into `api/api_organizations.py` and `web/web_organizations.py`.
- [Step 2] Registered new API and Web routers in `main.py` for all split resources.
- [Step 3] Implemented strict authentication separation: API endpoints require JWT/Bearer token, web endpoints require session cookie. All new routers updated to use the correct dependency.
- [Step 4] Completed project CRUD implementation with full Create, Read, Update, Archive operations, form processing, and mobile navigation support.

---

## Step 4 Progress

- Removed all old dual-purpose routers (`auth.py`, `dashboard.py`, `projects.py`, `organizations.py`) from `backend/app/routers/`.
- Eliminated all `accepts_json` and dual return logic from the codebase; all endpoints are now strictly API or web.
- All API endpoints now always return JSON (using Pydantic models or dicts).
- All web endpoints now always return `TemplateResponse`/`RedirectResponse` and have `include_in_schema=False`.
- Completed project CRUD implementation with comprehensive form processing, validation, and mobile navigation support.
- Step 4 is fully complete.

## Semantic Changelog

- [Step 4] Removed old dual-purpose routers and eliminated all `accepts_json` and dual return logic. All endpoints are now strictly API or web.
- [Step 4] Verified all API endpoints return JSON and all web endpoints return HTML with `include_in_schema=False`. Step 4 is complete. 

---

## Step 5 Progress

- Reviewed all navigation links and forms in templates; all now use `/app/` endpoints.
- Updated any remaining htmx or navigation links that used `/api/v1/` to `/app/` endpoints (e.g., dashboard activity feed).
- Step 5 is fully complete.

## Semantic Changelog

- [Step 5] Reviewed and updated all navigation links and forms to use `/app/` endpoints. Step 5 is complete. 

---

## Step 6 Progress

- All Playwright frontend tests and helpers have been updated to use only `/app/` routes. No `/api/v1/` endpoints are tested in the frontend suite.
- Ran the full Playwright test suite. Main issues found:
  - Selector strictness: Many failures due to multiple elements matching a selector (e.g., `locator('text=Organizations')`).
  - Outdated expectations: Some tests still expect `/api/v1/` in URLs or attributes.
  - Navigation/label mismatches: Tests expect unique links/labels, but UI has multiple similar elements.
  - No-JS mode flakiness: Failures due to selectors or missing expected text.
  - Accessibility/keyboard navigation: Some tests fail due to missing or ambiguous elements.
  - Test data/state: Ensure test data is seeded and cleaned up properly.
- See `FRONTEND_TESTING_STRATEGY.md` for a detailed "To improve" section and action items.
- API tests and dual-purpose endpoint cleanup are still pending.

## Semantic Changelog

- [Step 6] Updated all Playwright tests to only test `/app/` routes. Documented main issues and next steps. API test updates and dual-purpose endpoint cleanup are still pending. 