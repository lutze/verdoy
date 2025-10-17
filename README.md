# VerdoyLab - Laboratory Information Management System

Currently in pre-alpha and subject to significant breaking changes. 

VerdoyLab is an experiment in building a modern SaaS platform from scratch using AI Copilots. Envisioned as an open-source Laboratory (Information) Management System designed for research labs and R&D facilities, VerdoyLab has been fully pair-programmed with Cursor, using an intentional and iterative design/build practice. 

The eventual platform will, hopefully, be a simple, performant, and secure system to build the information management of an R&D lab. It will support remote programmatic integration for lab tools and sensors; multimodal data manage with native graph, vector and timeseries storage; project, process experiment and hardware management; and user/back-office management for one to many labs in one to many organizations, in an either multi- or data separated tenancy configuraiton. 

VerdoyLab is built on a FastAPI backend with Jinja 2 frontend, connected to a PostgreSQL + TimescaleDB database for high-performance data management and real-time IoT device integration.

Significant history of the work can be found in the project directories under /docs, and more recently stored in a Linear project that Cursor has been using to manage increasingly complicated dependencies and project structures (ask about access if you'd like to review). 

As development continues, progress updates will be documented here: (TBD)

## 🚀 Features

- **IoT Device Management**: ESP32 device registration, configuration, and monitoring (in progress)
- **Real-time Data Collection**: Time-series sensor data ingestion and storage (in progress)
- **User Authentication**: JWT-based authentication with organization management (partially implemented)
- **Experiment Tracking**: Comprehensive experiment and trial management (working prototype)
- **Bioreactor Integration**: Reference hardware management with settings for sensor reading and actuation (working prototpye)
- **RESTful APIs**: Full REST API with OpenAPI documentation (working prototype)
- **WebSocket Support**: Real-time data streaming and device communication (in-progress)
- **Multi-tenant Architecture**: Organization-based data isolation (in progress)
- **Event Sourcing**: Immutable audit trail for all system changes (in progress)
- **Knowledge Graph**: Rich entity relationships and graph queries (working representation)
- **MCP Service**: An MCP server that streamlines Agentic-LLM-to-API interaction. (future)

## 🏗️ Architecture

The system implements a simple architecture with separated concerns and a low-Javascript frontend:

- **Backend**: FastAPI with async Python
- **Database**: PostgreSQL with TimescaleDB extension for time-series data
- **Frontend**: Server-rendered HTML using Jinja, with progressive enhancement
- **IoT Integration**: ESP32 device support with MQTT/HTTP protocols
- **Containerization**: Docker and Docker Compose for easy deployment

### Repository Structure

```
.
├── backend/               # FastAPI backend service
│   ├── app/              # Application code
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API route handlers
│   │   ├── services/     # Business logic
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── templates/    # HTML templates
│   │   └── static/       # CSS/JS assets
│   ├── tests/            # Backend tests
│   └── requirements.txt  # Python dependencies
├── database/             # Database migrations and schemas
│   ├── migrations/       # SQL migration files
│   └── setup_db.py      # Database setup script
├── tests/               # Frontend tests (Playwright)
├── docs/                # Documentation
├── docker-compose.yml   # Container orchestration
└── README.md           # This file
```


## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lutze/verdoy.git
   cd verdoy
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432

### Development Setup

For development with live reloading:

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 Usage

### API Overview

The VerdoyLab API provides a comprehensive IoT device management system with the following key features:

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


## 🧪 Testing

Run the test suite:

```bash
# Backend tests
cd backend
pytest

# Frontend tests
npm test
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] Native vector storage support
- [ ] Robust native graph storage
- [ ] Graphical process builder
- [ ] Complete task-level role-based permissions 
- [ ] Tenancy support for multiple organizations
- [ ] More robust e2e testing and internal administration dashboards
- [ ] MCP and A2A extensions from programmatic APIs
- [ ] Multi-language support
- [ ] Mobile app support

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-username/verdoylab/issues)
- 💬 [Discussions](https://github.com/your-username/verdoylab/discussions)

## 🙏 Acknowledgments

- MVP feature set refined through discussions with Ivan Labra and Alena Tanakra of [KaskBIO](https://kask.bio)
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database powered by [PostgreSQL](https://www.postgresql.org/) and [TimescaleDB](https://www.timescale.com/)
- IoT integration for [ESP32](https://www.espressif.com/en/products/socs/esp32) devices