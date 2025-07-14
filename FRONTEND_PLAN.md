# LIM OS Frontend Implementation Plan

## 1. Project Structure

```
backend/app/
  templates/                # Jinja2 templates (HTML)
    base.html               # Main layout
    components/             # Reusable UI components (cards, forms, nav)
    pages/                  # Page-level templates
      auth/                 # Login, registration, profile
      dashboard/            # User dashboard
      organizations/        # Org list, detail, settings
      projects/             # Project list, detail
      processes/            # Process designer, process list
      experiments/          # Experiment list, detail, monitor
      bioreactors/          # Enrollment, dashboard, control
    partials/               # HTMX fragments, modals, etc.
  static/                   # Static assets
    css/
      main.css              # Core styles (mobile-first, grid/flexbox)
      components.css        # UI component styles
    js/
      htmx.min.js           # HTMX for dynamic interactions
      app.js                # Minimal JS for enhancement
    images/                 # Icons, logos, etc.
```

## 2. Core Pages & Components

### Authentication
- Login (HTML form, server-side validation)
- Registration (HTML form)
- Logout (POST endpoint)
- Profile (view/edit, change password, API key management)

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
1. **Setup**: Add templates/ and static/ directories, configure FastAPI for Jinja2 and static files
2. **Base Template**: Create `base.html` with navigation, layout, and responsive design
3. **Authentication**: Implement login, registration, logout, and profile pages
4. **Dashboard**: Build user dashboard with orgs, stats, and activity feed
5. **Organization/Project Management**: CRUD flows for orgs and projects
6. **Bioreactor Enrollment/Monitoring**: Multi-step form, real-time dashboard
7. **Process Designer**: Interactive step/logic management with HTMX
8. **Experiment Management**: Create, monitor, and control experiments
9. **Polish**: Accessibility, error handling, mobile optimization, inline validation

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