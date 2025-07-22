# LIM OS Frontend Implementation Plan

## 🚀 **Implementation Progress**

### ✅ **COMPLETED** (21 July 2025)
- **✅ Foundation Setup**: Templates and static directories created
- **✅ Docker Configuration**: Fixed path issues, containers running successfully
- **✅ FastAPI Integration**: Jinja2 templates and static files properly configured
- **✅ Base Template**: `base.html` created with proper structure and asset loading
- **✅ Static Assets**: CSS, JS, and HTMX files in place and serving correctly
- **✅ Backend Verification**: API operational at `http://localhost:8000`
- **✅ Template Rendering**: Frontend test endpoint working (`/frontend-test`)
- **✅ Database**: TimescaleDB migrations applied, system ready
- **✅ Authentication System**: Complete login, registration, and profile pages with dual authentication (JWT + session cookies)
- **✅ Navigation Component**: Responsive navbar with auth-aware navigation
- **✅ Content Negotiation**: HTML/JSON responses from same endpoints
- **✅ Test User Migration**: Default test user (`test@example.com` / `testpassword123`) is always created via migration and works for login
- **✅ Auth Redirects**: Post-login and logout redirects now use correct `/app/` URLs
- **✅ Dashboard System**: Complete dashboard with real-time stats, organization cards, and activity feed
- **✅ Session Authentication**: Secure HTTP-only cookies for web browsers with JWT tokens for API clients
- **✅ Template System**: Shared Jinja2 configuration with custom filters (number_format, etc.)
- **✅ Database Compatibility**: Cross-database JSON support for PostgreSQL/TimescaleDB and SQLite

### 🎯 **CURRENT STATUS**
**Authentication & Dashboard Complete** - Ready for organization and project management

The authentication and dashboard systems are fully operational:
- ✅ **Dual Authentication**: JWT Bearer tokens for API clients, HTTP-only session cookies for web browsers
- ✅ **Session Management**: Secure cookie handling with proper expiration and security flags
- ✅ **Login Flow**: Complete login → dashboard redirect with session persistence
- ✅ **Dashboard page**: `/app/dashboard` with organization overview and statistics
- ✅ **Real-time updates**: HTMX polling for stats and activity feed
- ✅ **Organization cards**: Display with stats, activity, and quick actions
- ✅ **Summary statistics**: Live-updating stats with responsive grid layout and formatted numbers
- ✅ **Activity feed**: Recent activity with organization context
- ✅ **Quick actions**: Direct links to key features (organizations, devices, experiments, etc.)
- ✅ **Responsive design**: Mobile-first layout with proper breakpoints
- ✅ **Progressive enhancement**: Works without JavaScript, enhanced with HTMX
- ✅ **Cross-database compatibility**: Shared templates and JSON handling for PostgreSQL and SQLite

---

## 1. Project Structure

```
backend/app/
  templates/                # Jinja2 templates (HTML) ✅ CREATED
    base.html               # Main layout ✅ IMPLEMENTED
    components/             # Reusable UI components (cards, forms, nav) ✅ STRUCTURE READY
      navbar.html           # Navigation component ✅ IMPLEMENTED
    pages/                  # Page-level templates ✅ STRUCTURE READY
      auth/                 # Login, registration, profile ✅ COMPLETED
        login.html          # Login page with validation ✅ IMPLEMENTED
        register.html       # Registration with org selection ✅ IMPLEMENTED
        profile.html        # User profile management ✅ IMPLEMENTED
      dashboard/            # User dashboard
      organizations/        # Org list, detail, settings
      projects/             # Project list, detail
      processes/            # Process designer, process list
      experiments/          # Experiment list, detail, monitor
      bioreactors/          # Enrollment, dashboard, control
    partials/               # HTMX fragments, modals, etc. ✅ STRUCTURE READY
  static/                   # Static assets ✅ CREATED & SERVING
    css/
      main.css              # Core styles (mobile-first, grid/flexbox) ✅ BASIC VERSION
      components.css        # UI component styles ✅ BASIC VERSION
    js/
      htmx.min.js           # HTMX for dynamic interactions ✅ INCLUDED
      app.js                # Minimal JS for enhancement ✅ BASIC VERSION
    images/                 # Icons, logos, etc. ✅ STRUCTURE READY
```

