# VerdoyLab Backend API

A modern, scalable IoT device management API built with FastAPI, designed for ESP32 device monitoring and control.

## 🏗️ Architecture Overview

The VerdoyLab Backend follows a clean architecture pattern with clear separation of concerns:

```
backend/
├── app/                          # Main application package
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration management
│   ├── dependencies.py           # Dependency injection
│   ├── exceptions.py             # Custom exception handlers
│   ├── database.py               # Database connection management
│   ├── middleware/               # Custom middleware
│   │   ├── cors.py              # CORS configuration
│   │   ├── logging.py           # Logging middleware
│   │   └── websocket.py         # WebSocket middleware
│   ├── models/                   # SQLAlchemy models
│   │   ├── base.py              # Base model class
│   │   ├── user.py              # User model
│   │   ├── device.py            # Device model
│   │   ├── reading.py           # Sensor readings model
│   │   ├── alert.py             # Alerts and rules model
│   │   ├── organization.py      # Organization model
│   │   ├── billing.py           # Billing/subscription model
│   │   └── command.py           # Device commands model
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user.py              # User schemas
│   │   ├── device.py            # Device schemas
│   │   ├── reading.py           # Reading schemas
│   │   ├── alert.py             # Alert schemas
│   │   ├── organization.py      # Organization schemas
│   │   ├── billing.py           # Billing schemas
│   │   └── command.py           # Command schemas
│   ├── routers/                  # API routes
│   │   ├── auth.py              # Authentication routes
│   │   ├── devices.py           # Device management
│   │   ├── readings.py          # Data ingestion & retrieval
│   │   ├── commands.py          # Device commands & control
│   │   ├── analytics.py         # Analytics & data export
│   │   ├── alerts.py            # Alert management
│   │   ├── organizations.py     # Organization management
│   │   ├── billing.py           # Billing & subscriptions
│   │   ├── system.py            # System health & metrics
│   │   ├── admin.py             # Admin endpoints
│   │   ├── health.py            # Health check routes
│   │   └── websocket/           # WebSocket endpoints
│   │       ├── live_data.py     # Live sensor data
│   │       ├── device_status.py # Device status events
│   │       └── alerts.py        # Real-time alerts
│   ├── services/                 # Business logic layer
│   │   ├── base.py              # Base service class
│   │   ├── auth_service.py      # Authentication service
│   │   ├── device_service.py    # Device service
│   │   ├── reading_service.py   # Reading service
│   │   ├── alert_service.py     # Alert service
│   │   ├── organization_service.py # Organization service
│   │   ├── billing_service.py   # Billing service
│   │   ├── command_service.py   # Command service
│   │   ├── analytics_service.py # Analytics service
│   │   ├── notification_service.py # Notification service
│   │   ├── cache_service.py     # Cache service
│   │   ├── background_service.py # Background tasks
│   │   └── websocket_service.py # WebSocket service
│   └── utils/                    # Utility functions
│       ├── helpers.py           # Common utility functions
│       ├── validators.py        # Custom validators
│       └── exporters.py         # Data export utilities
├── tests/                        # Test suite
│   ├── conftest.py              # Test configuration
│   ├── test_api/                # API endpoint tests
│   ├── test_core/               # Core service tests
│   └── test_integration/        # Integration tests
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── dockerfile                    # Docker configuration
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+ (or SQLite for development)
- Redis (optional, for caching)
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lms-core-poc/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # For development
   pip install -r requirements-dev.txt
   
   # For production
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # For development (SQLite)
   python -c "from app.database import init_db; init_db()"
   
   # For production (PostgreSQL)
   # Run database migrations
   ```

6. **Start the application**
   ```bash
   # Development
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Production
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment

```bash
# Build the image
docker build -t lms-core-backend .

# Run with Docker Compose
docker-compose up -d
```

## 🔐 Authentication

### User Authentication (Web Interface)

Users authenticate using JWT tokens:

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Use token in subsequent requests
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer <your-token>"
```

### Device Authentication (IoT Devices)

ESP32 devices authenticate using API keys stored in their properties:

```bash
# Device sends sensor readings
curl -X POST "http://localhost:8000/api/v1/devices/{device_id}/readings" \
  -H "Authorization: Bearer <device-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "readings": [
      {
        "sensor_type": "temperature",
        "value": 23.5,
        "unit": "°C",
        "timestamp": "2024-01-01T12:00:00Z"
      }
    ]
  }'
```

## 📡 API Endpoints

### Authentication & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/refresh` | Token refresh |
| GET | `/api/v1/auth/me` | Get current user info |

### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices` | List user's devices |
| POST | `/api/v1/devices` | Register new device |
| GET | `/api/v1/devices/{device_id}` | Get device details |
| PUT | `/api/v1/devices/{device_id}` | Update device |
| DELETE | `/api/v1/devices/{device_id}` | Remove device |
| GET | `/api/v1/devices/{device_id}/status` | Get device status |
| GET | `/api/v1/devices/{device_id}/health` | Get device health |

### Data Ingestion (Device → Server)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/devices/{device_id}/readings` | Send sensor readings |
| POST | `/api/v1/devices/{device_id}/heartbeat` | Device keep-alive |
| POST | `/api/v1/devices/{device_id}/status` | Update device status |
| POST | `/api/v1/devices/{device_id}/logs` | Send device logs |

