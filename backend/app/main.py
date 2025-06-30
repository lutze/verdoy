"""
LMS Core API - Main Application Entry Point

This is the main FastAPI application that orchestrates all components:
- Configuration management
- Database initialization
- Middleware setup
- Router registration
- Exception handling
- Health monitoring

The application follows a clean architecture pattern with:
- Dependency injection
- Service layer abstraction
- Proper error handling
- Comprehensive logging
- Health monitoring
- Real-time WebSocket support

Migration Status: Phase 6 - Main Application Refactoring Complete
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import configuration and core components
from app.config import settings
from app.database import init_db, check_db_connection
from app.exceptions import (
    LMSException,
    DatabaseConnectionException,
    ConfigurationException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException
)

# Import middleware setup functions
from app.middleware import (
    setup_cors_middleware,
    setup_logging_middleware,
    setup_websocket_middleware
)

# Import all routers from the new app structure
from app.routers import (
    # Core functionality routers
    auth_router,
    devices_router,
    readings_router,
    commands_router,
    
    # Feature routers
    analytics_router,
    alerts_router,
    organizations_router,
    billing_router,
    
    # System routers
    system_router,
    admin_router,
    health_router,
    
    # WebSocket routers
    live_data_ws_router,
    device_status_ws_router,
    alerts_ws_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown operations.
    
    Handles:
    - Database initialization and connection verification
    - Configuration validation
    - Service startup (Redis, message queues, etc.)
    - Graceful shutdown procedures
    """
    # Startup operations
    logger.info("Starting up LMS Core API...")
    startup_time = datetime.utcnow()
    
    try:
        # Validate configuration
        logger.info("Validating application configuration...")
        if not settings.validate():
            raise ConfigurationException("Invalid application configuration")
        logger.info("Configuration validated successfully")
        
        # Initialize database
        logger.info("Initializing database connection...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Verify database connection
        logger.info("Verifying database connection...")
        if check_db_connection():
            logger.info("Database connection verified successfully")
        else:
            logger.error("Database connection verification failed")
            raise DatabaseConnectionException("Cannot establish database connection")
        
        # TODO: Initialize additional services
        # - Redis connection for caching
        # - Message queue for background tasks
        # - WebSocket connection manager
        # - Alert notification service
        # - Analytics processing service
        
        startup_duration = datetime.utcnow() - startup_time
        logger.info(f"Application startup completed in {startup_duration.total_seconds():.2f} seconds")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise e
    
    yield
    
    # Shutdown operations
    logger.info("Shutting down LMS Core API...")
    shutdown_time = datetime.utcnow()
    
    try:
        # TODO: Implement graceful shutdown procedures
        # - Close database connections
        # - Stop background tasks
        # - Close WebSocket connections
        # - Flush caches
        # - Stop monitoring services
        
        shutdown_duration = datetime.utcnow() - shutdown_time
        logger.info(f"Application shutdown completed in {shutdown_duration.total_seconds():.2f} seconds")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

def create_app() -> FastAPI:
    """
    Application factory function that creates and configures the FastAPI application.
    
    This function follows the application factory pattern for better testing
    and configuration management.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    
    # Create FastAPI application instance
    app = FastAPI(
        title=settings.app_name,
        description="""
        IoT SaaS API for ESP32 device management and monitoring.
        
        ## Features
        
        ### Core Functionality
        - **Authentication**: User registration, login, and JWT token management
        - **Device Management**: ESP32 device registration, configuration, and monitoring
        - **Data Ingestion**: Sensor readings collection and storage
        - **Device Control**: Command queuing and device control operations
        
        ### Advanced Features
        - **Analytics**: Dashboard analytics and data reporting
        - **Alerts**: Alert rules and notification management
        - **Organizations**: Multi-tenant organization management
        - **Billing**: Subscription and usage management
        - **Real-time**: WebSocket endpoints for live data streaming
        
        ### System Management
        - **Health Monitoring**: System health checks and metrics
        - **Admin Functions**: Administrative operations and platform management
        
        ## API Versioning
        
        All endpoints are versioned with `/api/v1/` prefix for future compatibility.
        
        ## Architecture
        
        This API follows a clean architecture pattern with:
        - Service layer for business logic
        - Dependency injection for loose coupling
        - Comprehensive error handling
        - Real-time WebSocket support
        - Multi-tenant organization support
        """,
        version=settings.version,
        lifespan=lifespan,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url="/openapi.json",
        debug=settings.debug
    )
    
    # Add middleware
    setup_cors_middleware(app)
    setup_logging_middleware(app)
    setup_websocket_middleware(app)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routers with API versioning
    register_routers(app)
    
    # Add root endpoint
    @app.get("/", tags=["root"])
    def read_root():
        """
        Root endpoint providing API information and status.
        """
        return {
            "message": "LMS Core API",
            "version": settings.version,
            "environment": settings.environment,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "docs": f"{settings.docs_url}",
            "redoc": f"{settings.redoc_url}"
        }
    
    return app

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers for consistent error responses.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(LMSException)
    async def lms_exception_handler(request: Request, exc: LMSException):
        """Handle custom LMS exceptions."""
        logger.error(f"LMS Exception: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "type": exc.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions."""
        logger.warning(f"Validation Error: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(AuthenticationException)
    async def authentication_exception_handler(request: Request, exc: AuthenticationException):
        """Handle authentication exceptions."""
        logger.warning(f"Authentication Error: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Error",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(AuthorizationException)
    async def authorization_exception_handler(request: Request, exc: AuthorizationException):
        """Handle authorization exceptions."""
        logger.warning(f"Authorization Error: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=403,
            content={
                "error": "Authorization Error",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException):
        """Handle not found exceptions."""
        logger.info(f"Not Found: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(ConflictException)
    async def conflict_exception_handler(request: Request, exc: ConflictException):
        """Handle conflict exceptions."""
        logger.warning(f"Conflict: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=409,
            content={
                "error": "Conflict",
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unhandled Exception: {str(exc)} - {request.url}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if not settings.debug else str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with proper versioning and prefixes.
    
    Args:
        app: FastAPI application instance
    """
    
    # Core functionality routers
    app.include_router(
        auth_router,
        prefix=f"{settings.api_prefix}/auth",
        tags=["Authentication"]
    )
    
    app.include_router(
        devices_router,
        prefix=f"{settings.api_prefix}/devices",
        tags=["Device Management"]
    )
    
    app.include_router(
        readings_router,
        prefix=f"{settings.api_prefix}/readings",
        tags=["Data Ingestion"]
    )
    
    app.include_router(
        commands_router,
        prefix=f"{settings.api_prefix}/commands",
        tags=["Device Control"]
    )
    
    # Feature routers
    app.include_router(
        analytics_router,
        prefix=f"{settings.api_prefix}/analytics",
        tags=["Analytics"]
    )
    
    app.include_router(
        alerts_router,
        prefix=f"{settings.api_prefix}/alerts",
        tags=["Alerts"]
    )
    
    app.include_router(
        organizations_router,
        prefix=f"{settings.api_prefix}/organizations",
        tags=["Organizations"]
    )
    
    app.include_router(
        billing_router,
        prefix=f"{settings.api_prefix}/billing",
        tags=["Billing"]
    )
    
    # System routers
    app.include_router(
        system_router,
        prefix=f"{settings.api_prefix}/system",
        tags=["System"]
    )
    
    app.include_router(
        admin_router,
        prefix=f"{settings.api_prefix}/admin",
        tags=["Admin"]
    )
    
    app.include_router(
        health_router,
        prefix=f"{settings.api_prefix}/health",
        tags=["Health"]
    )
    
    # WebSocket routers (no API prefix for WebSocket endpoints)
    app.include_router(
        live_data_ws_router,
        tags=["WebSocket - Live Data"]
    )
    
    app.include_router(
        device_status_ws_router,
        tags=["WebSocket - Device Status"]
    )
    
    app.include_router(
        alerts_ws_router,
        tags=["WebSocket - Alerts"]
    )

# Create the application instance
app = create_app()

# Legacy event handlers for backward compatibility
# These will be removed in future versions
@app.on_event("startup")
async def startup_event():
    """
    Legacy startup event handler for backward compatibility.
    The main startup logic is now handled in the lifespan context manager.
    """
    logger.info("Legacy startup event triggered")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Legacy shutdown event handler for backward compatibility.
    The main shutdown logic is now handled in the lifespan context manager.
    """
    logger.info("Legacy shutdown event triggered")

if __name__ == "__main__":
    import uvicorn
    
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 