## 2. Core Pages & Components

### ✅ Authentication (COMPLETED)
- ✅ Login (HTML form, server-side validation)
- ✅ Registration (HTML form with organization selection)
- ✅ Logout (POST endpoint with redirect)
- ✅ Profile (view/edit, change password, API key management)

### 🆕 Navigation & Routing Strategy (Planned)
- All frontend pages will use a unified `/app` URL prefix for clarity and separation from API endpoints.
- Navigation links and routes will be as follows:
    - `/app` : Base home page
    - `/app/dashboard` : User's overall dashboard (projects, experiments, bioreactors, etc.)
    - `/app/admin/` : Admin area (profile, user, organization info)
    - `/app/admin/profile/` : User profile page
    - `/app/admin/organization/` : Organization info and management
    - `/app/projects` : Project list and detail
    - `/app/experiments` : Experiment management
    - `/app/bioreactors` : Bioreactor management
    - `/app/logout` : Logout endpoint
    - `/app/login` : Login endpoint
- All navigation components and links will be updated to use this structure.
- Existing `/api/v1/` HTML endpoints will be migrated to `/app/` as part of this transition.

### 🆕 Common Navigation (Planned)
- A shared navigation bar will be included at the top of every page.
- Navigation links will route to the base page for each major function (Dashboard, Organizations, Projects, Processes, Experiments, Bioreactors, Profile).
- The navigation will display a Log In or Log Out button depending on authentication state.
- Navigation will be implemented as a Jinja2 component (`components/navbar.html`) and included in the base template.

### 🆕 Base Home Page (Planned)
- A root-level home page will be created as the entry point for the application.
- The home page will provide links to all major sections and serve as the foundation for further page development.
- The home page will use the common navigation component.

### Dashboard
- List of organizations (cards/list)
- Summary stats (active experiments, online bioreactors)
- Recent activity feed (HTMX polling)

### Organization Management
- Organization list (table/cards)
- Create organization (form)
- Organization detail (tabs: overview, members, projects, bioreactors, settings)
- Member management (invite, remove, role change)

### Project Management
- Project list (per organization)
- Create project (form)
- Project detail (processes, experiments, bioreactors, metadata)

### Process Designer
- List of processes (per project)
- Process detail (steps, logic)
- Interactive designer (add/remove steps, configure logic, HTMX for dynamic fields)
- Save as template

### Experiment Management
- Create experiment (select process, bioreactor)
- Experiment detail (status, controls, real-time data, history)
- Monitor experiment (HTMX polling for live data)
- Start/pause/stop controls

### Bioreactor Management
- Enrollment (multi-step form, sensor/actuator config)
- Bioreactor dashboard (real-time sensor data, status, controls)
- Manual control panel (actuators, safety confirmations)

### User Profile
- View/edit info
- Change password
- API key management
- Notification preferences

## 3. Integration Points
- All forms submit to FastAPI backend endpoints (HTML response)
- HTMX used for:
  - Polling (real-time data, activity feeds)
  - Dynamic form fields (add/remove steps, sensors, actuators)
  - Partial updates (modals, inline edits)
- WebSocket endpoints for live experiment/bioreactor data (future enhancement)

## 4. Implementation Milestones

1. **✅ Setup**: Add templates/ and static/ directories, configure FastAPI for Jinja2 and static files **COMPLETE**
2. **✅ Base Template**: Create `base.html` with navigation, layout, and responsive design **COMPLETE**
3. **✅ Authentication**: Implement login, registration, logout, and profile pages **COMPLETE**
4. **✅ Dashboard**: Build user dashboard with orgs, stats, and activity feed **COMPLETE**
5. **🆕 Navigation Refactor**: Update all frontend routes and navigation to use `/app`-based URLs **NEXT**
6. **🆕 Base Home Page**: Create a root-level home page as the main entry point **NEXT**
7. **🎯 Organization/Project Management**: CRUD flows for orgs and projects **UPCOMING**
8. **Bioreactor Enrollment/Monitoring**: Multi-step form, real-time dashboard
9. **Process Designer**: Interactive step/logic management with HTMX
10. **Experiment Management**: Create, monitor, and control experiments
11. **Polish**: Accessibility, error handling, mobile optimization, inline validation

