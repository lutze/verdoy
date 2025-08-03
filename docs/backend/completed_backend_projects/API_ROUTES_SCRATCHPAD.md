# API Routes Scratchpad - Comparison of API Plan vs Implementation

## API Plan Routes (from API plan.md)

### Authentication & User Management
- [x] POST   /api/v1/auth/register
- [x] POST   /api/v1/auth/login  
- [x] POST   /api/v1/auth/logout
- [x] POST   /api/v1/auth/refresh
- [x] POST   /api/v1/auth/reset-password
- [x] GET    /api/v1/auth/me
- [ ] GET    /api/v1/users/profile
- [ ] PUT    /api/v1/users/profile
- [ ] DELETE /api/v1/users/account

### Device Management (Web Interface)
- [x] GET    /api/v1/devices                    # List user's devices
- [x] POST   /api/v1/devices                    # Register new device
- [x] GET    /api/v1/devices/{device_id}        # Get device details
- [x] PUT    /api/v1/devices/{device_id}        # Update device (name, location, etc.)
- [x] DELETE /api/v1/devices/{device_id}        # Remove device
- [x] GET    /api/v1/devices/{device_id}/status # Current status, last seen, etc.
- [x] GET    /api/v1/devices/{device_id}/health # Health metrics, diagnostics
- [x] POST   /api/v1/devices/{device_id}/reboot # Trigger device reboot
- [x] GET    /api/v1/devices/{device_id}/config # Get device configuration
- [x] PUT    /api/v1/devices/{device_id}/config # Update device settings

### IoT Data Ingestion (Device → Server)
- [x] POST   /api/v1/devices/{device_id}/readings        # Batch sensor readings
- [x] POST   /api/v1/devices/{device_id}/heartbeat       # Device keep-alive
- [x] POST   /api/v1/devices/{device_id}/status          # Device status updates
- [ ] POST   /api/v1/devices/{device_id}/logs            # Device error/debug logs
- [x] POST   /api/v1/devices/provision                   # Initial device setup
- [x] GET    /api/v1/devices/{device_id}/provision-status # Check provisioning

### IoT Commands & Control (Server → Device)
- [x] GET    /api/v1/devices/{device_id}/commands        # Device polls for commands
- [x] POST   /api/v1/devices/{device_id}/commands        # Queue command for device
- [x] PUT    /api/v1/devices/{device_id}/commands/{cmd_id} # Mark command as executed
- [x] POST   /api/v1/devices/{device_id}/control/restart
- [x] POST   /api/v1/devices/{device_id}/control/update-firmware
- [x] POST   /api/v1/devices/{device_id}/control/calibrate
- [x] POST   /api/v1/devices/{device_id}/control/set-reading-interval

### Data Retrieval & Analytics (Web Dashboard)
- [x] GET    /api/v1/readings                            # Query readings across devices
- [x] GET    /api/v1/readings/latest                     # Latest readings from all devices
- [x] GET    /api/v1/readings/export                     # Export data (CSV/JSON)
- [x] GET    /api/v1/devices/{device_id}/readings        # Historical readings
- [x] GET    /api/v1/devices/{device_id}/readings/latest # Latest readings
- [ ] GET    /api/v1/devices/{device_id}/readings/stats  # Statistical summaries
- [x] GET    /api/v1/analytics/summary                   # Dashboard summary
- [x] GET    /api/v1/analytics/trends                    # Time-based trends
- [x] GET    /api/v1/analytics/alerts                    # Active alerts/notifications
- [x] GET    /api/v1/analytics/reports                   # Predefined reports

### Real-time & WebSocket
- [x] WS     /ws/live-data                               # Live sensor readings
- [x] WS     /ws/device-status                          # Device online/offline events
- [x] WS     /ws/alerts                                 # Real-time alerts
- [ ] GET    /api/v1/stream/readings                    # SSE for live readings
- [ ] GET    /api/v1/stream/device-events              # SSE for device events

### Alerts & Notifications
- [x] GET    /api/v1/alerts/rules                       # List alert rules
- [x] POST   /api/v1/alerts/rules                       # Create alert rule
- [x] PUT    /api/v1/alerts/rules/{rule_id}            # Update alert rule
- [x] DELETE /api/v1/alerts/rules/{rule_id}            # Delete alert rule
- [x] GET    /api/v1/alerts                             # Alert history
- [x] PUT    /api/v1/alerts/{alert_id}/acknowledge      # Mark alert as seen
- [x] GET    /api/v1/alerts/active                      # Currently active alerts

### Organization & Account Management
- [x] GET    /api/v1/organizations                      # User's organizations
- [x] POST   /api/v1/organizations                      # Create organization
- [x] GET    /api/v1/organizations/{org_id}            # Organization details
- [ ] PUT    /api/v1/organizations/{org_id}            # Update organization
- [ ] GET    /api/v1/organizations/{org_id}/members     # Team members
- [ ] POST   /api/v1/organizations/{org_id}/invite      # Invite team member
- [ ] DELETE /api/v1/organizations/{org_id}/members/{user_id} # Remove member
- [x] GET    /api/v1/billing/subscription               # Current plan
- [x] POST   /api/v1/billing/subscription               # Update subscription
- [x] GET    /api/v1/billing/usage                      # Usage statistics

### System & Admin
- [x] GET    /api/v1/system/health                      # API health check
- [x] GET    /api/v1/system/metrics                     # System metrics
- [x] GET    /api/v1/system/version                     # API version info
- [x] GET    /api/v1/admin/users                        # All users (admin only)
- [x] GET    /api/v1/admin/devices                      # All devices (admin only)
- [x] GET    /api/v1/admin/stats                        # Platform statistics

## Existing Routes (from current implementation)

