"""
Configuration management for VerdoyLab API.

This module provides centralized configuration management using environment variables
and Pydantic settings validation. It supports both development and production environments
with proper validation and default values.
"""

import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, Field

class Settings(BaseSettings):
    """
    Application settings with environment variable support and validation.
    
    All settings can be configured via environment variables with the same name
    (case-insensitive). For example, DATABASE_URL can be set via DATABASE_URL env var.
    """
    
    # Application settings
    app_name: str = "VerdoyLab API"
    version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    
    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="JWT token expiration time in minutes")
    
    # Database settings
    database_url: str = Field(
        default="sqlite:///./lms_core.db", 
        description="Database connection URL (supports PostgreSQL and SQLite)"
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # File upload settings
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    allowed_file_types: List[str] = Field(
        default=[".csv", ".json", ".xlsx", ".pdf"],
        description="Allowed file types for uploads"
    )
    
    # Redis settings (for caching)
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    redis_ttl: Optional[int] = Field(default=3600, description="Default Redis TTL in seconds")
    
    # Email settings
    smtp_server: Optional[str] = Field(default=None, description="SMTP server for email notifications")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    
    # WebSocket settings
    websocket_ping_interval: int = Field(default=20, description="WebSocket ping interval in seconds")
    websocket_ping_timeout: int = Field(default=20, description="WebSocket ping timeout in seconds")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Rate limiting settings
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # Background task settings
    background_task_queue: str = Field(default="default", description="Background task queue name")
    background_task_workers: int = Field(default=4, description="Number of background task workers")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", description="API prefix for all endpoints")
    docs_url: str = Field(default="/docs", description="Swagger UI URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ['development', 'staging', 'production', 'test']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format and log warnings for SQLite usage."""
        if v.startswith(('postgresql://', 'postgres://')):
            # PostgreSQL - validate format
            if not any(char in v for char in ['@', ':', '/']):
                raise ValueError('Invalid PostgreSQL URL format')
            return v
        elif v.startswith('sqlite://'):
            # SQLite - log warning for non-development environments
            env = os.environ.get('ENVIRONMENT', 'development').lower()
            if env in ['staging', 'production']:
                logging.warning(
                    "SQLite database detected in non-development environment. "
                    "This is not recommended for production use. "
                    "Consider using PostgreSQL for better performance and features."
                )
            return v
        else:
            raise ValueError(
                'Database URL must be a PostgreSQL (postgresql://) or SQLite (sqlite://) connection string'
            )
    
    @validator('allowed_origins')
    def validate_allowed_origins(cls, v):
        """Validate allowed origins format."""
        for origin in v:
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid origin format: {origin}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {allowed}')
        return v.upper()
    
    def validate(self) -> bool:
        """
        Validate all settings.
        
        Returns:
            bool: True if all settings are valid
            
        Raises:
            ValueError: If any setting is invalid
        """
        try:
            # Validate required settings
            if not self.secret_key:
                raise ValueError("Secret key is required")
            
            if not self.database_url:
                raise ValueError("Database URL is required")
            
            # Validate environment-specific settings
            if self.environment == "production":
                if self.debug:
                    raise ValueError("Debug mode should be disabled in production")
                
                if not self.secret_key or len(self.secret_key) < 64:
                    raise ValueError("Strong secret key required in production")
                
                # Warn about SQLite in production
                if self.database_url.startswith('sqlite://'):
                    logging.warning(
                        "SQLite database detected in production environment. "
                        "This is not recommended for production deployments."
                    )
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            return False
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith('sqlite://')
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.database_url.startswith(('postgresql://', 'postgres://'))
    
    class Config:
        """Pydantic configuration."""
        env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}" if os.getenv('ENVIRONMENT') == 'test' else ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create global settings instance
settings = Settings()

# Configure logging based on settings
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)

# Log configuration summary (without sensitive data)
logging.info(f"Configuration loaded for environment: {settings.environment}")
logging.info(f"Debug mode: {settings.debug}")
logging.info(f"Database type: {'SQLite' if settings.is_sqlite else 'PostgreSQL'}")
logging.info(f"Database pool size: {settings.database_pool_size}")
logging.info(f"Allowed origins: {len(settings.allowed_origins)} configured")
logging.info(f"Rate limiting: {settings.rate_limit_requests} requests per {settings.rate_limit_window} seconds")

# Log database-specific warnings
if settings.is_sqlite and settings.environment != "development":
    logging.warning(
        "Using SQLite in non-development environment. "
        "Some features may not work correctly. "
        "Consider using PostgreSQL for production deployments."
    ) 