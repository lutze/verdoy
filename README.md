# LMS Evo Core POC


## Getting started

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.com/kask561948/kask-core-mvp/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

-- 

## Description
*Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.*

### Repository Structure

The project follows a microservices architecture with the following main components:

```
.
├── backend/               # Backend service
│   ├── dockerfile         # Backend service container configuration
│   ├── main.py            # Main application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/              # Frontend application
│   └── kask-core-nextjs/  # Next.js web application
├── database/              # Database migrations and schemas
├── docker-compose.yml     # Container orchestration configuration
└── README.md              # Project documentation
```

The project uses Docker for containerization and includes database migrations for schema management. The backend is built with Python, while the frontend uses Next.js. Each service has its own container configuration and can be orchestrated using Docker Compose.


## Badges
*On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.*

## Visuals
*Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.*

## Installation
*Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.*

## Usage
*Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.*

### API Overview

The LMS Core API provides a comprehensive IoT device management system with the following key features:

- **User Authentication**: JWT-based authentication for web interface users
- **Device Management**: ESP32 device registration, configuration, and monitoring
- **Data Ingestion**: Sensor readings collection and storage
- **Device Control**: Command queuing and device control operations
- **Real-time Data**: WebSocket endpoints for live data streaming

### Authentication

#### User Authentication (Web Interface)

Users authenticate using JWT tokens:

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "organization_id": "uuid",
    "is_active": true
  }
}
```

Use the token in subsequent requests:

```bash
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

#### Device Authentication (IoT Devices)

ESP32 devices authenticate using API keys stored in their properties:

```bash
# Device sends sensor readings
curl -X POST "http://localhost:8000/api/v1/devices/{device_id}/readings" \
  -H "Authorization: Bearer device_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "uuid",
    "readings": [
      {
        "sensor_type": "temperature",
        "value": 23.5,
        "unit": "°C",
        "timestamp": "2024-01-01T12:00:00Z",
        "quality": "good"
      }
    ]
  }'
```

### Key API Endpoints

#### Device Management

```bash
# List user's devices
GET /api/v1/devices

# Register new device
POST /api/v1/devices
{
  "name": "My ESP32 Device",
  "description": "Temperature sensor in lab",
  "location": "Lab A",
  "firmware_version": "1.0.0",
  "hardware_model": "ESP32-WROOM-32",
  "mac_address": "24:6F:28:XX:XX:XX"
}

# Get device details
GET /api/v1/devices/{device_id}

# Update device
PUT /api/v1/devices/{device_id}
```

#### Data Ingestion (Device → Server)

```bash
# Send sensor readings
POST /api/v1/devices/{device_id}/readings

# Device heartbeat
POST /api/v1/devices/{device_id}/heartbeat

# Update device status
POST /api/v1/devices/{device_id}/status
```

#### Data Retrieval (Web Dashboard)

```bash
# Get device readings
GET /api/v1/devices/{device_id}/readings

# Get latest readings
GET /api/v1/devices/{device_id}/readings/latest

# Get reading statistics
GET /api/v1/devices/{device_id}/readings/stats
```

#### Device Control (Server → Device)

```bash
# Queue command for device
POST /api/v1/devices/{device_id}/commands

# Device polls for commands
GET /api/v1/devices/{device_id}/commands

# Mark command as executed
PUT /api/v1/devices/{device_id}/commands/{cmd_id}
```

### WebSocket Endpoints

For real-time data streaming:

```javascript
// Live sensor data
const ws = new WebSocket('ws://localhost:8000/ws/live-data');

// Device status events
const ws = new WebSocket('ws://localhost:8000/ws/device-status');

// Real-time alerts
const ws = new WebSocket('ws://localhost:8000/ws/alerts');
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Database Migrations

The project uses a custom migration runner to manage database schema changes. Migrations are stored in the `database/migrations` directory and are applied in alphabetical order.

For detailed instructions on setting up the database, running and rolling back the migrations, refer to `database/README.md`


## Support
*Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.*

## Roadmap
*If you have ideas for releases in the future, it is a good idea to list them in the README.*

## Contributing
*State if you are open to contributions and what your requirements are for accepting them.*

*For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.*

*You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.*

## Authors and acknowledgment
*Show your appreciation to those who have contributed to the project.*

## License
*For open source projects, say how it is licensed.*

## Project status
*If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.*
