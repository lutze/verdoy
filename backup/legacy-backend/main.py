"""
VerdoyLab API - Main Application Entry Point

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

Migration Status: Phase 6 - Service Layer Integration Complete
"""

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import new app structure components
from app.config import settings
from app.database import init_db, check_db_connection
from app.exceptions import (
    LMSException,
    DatabaseConnectionException,
    ConfigurationException
)

# Import all routers from the new app structure
from app.routers import (
    # Core functionality routers (implemented)
    auth_router,
    devices_router,
    readings_router,
    commands_router,
    
    # Feature routers (stubbed - need implementation)
    analytics_router,      # TODO: Implement analytics business logic
    alerts_router,         # TODO: Implement alert management system
    organizations_router,  # TODO: Implement multi-tenant organization logic
    billing_router,        # TODO: Implement billing and subscription system
    
    # System routers (stubbed - need implementation)
    system_router,         # TODO: Implement system metrics and monitoring
    admin_router,          # TODO: Implement admin functionality
    health_router,         # TODO: Implement comprehensive health checks
    
    # WebSocket routers (stubbed - need implementation)
    live_data_ws_router,       # TODO: Implement real-time data streaming
    device_status_ws_router,   # TODO: Implement device status events
    alerts_ws_router,          # TODO: Implement real-time alert notifications
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    - Service startup (future: Redis, message queues, etc.)
    - Graceful shutdown procedures
    """
    # Startup operations
    logger.info("Starting up VerdoyLab API...")
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
    logger.info("Shutting down VerdoyLab API...")
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

# Create FastAPI application instance
app = FastAPI(
    title="VerdoyLab API",
    description="""
    IoT SaaS API for ESP32 device management and monitoring.
    
    ## Features
    
    ### Core Functionality (Implemented)
    - **Authentication**: User registration, login, and JWT token management
    - **Device Management**: ESP32 device registration, configuration, and monitoring
    - **Data Ingestion**: Sensor readings collection and storage
    - **Device Control**: Command queuing and device control operations
    
    ### Features (Stubbed - In Development)
    - **Analytics**: Dashboard analytics and data reporting
    - **Alerts**: Alert rules and notification management
    - **Organizations**: Multi-tenant organization management
    - **Billing**: Subscription and usage management
    - **Real-time**: WebSocket endpoints for live data streaming
    
    ### System Management (Stubbed - In Development)
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
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Configured in settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Add additional middleware
# - Rate limiting middleware
# - Request logging middleware
# - Authentication middleware (if needed beyond router-level)
# - Performance monitoring middleware
# - Security headers middleware

# Include all routers with proper organization

# Core functionality routers (implemented and functional)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(readings_router, prefix="/api/v1")
app.include_router(commands_router, prefix="/api/v1")

# Feature routers (stubbed - return placeholder responses)
# TODO: Implement business logic for these routers
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(organizations_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")

# System routers (stubbed - basic functionality)
# TODO: Implement comprehensive system management
app.include_router(system_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

# WebSocket routers (stubbed - basic WebSocket handling)
# TODO: Implement real-time data streaming and event handling
app.include_router(live_data_ws_router)
app.include_router(device_status_ws_router)
app.include_router(alerts_ws_router)

# Global exception handlers
@app.exception_handler(LMSException)
async def lms_exception_handler(request, exc: LMSException):
    """
    Handle custom LMS exceptions with proper error responses.
    """
    logger.error(f"LMS Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": exc.error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unexpected errors.
    Provides consistent error responses and logs errors for debugging.
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    # In production, don't expose internal error details
    if settings.ENVIRONMENT == "production":
        error_detail = "An unexpected error occurred"
    else:
        error_detail = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": error_detail,
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Root endpoint
@app.get("/", tags=["root"])
def read_root():
    """
    Root endpoint providing API information and status.
    
    Returns:
        API information and status
    """
    return {
        "message": "VerdoyLab API",
        "version": "1.0.0",
        "status": "running",
        "architecture": "clean-architecture",
        "features": {
            "authentication": "implemented",
            "device_management": "implemented",
            "data_ingestion": "implemented",
            "device_control": "implemented",
            "analytics": "stubbed",
            "alerts": "stubbed",
            "organizations": "stubbed",
            "billing": "stubbed",
            "websockets": "stubbed"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "health_check": "/api/v1/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check endpoint (migrated to new structure)
@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Health status information
    """
    try:
        # Check database connection
        db_healthy = check_db_connection()
        
        # TODO: Add additional health checks
        # - Redis connection
        # - External service dependencies
        # - Disk space
        # - Memory usage
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "api": "healthy",
                "memory": "healthy",  # TODO: Implement actual check
                "disk": "healthy"     # TODO: Implement actual check
            }
        }
        
        status_code = 200 if db_healthy else 503
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Legacy endpoints - DEPRECATED (will be removed in future versions)
@app.get("/db-check", tags=["legacy"])
async def check_db():
    """
    DEPRECATED: Legacy database check endpoint.
    
    This endpoint is deprecated and will be removed in a future version.
    Use /api/v1/health instead for health checks.
    
    Returns:
        Database connection status
    """
    logger.warning("Legacy /db-check endpoint called - use /api/v1/health instead")
    
    try:
        # Use the new health check logic
        db_healthy = check_db_connection()
        
        return {
            "status": "connected" if db_healthy else "disconnected",
            "message": "Database connection check",
            "deprecated": True,
            "recommended_endpoint": "/api/v1/health"
        }
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "deprecated": True,
            "recommended_endpoint": "/api/v1/health"
        }

@app.post("/ollama-check", tags=["legacy"])
async def ollama_check():
    """
    DEPRECATED: Legacy Ollama check endpoint.
    
    This endpoint is deprecated and will be removed in a future version.
    Use appropriate service endpoints instead.
    
    Returns:
        Ollama service status
    """
    logger.warning("Legacy /ollama-check endpoint called - this endpoint is deprecated")
    
    return {
        "status": "deprecated",
        "message": "This endpoint is deprecated and will be removed",
        "recommended_action": "Use appropriate service endpoints for AI functionality",
        "timestamp": datetime.utcnow().isoformat()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Logs startup information and validates critical components.
    """
    logger.info("VerdoyLab API startup event triggered")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    
    # TODO: Add startup validation
    # - Validate external service connections
    # - Check required directories and files
    # - Initialize caches and queues

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Performs cleanup operations and logs shutdown information.
    """
    logger.info("VerdoyLab API shutdown event triggered")
    
    # TODO: Add shutdown cleanup
    # - Close database connections
    # - Stop background tasks
    # - Flush caches
    # - Close WebSocket connections

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