### Data Retrieval (Web Dashboard)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices/{device_id}/readings` | Get device readings |
| GET | `/api/v1/devices/{device_id}/readings/latest` | Get latest readings |
| GET | `/api/v1/devices/{device_id}/readings/stats` | Get reading statistics |
| GET | `/api/v1/analytics/summary` | Get dashboard summary |
| GET | `/api/v1/analytics/trends` | Get time-based trends |

### Device Control (Server → Device)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices/{device_id}/commands` | Device polls for commands |
| POST | `/api/v1/devices/{device_id}/commands` | Queue command for device |
| PUT | `/api/v1/devices/{device_id}/commands/{cmd_id}` | Mark command as executed |

### Real-time Data (WebSocket)

| Endpoint | Description |
|----------|-------------|
| `WS /ws/live-data` | Live sensor readings |
| `WS /ws/device-status` | Device online/offline events |
| `WS /ws/alerts` | Real-time alerts |

### System & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/system/metrics` | System metrics |
| GET | `/api/v1/system/version` | API version info |

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@db:5432/verdoy-db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Database Configuration

The API supports both PostgreSQL (production) and SQLite (development):

```bash
# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@db:5432/verdoy-db

# SQLite (development)
DATABASE_URL=sqlite:///./lms_core.db
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api/test_auth.py

# Run tests in parallel
pytest -n auto
```

### Test Configuration

Tests use a separate SQLite database and environment:

```bash
# Test environment variables
TEST_DATABASE_URL=sqlite:///./test.db
APP_ENV=testing
DEBUG=false
```

## 🚀 Development

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# Security checks
bandit -r app/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test**
   ```bash
   # Run tests
   pytest
   
   # Check code quality
   black app/ tests/
   flake8 app/ tests/
   ```

3. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push and create merge request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed health check
curl http://localhost:8000/api/v1/system/metrics
```

### Logging

The API uses structured logging with configurable levels:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Structured logging (JSON format)
logger = logging.getLogger(__name__)
logger.info("User logged in", extra={"user_id": user.id, "ip": request.client.host})
```

### Metrics

System metrics are available at `/api/v1/system/metrics`:

```json
{
  "uptime": 3600,
  "memory_usage": 128.5,
  "cpu_usage": 15.2,
  "active_connections": 42,
  "requests_per_minute": 120
}
```

## 🔒 Security

### Authentication & Authorization

- **JWT-based authentication** for web interface users
- **API key authentication** for IoT devices
- **Role-based access control** (RBAC)
- **Organization-based data isolation**

### Data Protection

- **HTTPS/TLS encryption** in transit
- **Password hashing** with bcrypt
- **Input validation** and sanitization
- **SQL injection prevention** with SQLAlchemy ORM

### Security Best Practices

1. **Environment Variables**: Never commit sensitive data to version control
2. **API Keys**: Rotate device API keys regularly
3. **CORS**: Restrict CORS origins to your frontend domains
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Logging**: Log security events and authentication attempts

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Use strong `SECRET_KEY` (min 32 characters)
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching (optional)
- [ ] Configure CORS origins for your frontend
- [ ] Set up monitoring and logging
- [ ] Configure backup procedures
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Set up health checks and monitoring

### Docker Production

```bash
# Build production image
docker build -t lms-core-backend:latest .

# Run with production environment
docker run -d \
  --name lms-core-backend \
  -p 8000:8000 \
  --env-file .env.production \
  lms-core-backend:latest
```

### Environment-Specific Configuration

```bash
# Development
cp .env.example .env.development

# Testing
cp .env.example .env.test

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.production
```

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `pytest && black app/ tests/ && flake8 app/ tests/`
4. **Commit changes**: `git commit -m "feat: add amazing feature"`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Create Pull Request**

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for all public functions
- Keep functions small and focused
- Write comprehensive tests

### Testing Requirements

- Maintain >90% test coverage
- Write unit tests for all new features
- Include integration tests for API endpoints
- Test error scenarios and edge cases

## 📚 Documentation

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connection
python -c "from app.database import get_db; print('Database OK')"

# Verify environment variables
echo $DATABASE_URL
```

#### Authentication Issues

```bash
# Check JWT token
python -c "import jwt; print(jwt.decode(token, options={'verify_signature': False}))"

# Verify secret key
echo $SECRET_KEY
```

#### CORS Issues

```bash
# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/v1/auth/login
```

### Debug Mode

Enable debug mode for detailed error messages:

```bash
# Set debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with debug logging
uvicorn app.main:app --reload --log-level debug
```

### Logs

Check application logs for errors:

```bash
# View logs
tail -f logs/lms_core.log

# Search for errors
grep ERROR logs/lms_core.log
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and API docs
- **Issues**: Create an issue on GitHub/GitLab
- **Discussions**: Use project discussions for questions
- **Email**: Contact the development team

### Reporting Bugs

When reporting bugs, please include:

1. **Environment**: OS, Python version, dependencies
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Logs**: Relevant error messages and logs
6. **Screenshots**: If applicable

### Feature Requests

When requesting features, please include:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives**: What other approaches were considered?
4. **Impact**: Who will benefit from this feature?

---

**VerdoyLab Backend** - Modern IoT device management API built with FastAPI 