### Authentication Router (/api/v1/auth)
- POST /register
- POST /login
- POST /logout
- POST /refresh
- GET /me
- PUT /me
- POST /forgot-password
- POST /reset-password
- POST /change-password

### Devices Router (/api/v1/devices)
- GET "" (list devices)
- POST "" (create device)
- GET /{device_id} (get device)
- PUT /{device_id} (update device)
- DELETE /{device_id} (delete device)
- GET /{device_id}/status (device status)
- GET /{device_id}/health (device health)
- GET /{device_id}/config (get config)
- PUT /{device_id}/config (update config)
- POST /provision (device provisioning)
- GET /{device_id}/provision-status (provision status)
- POST /{device_id}/readings (receive readings)
- POST /{device_id}/heartbeat (device heartbeat)
- POST /{device_id}/status (update device status)
- GET /{device_id}/readings (get device readings)
- GET /{device_id}/readings/latest (latest readings)
- POST /{device_id}/reboot (reboot device)

### Commands Router (/api/v1/commands)
- GET "" (list commands)
- POST "" (create command)
- GET /{command_id} (get command)
- PUT /{command_id} (update command)
- DELETE /{command_id} (delete command)
- GET /devices/{device_id}/commands (device commands)
- POST /devices/{device_id}/commands (queue command)
- GET /devices/{device_id}/poll (poll for commands)
- PUT /devices/{device_id}/commands/{command_id}/execute (mark executed)
- POST /devices/{device_id}/control/restart (restart control)
- POST /devices/{device_id}/control/update-firmware (firmware update)
- POST /devices/{device_id}/control/calibrate (calibrate)
- POST /devices/{device_id}/control/set-reading-interval (set interval)
- GET /templates (command templates)
- POST /templates (create template)
- POST /bulk (bulk commands)

### Readings Router (/api/v1/readings)
- GET "" (list readings)
- GET /latest (latest readings)
- GET /stats (reading stats)
- GET /aggregation (aggregated data)
- POST /export (export data)
- GET /quality (data quality)
- GET /trends (trends)
- DELETE /{reading_id} (delete reading)
- POST /bulk-delete (bulk delete)

### Analytics Router (/api/v1/analytics)
- GET /summary (dashboard summary)
- GET /trends (trends)
- GET /alerts (alerts analytics)
- GET /reports (reports)

### Alerts Router (/api/v1/alerts)
- GET /rules (list alert rules)
- POST /rules (create alert rule)
- PUT /rules/{rule_id} (update alert rule)
- DELETE /rules/{rule_id} (delete alert rule)
- GET "" (list alerts)
- GET /active (active alerts)
- PUT /{alert_id}/acknowledge (acknowledge alert)

### Organizations Router (/api/v1/organizations)
- GET "" (list organizations)
- POST "" (create organization)
- GET /{org_id} (organization details)

### Billing Router (/api/v1/billing)
- GET /subscription (get subscription)
- POST /subscription (update subscription)
- GET /usage (usage statistics)

### System Router (/api/v1/system)
- GET /health (health check)
- GET /metrics (system metrics)
- GET /version (version info)

### Admin Router (/api/v1/admin)
- GET /users (all users)
- GET /devices (all devices)
- GET /stats (platform stats)

### Health Router (/api/v1/health)
- GET "" (health check)
- GET /info (system info)

### WebSocket Routers
- WS /ws/live-data (live data)
- WS /ws/device-status (device status)
- WS /ws/alerts (alerts)

## Missing Routes (API Plan vs Implementation)

### Authentication & User Management
- [ ] GET    /api/v1/users/profile
- [ ] PUT    /api/v1/users/profile  
- [ ] DELETE /api/v1/users/account

### IoT Data Ingestion
- [ ] POST   /api/v1/devices/{device_id}/logs            # Device error/debug logs

### Data Retrieval & Analytics
- [ ] GET    /api/v1/devices/{device_id}/readings/stats  # Statistical summaries

### Real-time & WebSocket
- [ ] GET    /api/v1/stream/readings                    # SSE for live readings
- [ ] GET    /api/v1/stream/device-events              # SSE for device events

### Organization & Account Management
- [ ] PUT    /api/v1/organizations/{org_id}            # Update organization
- [ ] GET    /api/v1/organizations/{org_id}/members     # Team members
- [ ] POST   /api/v1/organizations/{org_id}/invite      # Invite team member
- [ ] DELETE /api/v1/organizations/{org_id}/members/{user_id} # Remove member

## Summary

**Total API Plan Routes**: 47
**Total Implemented Routes**: 42
**Missing Routes**: 5

### Missing Route Categories:
1. **User Profile Management** (3 routes) - Separate user profile endpoints
2. **Device Logs** (1 route) - Device error/debug logging
3. **Device Reading Stats** (1 route) - Statistical summaries for device readings
4. **Server-Sent Events** (2 routes) - Alternative to WebSocket for real-time data
5. **Organization Management** (4 routes) - Team member management and organization updates

### Implementation Status:
- ✅ **Core Device Management**: Complete
- ✅ **Authentication**: Complete (except user profile endpoints)
- ✅ **Data Ingestion**: Complete (except device logs)
- ✅ **Device Control**: Complete
- ✅ **Analytics**: Complete (except device-specific stats)
- ✅ **Alerts**: Complete
- ✅ **Basic Organization**: Complete
- ✅ **Billing**: Complete
- ✅ **System & Admin**: Complete
- ✅ **WebSocket**: Complete
- ❌ **User Profile Management**: Missing
- ❌ **Device Logs**: Missing
- ❌ **Device Reading Stats**: Missing
- ❌ **Server-Sent Events**: Missing
- ❌ **Advanced Organization Management**: Missing 