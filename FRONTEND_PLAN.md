# LIM OS Frontend Implementation Plan

## 🚀 **Implementation Progress**

### ✅ **COMPLETED** (December 2024)
- **✅ Foundation Setup**: Templates and static directories created
- **✅ Docker Configuration**: Fixed path issues, containers running successfully
- **✅ FastAPI Integration**: Jinja2 templates and static files properly configured
- **✅ Base Template**: `base.html` created with proper structure and asset loading
- **✅ Static Assets**: CSS, JS, and HTMX files in place and serving correctly
- **✅ Backend Verification**: API operational at `http://localhost:8000`
- **✅ Template Rendering**: Frontend test endpoint working (`/frontend-test`)
- **✅ Database**: TimescaleDB migrations applied, system ready
- **✅ Authentication System**: Complete login, registration, and profile pages
- **✅ Navigation Component**: Responsive navbar with auth-aware navigation
- **✅ Content Negotiation**: HTML/JSON responses from same endpoints

### 🎯 **CURRENT STATUS**
**Authentication Complete** - Ready for dashboard and organization management

The authentication system is fully operational:
- ✅ Login page: `/api/v1/auth/login` with form validation and error handling
- ✅ Registration page: `/api/v1/auth/register` with organization selection
- ✅ Profile page: `/api/v1/auth/profile` with account management features
- ✅ Responsive navigation with user dropdown and mobile menu
- ✅ Content negotiation: HTML for browsers, JSON for programmatic clients
- ✅ Consistent `/api/v1` prefix maintained for all endpoints

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
4. **🎯 Dashboard**: Build user dashboard with orgs, stats, and activity feed **NEXT**
5. **Organization/Project Management**: CRUD flows for orgs and projects
6. **Bioreactor Enrollment/Monitoring**: Multi-step form, real-time dashboard
7. **Process Designer**: Interactive step/logic management with HTMX
8. **Experiment Management**: Create, monitor, and control experiments
9. **Polish**: Accessibility, error handling, mobile optimization, inline validation

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

**This plan should be reviewed and approved before frontend code is generated.** 