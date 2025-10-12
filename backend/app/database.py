"""
Database configuration and session management for VerdoyLab API.

This module handles database connections, session management, and
initialization for the FastAPI application. Supports both PostgreSQL
and SQLite databases with appropriate configurations for each.
"""

import logging
from sqlalchemy import create_engine, text, Column, TypeDecorator, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
import json
import uuid

from .config import settings


class JSONType(TypeDecorator):
    """
    Custom JSON type that works with both PostgreSQL and SQLite.
    
    In PostgreSQL, this will use JSONB for better performance and operator support.
    In SQLite, this will use TEXT with JSON validation.
    """
    impl = String
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def load_dialect_impl(self, dialect):
        """Use JSONB for PostgreSQL, String for SQLite."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(String())
    
    def process_bind_param(self, value, dialect):
        """Convert Python dict/list to JSON string for storage."""
        if value is None:
            return None
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        """Convert JSON string back to Python dict/list."""
        if value is None:
            return None
        
        # PostgreSQL/TimescaleDB automatically parses JSONB to dict/list
        # SQLite returns JSON as string that needs parsing
        if isinstance(value, (dict, list)):
            # Already parsed (PostgreSQL/TimescaleDB)
            return value
        elif isinstance(value, (str, bytes)):
            # String that needs parsing (SQLite)
            return json.loads(value)
        else:
            # Fallback: return as-is
            return value


class UUIDType(TypeDecorator):
    """
    Custom UUID type that works with both PostgreSQL and SQLite.

    In PostgreSQL, this will use UUID for better performance and native UUID support.
    In SQLite, this will use String with UUID validation.
    """
    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def load_dialect_impl(self, dialect):
        """Use UUID for PostgreSQL, String for SQLite."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        """Convert Python UUID to string for storage."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            # Validate that it's a valid UUID string
            try:
                uuid.UUID(value)
                return value
            except ValueError:
                raise ValueError(f"Invalid UUID string: {value}")
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert string back to Python UUID."""
        if value is None:
            return None
        
        # PostgreSQL/TimescaleDB automatically parses UUID to UUID object
        if isinstance(value, uuid.UUID):
            return value
        elif isinstance(value, (str, bytes)):
            # String that needs parsing (SQLite)
            try:
                return uuid.UUID(str(value))
            except ValueError:
                return None
        else:
            # Fallback: return as-is
            return value


# Configure engine based on database type
if settings.is_sqlite:
    # SQLite configuration - simpler, no connection pooling needed
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,  # SQLite doesn't need connection pooling
        connect_args={"check_same_thread": False},  # Allow multiple threads
        echo=settings.debug
    )
    logging.info("Using SQLite database with static pool configuration")
else:
    # PostgreSQL configuration - full connection pooling
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug
    )
    logging.info(f"Using PostgreSQL database with pool size: {settings.database_pool_size}")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """
    Database dependency for FastAPI.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database with tables.
    
    This function creates all tables defined in the models.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables initialized successfully")


def check_db_connection():
    """
    Check if database connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            if settings.is_sqlite:
                result = connection.execute(text("SELECT 1"))
            else:
                result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False


def get_db_info():
    """
    Get database information.
    
    Returns:
        Dictionary with database information
    """
    try:
        with engine.connect() as connection:
            if settings.is_sqlite:
                # SQLite-specific information
                version_result = connection.execute(text("SELECT sqlite_version();"))
                version = version_result.fetchone()[0]
                
                return {
                    "status": "connected",
                    "type": "SQLite",
                    "version": version,
                    "database": "sqlite",
                    "pool_size": "N/A (StaticPool)",
                    "checked_out": "N/A (StaticPool)"
                }
            else:
                # PostgreSQL-specific information
                version_result = connection.execute(text("SELECT version();"))
                version = version_result.fetchone()[0]
                
                db_name_result = connection.execute(text("SELECT current_database();"))
                db_name = db_name_result.fetchone()[0]
                
                return {
                    "status": "connected",
                    "type": "PostgreSQL",
                    "version": version,
                    "database": db_name,
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout()
                }
    except Exception as e:
        return {
            "status": "error",
            "type": "Unknown",
            "error": str(e)
        }


def run_migrations():
    """
    Run database migrations.
    
    This function should be called to apply any pending migrations.
    For now, it's a placeholder - you should integrate with Alembic
    or your preferred migration tool.
    """
    if settings.is_sqlite:
        logging.warning(
            "Running migrations on SQLite. Some PostgreSQL-specific "
            "features may not be available."
        )
    
    # TODO: Integrate with Alembic for proper migration handling
    logging.info("Migration system not yet implemented. Use init_db() for schema creation.")
    return True 