### 🔧 **Recent Technical Fixes**
- Fixed Docker static file path: `directory="app/static"`
- Fixed Docker templates path: `directory="app/templates"`
- Resolved container startup issues
- Verified API endpoints and template rendering
- **Authentication System**: Complete with content negotiation
- **Navigation Component**: Responsive navbar with authentication state
- **Router Registration**: Fixed auth routes with `/api/v1` prefix consistency

### 📋 **Development Best Practices Learned**
- **Docker Rebuilds**: Always force complete rebuild (`docker compose down && docker compose build --no-cache && docker compose up -d`) when making route or backend structural changes
- **Content Negotiation**: Single endpoints serving both HTML and JSON based on Accept headers
- **API Consistency**: Maintain `/api/v1` prefix for all endpoints (web browsers and programmatic clients)
- **Template Caching**: Python import caching can prevent route changes from taking effect without full rebuild

## 5. Design Principles
- HTML-first, works without JS
- Progressive enhancement (HTMX, minimal JS)
- Semantic, accessible markup
- Mobile-first, responsive CSS (Grid/Flexbox)
- Clear validation and error messages
- Consistent navigation and layout

## 6. Risks & Considerations
- Ensure all critical flows work without JavaScript
- Handle real-time updates efficiently (HTMX polling, future WebSocket)
- Graceful error handling and offline scenarios
- Security: CSRF tokens, input validation, role-based access

---

## 7. Frontend Smoke Testing Strategy

To ensure all frontend pages continue to load and function correctly after future changes, we will:
- Add **Playwright smoke tests** for each Core Pages & Components section as they are implemented.
- These tests will verify that key HTML pages render, forms are present, and navigation works as expected.
- Playwright tests will be run as part of CI and before major releases.

### Playwright Smoke Test Coverage

#### Authentication Pages (COMPLETED)
- [ ] Login page loads and form is visible (`/api/v1/auth/login`)
- [ ] Registration page loads and form is visible (`/api/v1/auth/register`)
- [ ] Profile page loads and user info is visible (`/api/v1/auth/profile`)
- [ ] Navigation bar renders correct links for guest and authenticated users
- [ ] Submitting login form with invalid credentials shows error
- [ ] Submitting registration form with missing fields shows error

#### Dashboard (COMPLETED)
- [x] Dashboard page loads and displays organization cards
- [x] Activity feed and stats are visible
- [x] Summary statistics update via HTMX
- [x] Organization cards display with proper stats and actions
- [x] Quick action cards link to key features
- [x] Responsive design works on mobile and desktop
- [x] Progressive enhancement (works without JavaScript)
- [x] HTMX polling for real-time updates

#### Organization Management (FUTURE)
- [ ] Organization list page loads
- [ ] Create organization form is visible
- [ ] Member management UI loads

#### Project Management (FUTURE)
- [ ] Project list and detail pages load
- [ ] Create project form is visible

#### ... (repeat for each section)

---

**All new Core Pages & Components must include Playwright smoke tests to ensure robust frontend quality.**

**This plan should be reviewed and approved before frontend code is generated.**

## 8. API Documentation Conventions for Frontend Pages

- **All new frontend (HTML) endpoints must use `include_in_schema=False` in their FastAPI route decorators.**
    - This ensures that HTML-only (web-specialized) endpoints are hidden from the OpenAPI schema, Swagger UI, and ReDoc.
    - Only JSON API endpoints intended for programmatic clients should appear in the API docs.
- **When developing new frontend pages or partials:**
    - If the route returns a Jinja2 template or HTMLResponse, always add `include_in_schema=False`.
    - Example:
      ```python
      @router.get("/my-page", response_class=HTMLResponse, include_in_schema=False)
      async def my_page(...):
          ...
      ```
- **Review all new routers for compliance before merging.** 